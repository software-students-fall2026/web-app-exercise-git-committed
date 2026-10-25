from flask import Blueprint, render_template
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
        posts=posts,
        folders=folders
    )