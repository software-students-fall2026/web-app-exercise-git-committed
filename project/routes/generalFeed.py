import re
from datetime import datetime
from urllib.parse import urlsplit

from bson import ObjectId
from flask import Blueprint, abort, current_app, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from pymongo.errors import DuplicateKeyError, PyMongoError

general_feed_bp = Blueprint("general_feed", __name__)
PAGE_SIZE = 20


def _database():
    from database import users_collection

    return users_collection.database


def _object_id(value):
    if not ObjectId.is_valid(value):
        abort(404)
    return ObjectId(value)


def _return_to_feed():
    target = request.form.get("return_to", "")
    if len(target) > 2000 or "\r" in target or "\n" in target:
        return redirect(url_for("general_feed.general_feed"))
    try:
        parsed = urlsplit(target)
    except ValueError:
        return redirect(url_for("general_feed.general_feed"))
    if not parsed.scheme and not parsed.netloc and parsed.path in {
        "/feed", "/generalFeed.html", "/following", "/following.html"
    }:
        return redirect(target)
    return redirect(url_for("general_feed.general_feed"))


def _song_links(post):
    spotify = str(post.get("spotify_url") or "")
    audio = str(post.get("audio_url") or "")
    try:
        parsed = urlsplit(spotify)
        valid_spotify = (
            parsed.scheme == "https"
            and parsed.netloc == "open.spotify.com"
            and re.fullmatch(r"/track/[A-Za-z0-9]{22}", parsed.path)
        )
    except ValueError:
        valid_spotify = False
    valid_audio = re.fullmatch(
        r"/uploads/audio/[A-Za-z0-9_.-]+\.(mp3|wav|ogg|m4a|flac)", audio
    )
    return spotify if valid_spotify else "", audio if valid_audio else ""


def _feed(following_only=False):
    db = _database()
    viewer_id = _object_id(current_user.get_id()) if current_user.is_authenticated else None
    query_text = request.args.get("q", "").strip()[:150]
    people_query = request.args.get("people", "").strip()[:100]
    default_sort = "newest" if following_only else "top"
    sort = request.args.get("sort", default_sort)
    if sort not in {"top", "newest"}:
        sort = default_sort
    page = max(1, min(request.args.get("page", 1, type=int), 10000))

    following_ids = []
    if viewer_id:
        following_ids = list({
            row["following_id"]
            for row in db.follows.find({"follower_id": viewer_id})
            if isinstance(row.get("following_id"), ObjectId)
        })
    query = {}
    if following_only:
        query["author_id"] = {"$in": following_ids}
    if query_text:
        expression = {"$regex": re.escape(query_text), "$options": "i"}
        query["$or"] = [
            {"song_title": expression}, {"artist": expression}, {"caption": expression}
        ]

    order = {"created_at": -1, "_id": -1}
    if sort == "top":
        order = {"vote_count": -1, **order}
    posts = list(db.posts.aggregate([
        {"$match": query},
        {"$lookup": {
            "from": "votes", "localField": "_id", "foreignField": "post_id", "as": "post_votes"
        }},
        {"$addFields": {"vote_count": {"$size": "$post_votes"}}},
        {"$sort": order},
        {"$skip": (page - 1) * PAGE_SIZE},
        {"$limit": PAGE_SIZE},
    ]))
    authors = {
        user["_id"]: user
        for user in db.users.find(
            {"_id": {"$in": [post.get("author_id") for post in posts]}},
            {"display_name": 1, "username": 1, "profile_picture_url": 1},
        )
    }
    for post in posts:
        author = authors.get(post.get("author_id"), {})
        post["author_name"] = author.get("display_name") or author.get("username") or "Deleted user"
        post["username"] = author.get("username", "")
        post["author_picture_url"] = author.get("profile_picture_url", "")
        post["can_follow"] = bool(author) and post.get("author_id") != viewer_id
        post["is_following"] = post.get("author_id") in following_ids
        post["is_voted"] = viewer_id is not None and any(
            vote.get("user_id") == viewer_id for vote in post.pop("post_votes")
        )
        created_at = post.get("created_at")
        post["date_label"] = created_at.strftime("%b %d, %Y") if isinstance(created_at, datetime) else ""
        post["spotify_url"], post["audio_url"] = _song_links(post)

    people_filter = {"_id": {"$ne": viewer_id}} if viewer_id else {}
    if people_query:
        expression = {"$regex": re.escape(people_query), "$options": "i"}
        people_filter["$or"] = [{"display_name": expression}, {"username": expression}]
    people = list(db.users.find(
        people_filter, {"display_name": 1, "username": 1, "profile_picture_url": 1}
    ).sort("username", 1).limit(10))
    for person in people:
        person["is_following"] = person["_id"] in following_ids
    following_users = list(db.users.find(
        {"_id": {"$in": following_ids}}, {"display_name": 1, "username": 1, "profile_picture_url": 1}
    ).sort("username", 1).limit(100))

    return render_template(
        "following.html" if following_only else "generalFeed.html",
        posts=posts, people=people, following_users=following_users,
        following_count=len(following_ids), following_only=following_only,
        query=query_text, people_query=people_query, sort=sort, page=page,
        has_next=db.posts.count_documents(query) > page * PAGE_SIZE,
    )


@general_feed_bp.get("/feed")
@general_feed_bp.get("/generalFeed.html")
def general_feed():
    return _feed()


@general_feed_bp.get("/following")
@general_feed_bp.get("/following.html")
@login_required
def following():
    return _feed(following_only=True)


@general_feed_bp.post("/feed/posts/<post_id>/vote")
@login_required
def vote(post_id):
    db = _database()
    post_id = _object_id(post_id)
    if db.posts.find_one({"_id": post_id}, {"_id": 1}) is None:
        abort(404)
    action = request.form.get("action")
    if action not in {"vote", "unvote"}:
        abort(400)
    key = {"user_id": _object_id(current_user.get_id()), "post_id": post_id}
    if action == "vote":
        db.votes.create_index([("user_id", 1), ("post_id", 1)], unique=True)
        try:
            db.votes.update_one(key, {"$setOnInsert": key}, upsert=True)
        except DuplicateKeyError:
            pass
    else:
        db.votes.delete_many(key)
    return _return_to_feed()


@general_feed_bp.post("/feed/users/<user_id>/follow")
@login_required
def follow(user_id):
    db = _database()
    target_id = _object_id(user_id)
    viewer_id = _object_id(current_user.get_id())
    if target_id == viewer_id:
        abort(400)
    if db.users.find_one({"_id": target_id}, {"_id": 1}) is None:
        abort(404)
    action = request.form.get("action")
    if action not in {"follow", "unfollow"}:
        abort(400)
    key = {"follower_id": viewer_id, "following_id": target_id}
    if action == "follow":
        db.follows.create_index([("follower_id", 1), ("following_id", 1)], unique=True)
        try:
            db.follows.update_one(key, {"$setOnInsert": key}, upsert=True)
        except DuplicateKeyError:
            pass
    else:
        db.follows.delete_many(key)
    return _return_to_feed()


@general_feed_bp.errorhandler(PyMongoError)
@general_feed_bp.errorhandler(RuntimeError)
def feed_unavailable(error):
    current_app.logger.warning("Feed database is unavailable.")
    return "The feed is temporarily unavailable. Please try again later.", 503
