from flask import Blueprint, render_template
from flask_login import login_required, current_user
from bson import ObjectId
from database import db

profile_bp = Blueprint("profile", __name__)

@profile_bp.route("/profile")
@login_required
def profile():
    user_id = ObjectId(current_user.id)

    user = db.users.find_one({"_id": user_id})
    posts = list(db.posts.find({"author_id": user_id}))

    followers = db.follows.count_documents({"following_id": user_id})
    following = db.follows.count_documents({"follower_id": user_id})

    return render_template(
        "profilePage.html",
        user=user,
        posts=posts,
        followers=followers,
        following=following
    )
