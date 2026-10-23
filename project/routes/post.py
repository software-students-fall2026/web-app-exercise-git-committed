from flask import Blueprint, render_template

post_bp = Blueprint("post", __name__)


@post_bp.get("/create-post")
@post_bp.get("/createPost.html")
def create_post():
    return render_template("createPost.html")
