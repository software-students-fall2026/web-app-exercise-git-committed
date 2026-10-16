"""Behavior checks with a MongoDB test double; no shared accounts or DB writes."""

import re
from datetime import datetime, timedelta, timezone

import mongomock
import pytest
from bson import ObjectId

from preview import create_app
from sample_data import POST_IDS, seed_sample_data
from sonder_feed.repository import FeedRepository
from sonder_feed.routes import spotify_embed_url


@pytest.fixture
def database():
    database = mongomock.MongoClient(tz_aware=True)["test_sonder"]
    seed_sample_data(database)
    return database


@pytest.fixture
def app(database):
    return create_app(database, config={"TESTING": True, "SECRET_KEY": "test-only-secret"})


@pytest.fixture
def client(app):
    client = app.test_client()
    with client.session_transaction() as session:
        session["_user_id"] = "demo-alex"
        session["_fresh"] = True
    return client


def action(client, path, state="on", **extra):
    response = client.get("/feed")
    token = re.search(r'name="csrf_token" value="([^"]+)"', response.text).group(1)
    return client.post(path, data={"state": state, "csrf_token": token, **extra})


def test_following_shows_only_followed_users_in_date_order(client):
    response = client.get("/following")
    assert response.status_code == 200
    identifiers = re.findall(r'data-post-id="([^"]+)"', response.text)
    assert identifiers == [str(POST_IDS[0]), str(POST_IDS[1]), str(POST_IDS[2])]
    assert str(POST_IDS[3]) not in identifiers
    assert "Mina Chen" in response.text
    assert "Theo James" in response.text


def test_follow_and_unfollow_change_the_next_feed_request(client, database):
    assert action(client, "/people/demo-noor/follow").status_code == 303
    response = client.get("/following")
    assert str(POST_IDS[3]) in re.findall(r'data-post-id="([^"]+)"', response.text)
    # A fresh repository instance sees the saved relationship, not a UI-only change.
    assert "demo-noor" in FeedRepository(database).followed_ids("demo-alex")
    assert action(client, "/people/demo-noor/follow", "off").status_code == 303
    assert str(POST_IDS[3]) not in re.findall(r'data-post-id="([^"]+)"', client.get("/following").text)
    assert str(POST_IDS[3]) in re.findall(r'data-post-id="([^"]+)"', client.get("/feed").text)


def test_repeated_follow_does_not_duplicate_relationship(client, database):
    for _ in range(2):
        assert action(client, "/people/demo-noor/follow").status_code == 303
    assert database.follows.count_documents({"follower_id": "demo-alex", "followed_id": "demo-noor"}) == 1


def test_upvote_is_saved_once_and_removing_it_keeps_others_votes(client, database):
    post_id = str(POST_IDS[0])
    path = f"/posts/{post_id}/vote"
    for _ in range(2):
        assert action(client, path).status_code == 303
    assert database.votes.count_documents({"post_id": post_id}) == 3
    assert database.votes.count_documents({"user_id": "demo-alex", "post_id": post_id}) == 1
    post = FeedRepository(database).feed("demo-alex")[0][0]
    assert post["voted"] is True
    assert post["vote_count"] == 3
    assert action(client, path, "off").status_code == 303
    post = FeedRepository(database).feed("demo-alex")[0][0]
    assert post["voted"] is False
    assert post["vote_count"] == 2
    assert database.votes.count_documents({"post_id": post_id}) == 2


def test_posted_actor_id_cannot_vote_as_someone_else(client, database):
    post_id = str(POST_IDS[2])
    assert action(client, f"/posts/{post_id}/vote", user_id="demo-theo").status_code == 303
    assert database.votes.find_one({"post_id": post_id, "user_id": "demo-alex"})
    assert database.votes.find_one({"post_id": post_id, "user_id": "demo-theo"}) is None


def test_following_page_lists_current_people_and_searches_for_others(client):
    response = client.get("/following")
    assert response.status_code == 200
    assert 'aria-label="Unfollow Mina Chen"' in response.text
    assert 'aria-label="Follow Noor Ali"' in response.text
    assert 'data-person-id="demo-alex"' not in response.text
    response = client.get("/following?people_q=noor")
    assert "Results for “noor”" in response.text
    assert 'aria-label="Follow Noor Ali"' in response.text


def test_people_search_treats_regex_input_literally(app):
    assert app.extensions["sonder_feed"].find_people("demo-alex", ".*") == []


def test_unfollowing_everyone_shows_the_empty_feed(client, database):
    database.follows.delete_many({"follower_id": "demo-alex"})
    response = client.get("/following")
    assert response.status_code == 200
    assert 'href="#find-people"' in response.text
    assert 'data-post-id="' not in response.text


def test_pagination_has_no_repeated_posts(client, database):
    now = datetime.now(timezone.utc)
    database.posts.insert_many([
        {"user_id": "demo-mina", "title": f"Extra post {index}", "artist": "Artist", "spotify_url": "", "caption": "", "created_at": now + timedelta(minutes=index)}
        for index in range(15)
    ])
    first = client.get("/feed")
    second = client.get("/feed?page=2")
    first_ids = re.findall(r'data-post-id="([^"]+)"', first.text)
    second_ids = re.findall(r'data-post-id="([^"]+)"', second.text)
    assert len(first_ids) == 12
    assert len(second_ids) == 7
    assert not set(first_ids) & set(second_ids)
    assert "Older posts" in first.text
    assert "Newer posts" in second.text


@pytest.mark.parametrize("page", ["0", "-1", "oops", "10001"])
def test_invalid_page_is_rejected(client, page):
    assert client.get(f"/feed?page={page}").status_code == 400


