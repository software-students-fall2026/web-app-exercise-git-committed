import re
from datetime import datetime, timedelta, timezone

from bson import ObjectId
from bson.errors import InvalidId
from flask import Blueprint, render_template, request
from flask_login import current_user

from database import (
    communities_collection,
    follows_collection,
    posts_collection,
    saves_collection,
)

explore_bp = Blueprint("explore", __name__)

DAYS_BACK = 7
POST_LIMIT = 50


def to_object_id(value):
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        return None


@explore_bp.route("/explore")
@explore_bp.route("/exploreFeed.html")
def explore():
    user_id = to_object_id(current_user.id) if current_user.is_authenticated else None
    query_text = request.args.get("q", "").strip()
    community_arg = request.args.get("community", "").strip()
    community_id = to_object_id(community_arg) if community_arg else None

    match = {"created_at": {"$gte": datetime.now(timezone.utc) - timedelta(days=DAYS_BACK)}}

   
    if user_id:
        followed = follows_collection.distinct("following_id", {"follower_id": user_id})
        match["author_id"] = {"$nin": followed + [user_id]}
    if community_id:
        match["community_id"] = community_id

    pipeline = [
        {"$match": match},
        {"$sort": {"created_at": -1}},
        {"$lookup": {"from": "users", "localField": "author_id", "foreignField": "_id", "as": "author"}},
        {"$unwind": "$author"},
        {"$lookup": {"from": "communities", "localField": "community_id", "foreignField": "_id", "as": "community"}},
        {"$unwind": {"path": "$community", "preserveNullAndEmptyArrays": True}},
    ]

    if query_text:
        pattern = {"$regex": re.escape(query_text), "$options": "i"}
        pipeline.append({"$match": {"$or": [
            {"song_title": pattern},
            {"artist": pattern},
            {"author.display_name": pattern},
            {"author.username": pattern},
            {"community.name": pattern},
        ]}})

    pipeline += [
        {"$limit": POST_LIMIT},
        {"$lookup": {"from": "votes", "localField": "_id", "foreignField": "post_id", "as": "votes"}},
        {"$addFields": {
            "upvote_count": {"$size": "$votes"},
            "upvoted": {"$in": [user_id, "$votes.user_id"]},
        }},
        {"$project": {"votes": 0, "author.password_hash": 0, "author.email": 0}},
    ]

    posts = list(posts_collection.aggregate(pipeline))

    saved_ids = set()
    if user_id:
        saved_ids = set(saves_collection.distinct("post_id", {"user_id": user_id}))
    for post in posts:
        post["saved"] = post["_id"] in saved_ids

    communities = list(communities_collection.find().sort("name", 1))

    return render_template(
        "exploreFeed.html",
        posts=posts,
        communities=communities,
        query=query_text,
        selected_community=str(community_id) if community_id else "",
    )