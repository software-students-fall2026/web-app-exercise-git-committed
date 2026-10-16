"""Check that the completed page drafts form one navigable local demo."""

from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

import mongomock

from preview import create_app
from sample_data import seed_sample_data


class PageLinks(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.links = []
        self.assets = []
        self.ids = set()
        self.feed(html)

    def handle_starttag(self, tag, attributes):
        attributes = dict(attributes)
        if "id" in attributes:
            self.ids.add(attributes["id"])
        if tag == "a" and attributes.get("href"):
            self.links.append(attributes["href"])
        if tag == "link" and attributes.get("rel") == "stylesheet":
            self.assets.append(attributes["href"])
        if tag in {"img", "source", "script"} and attributes.get("src"):
            self.assets.append(attributes["src"])


def test_demo_navigation_connects_all_completed_pages_and_assets():
    client = create_app(demo=True, config={"TESTING": True}).test_client()
    pending = ["/"]
    visited = set()
    while pending:
        path = pending.pop()
        if path in visited:
            continue
        visited.add(path)
        response = client.get(path, follow_redirects=True)
        assert response.status_code == 200, path
        actual_path = response.request.path
        page = PageLinks(response.text)
        for asset in page.assets:
            destination = urlsplit(urljoin(actual_path, asset))
            if not destination.netloc:
                assert client.get(destination.path).status_code == 200, asset
        for link in page.links:
            assert link != "#", f"Unconnected placeholder on {actual_path}"
            destination = urlsplit(urljoin(actual_path, link))
            if destination.netloc or destination.scheme:
                continue
            if destination.fragment:
                target = client.get(destination.path, follow_redirects=True)
                assert destination.fragment in PageLinks(target.text).ids, link
            pending.append(destination.path)

    assert {
        "/login.html", "/register.html", "/feed", "/following",
        "/profilePage.html", "/saved.html", "/appScreen.html",
    } <= visited
    assert "@alexonrepeat" in client.get("/profilePage.html").text


def test_demo_account_screens_do_not_submit_credentials_or_create_users():
    app = create_app(demo=True, config={"TESTING": True})
    client = app.test_client()
    database = app.extensions["sonder_feed"].db
    initial_users = database.users.count_documents({})
    for path in ("/login.html", "/register.html"):
        response = client.get(path)
        assert "<fieldset disabled>" in response.text
        assert "Continue with sample account" in response.text
        assert 'type="submit"' not in response.text
        assert client.post(path, data={"username": "new-user", "password": "unused"}).status_code == 405
    assert database.users.count_documents({}) == initial_users


def test_draft_routes_are_demo_only_and_do_not_serve_arbitrary_files():
    database = mongomock.MongoClient(tz_aware=True)["test_sonder"]
    seed_sample_data(database)
    real_client = create_app(database, config={"TESTING": True, "SECRET_KEY": "test-only-secret"}).test_client()
    demo_client = create_app(demo=True, config={"TESTING": True}).test_client()
    assert real_client.get("/login.html").status_code == 404
    assert real_client.get("/profilePage.html").status_code == 404
    for path in ("/instructions.css", "/_demo_nav.html", "/createPost.html", "/exploreFeed.html", "/community.html"):
        assert demo_client.get(path).status_code == 404, path
    assert demo_client.get("/generalFeed.html").headers["Location"] == "/feed"
    assert demo_client.get("/following.html").headers["Location"] == "/following"
