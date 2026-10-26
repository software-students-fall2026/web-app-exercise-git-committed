
from datetime import datetime, timezone

from flask import Blueprint, abort, redirect, render_template, request, jsonify, url_for
from flask_login import login_required, current_user
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from database import db

saved_bp = Blueprint("saved", __name__)


@saved_bp.route("/saved")
@login_required
def saved_posts():
    user_id = ObjectId(current_user.id)

    saves = list(db.saves.find({"user_id": user_id}))
    post_ids = [save["post_id"] for save in saves]

    posts = list(db.posts.find({"_id": {"$in": post_ids}}))
    folders = list(db.saved_folders.find({"user_id": user_id}))

    return render_template(
        "savedPosts.html",
        saved_posts=posts,
        saved_categories=folders
    )


@saved_bp.post("/posts/<post_id>/save")
@login_required
def save_post(post_id):
    if not ObjectId.is_valid(post_id):
        abort(404)
    post_id = ObjectId(post_id)
    if db.posts.find_one({"_id": post_id}, {"_id": 1}) is None:
        abort(404)

    key = {"user_id": ObjectId(current_user.id), "post_id": post_id}
    action = request.form.get("action")
    if action == "save":
        db.saves.create_index([("user_id", 1), ("post_id", 1)], unique=True)
        try:
            db.saves.update_one(key, {"$setOnInsert": {
                **key, "saved_at": datetime.now(timezone.utc)
            }}, upsert=True)
        except DuplicateKeyError:
            pass
    elif action == "unsave":
        db.saves.delete_many(key)
        db.saved_folders.update_many(
            {"user_id": key["user_id"]}, {"$pull": {"post_ids": post_id}}
        )
    else:
        abort(400)

    target = request.form.get("return_to")
    if target not in {
        "/profile", "/saved", "/saved.html", "/SavedPost.html", "/SavedPosts.html",
        "/savedPosts.html", "/explore", "/exploreFeed.html"
    }:
        target = url_for("saved.saved_posts")
    return redirect(target)


@saved_bp.route("/saved/categories", methods=["POST"])
@login_required
def add_saved_category():
    data = request.get_json()
    name = data["name"].strip()

    if not name:
        return jsonify({"error": "Category name is required"}), 400

    user_id = ObjectId(current_user.id)
    db.saved_folders.insert_one({
        "user_id": user_id,
        "name": name,
        "post_ids": []
    })

    return jsonify({"message": "Category created"}), 201