@pytest.mark.parametrize("path", ["/feed", "/following"])
def test_anonymous_users_cannot_read_private_screens(app, path):
    assert app.test_client().get(path).status_code == 401


@pytest.mark.parametrize("path", [f"/posts/{POST_IDS[0]}/vote", "/people/demo-noor/follow"])
def test_anonymous_mutations_are_rejected(app, path):
    assert app.test_client().post(path, data={"state": "on"}).status_code == 401


def test_csrf_is_required_and_invalid_state_does_not_mutate(client, database):
    path = "/people/demo-noor/follow"
    assert client.post(path, data={"state": "on"}).status_code == 400
    assert action(client, path, "anything").status_code == 400
    assert database.follows.count_documents({"follower_id": "demo-alex", "followed_id": "demo-noor"}) == 0


def test_missing_targets_and_self_follow_are_rejected(client, database):
    assert action(client, "/people/demo-alex/follow").status_code == 400
    assert action(client, "/people/no-such-person/follow").status_code == 404
    assert action(client, "/posts/no-such-post/vote").status_code == 404
    assert database.follows.count_documents({"follower_id": "demo-alex"}) == 2


def test_mutations_require_post(client):
    assert client.get("/people/demo-noor/follow").status_code == 405
    assert client.get(f"/posts/{POST_IDS[0]}/vote").status_code == 405


@pytest.mark.parametrize("destination", ["https://example.com/", "//example.com/", "https://[broken"])
def test_return_destination_cannot_redirect_to_another_site(client, destination):
    response = action(client, "/people/demo-noor/follow", return_to=destination)
    assert response.status_code == 303
    assert response.headers["Location"] == "/following"


def test_user_text_is_escaped_and_invalid_music_link_does_not_break_feed(client, database):
    database.posts.update_one({"_id": POST_IDS[0]}, {"$set": {"caption": "<script>alert(1)</script>", "spotify_url": "https://[broken"}})
    response = client.get("/feed")
    assert response.status_code == 200
    assert "<script>alert(1)</script>" not in response.text
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in response.text
    assert "A Spotify player isn’t available" in response.text


@pytest.mark.parametrize("value", ["javascript:alert(1)", "https://open.spotify.com.evil.example/track/3xKsf9qdS1CyvXSMEid6g8", "https://[broken", None])
def test_only_valid_spotify_links_become_embeds(value):
    assert spotify_embed_url(value) is None


def test_localized_spotify_share_link_uses_canonical_player():
    assert spotify_embed_url("https://open.spotify.com/intl-fr/track/3xKsf9qdS1CyvXSMEid6g8?si=example") == "https://open.spotify.com/embed/track/3xKsf9qdS1CyvXSMEid6g8?theme=0"


def test_mongo_object_ids_work_for_users_and_posts(client, database):
    identifier = ObjectId()
    database.users.insert_one({"_id": identifier, "username": "newlistener", "display_name": "New Listener"})
    database.posts.insert_one({"user_id": str(identifier), "title": "Object ID song", "artist": "Artist", "spotify_url": "", "caption": "", "created_at": datetime.now(timezone.utc)})
    assert action(client, f"/people/{identifier}/follow").status_code == 303
    assert "Object ID song" in client.get("/feed").text


def test_demo_cannot_automatically_sign_in_to_a_supplied_database(database):
    with pytest.raises(ValueError, match="external database"):
        create_app(database, demo=True)


def test_demo_is_explicit_and_uses_only_temporary_data(monkeypatch):
    monkeypatch.setenv("MONGO_URI", "mongodb://not-a-real-shared-server:27017/")
    app = create_app(demo=True)
    assert isinstance(app.extensions["sonder_feed"].db.client, mongomock.MongoClient)
    assert "Sample data · local preview" in app.test_client().get("/feed").text


def test_general_feed_includes_unfollowed_listeners_and_survives_empty_follows(client, database):
    database.follows.delete_many({"follower_id": "demo-alex"})
    response = client.get("/feed?sort=newest")
    identifiers = re.findall(r'data-post-id="([^"]+)"', response.text)
    assert identifiers == [str(POST_IDS[i]) for i in (3, 0, 1, 2)]
    assert 'data-post-id="' not in client.get("/following").text


def test_top_sort_uses_saved_votes_before_pagination(database):
    repository = FeedRepository(database)
    for index in range(4):
        repository.set_vote(f"sample-voter-{index}", POST_IDS[3], True)
    first, has_next = repository.general_feed("demo-alex", page_size=1)
    second, _ = repository.general_feed("demo-alex", page=2, page_size=1)
    assert first[0]["id"] == str(POST_IDS[3])
    assert first[0]["vote_count"] == 4
    assert has_next is True
    assert second[0]["id"] == str(POST_IDS[0])


def test_song_search_filters_both_feeds_without_escaping_follow_scope(client):
    response = client.get("/feed?q=dreams&sort=newest")
    assert re.findall(r'data-post-id="([^"]+)"', response.text) == [str(POST_IDS[3]), str(POST_IDS[1])]
    response = client.get("/following?q=dreams")
    assert re.findall(r'data-post-id="([^"]+)"', response.text) == [str(POST_IDS[1])]
    assert 'data-post-id="' not in client.get("/feed?q=.*").text


def test_invalid_sort_is_rejected(client):
    assert client.get("/feed?sort=unknown").status_code == 400


def test_following_count_updates_and_vote_preserves_screen_and_filter(client):
    action(client, "/people/demo-theo/follow", "off")
    assert "1 listener you follow" in client.get("/following").text
    response = action(client, f"/posts/{POST_IDS[0]}/vote", return_to=f"/following?q=pink#post-{POST_IDS[0]}")
    assert response.headers["Location"] == f"/following?q=pink#post-{POST_IDS[0]}"
