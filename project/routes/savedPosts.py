
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from bson import ObjectId
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
