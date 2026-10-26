import hmac
import os
import secrets
from pathlib import Path

from bson import ObjectId
from bson.errors import InvalidId
from dotenv import load_dotenv
from flask import Flask, abort, jsonify, render_template, request, send_from_directory, session
from flask_login import LoginManager, UserMixin, current_user
from jinja2 import ChoiceLoader, DictLoader

from routes.generalFeed import general_feed_bp
from routes.settings import settings_bp
from routes.register import register_bp
from routes.savedPosts import saved_bp, saved_posts
from routes.login import login_bp
from routes.community import community_bp
from routes.CreatePost import create_post_bp

load_dotenv()

app = Flask(__name__, template_folder=".")
app.register_blueprint(register_bp)
app.register_blueprint(saved_bp)
app.register_blueprint(login_bp)
app.register_blueprint(community_bp)
app.register_blueprint(create_post_bp)
project_folder = Path(app.root_path)
app.jinja_loader = ChoiceLoader([
    app.jinja_loader,
    DictLoader({"savedPosts.html": '{% extends "SavedPosts.html" %}'}),
])

app.config.update(
    SECRET_KEY=os.getenv("SECRET_KEY") or secrets.token_hex(32),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    UPLOAD_FOLDER=str(Path(app.instance_path) / "uploads" / "audio"),
    MAX_CONTENT_LENGTH=25 * 1024 * 1024,
    ALLOWED_AUDIO_EXTENSIONS={"mp3", "wav", "ogg", "m4a", "flac"},
)
Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

login_manager = LoginManager(app)
login_manager.login_view = "login"
app.register_blueprint(general_feed_bp)
app.register_blueprint(settings_bp)


@app.context_processor
def form_tokens():
    def csrf_token():
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_urlsafe(32)
        return session["csrf_token"]
    return {"csrf_token": csrf_token}


@app.before_request
def check_form_token():
    if (
        request.blueprint in {"general_feed", "settings"}
        and request.method == "POST"
        and current_user.is_authenticated
    ):
        expected = session.get("csrf_token")
        supplied = request.form.get("csrf_token", "")
        if not isinstance(expected, str) or not hmac.compare_digest(expected.encode(), supplied.encode()):
            abort(400, description="The form expired. Reload the page and try again.")


class User(UserMixin):
    def __init__(self, document):
        self.id = str(document["_id"])
        self.username = document.get("username", "")
        self.display_name = document.get("display_name", self.username)
        self.email = document.get("email", "")
        self.profile_picture_url = document.get("profile_picture_url", "")


@login_manager.user_loader
def load_user(user_id):
    if not isinstance(user_id, str):
        return None
    try:
        object_id = ObjectId(user_id)
    except (InvalidId, TypeError):
        return None

    from database import users_collection

    document = users_collection.find_one({"_id": object_id})
    return User(document) if document is not None else None


@app.get("/")
@app.get("/appScreen.html")
@app.get("/LandingPage.html")
def welcome():
    return render_template("LandingPage.html")


@app.get("/login")
@app.get("/login.html")
def login():
    return render_template("login.html")


@app.get("/register")
@app.get("/register.html")
def register():
    return render_template("register.html")


@app.get("/explore")
@app.get("/exploreFeed.html")
def explore():
    return render_template("exploreFeed.html")

@app.get("/profile")
@app.get("/profilePage.html")
def profile():
    return render_template("profilePage.html")


@app.get("/saved.html")
@app.get("/SavedPost.html")
@app.get("/SavedPosts.html")
@app.get("/savedPosts.html")
def saved():
    return saved_posts()


@app.get("/communities")
@app.get("/community.html")
def communities():
    return render_template("community.html")


@app.get("/<filename>.css")
def stylesheet(filename):
    filename = {
        "ExploreFeed": "exploreFeed", "appScreen": "LandingPage", "saved": "savedPosts"
    }.get(filename, filename)
    return send_from_directory(project_folder, f"{filename}.css")


@app.get("/images/<path:filename>")
def image(filename):
    if Path(filename).suffix.lower() not in {
        ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico"
    }:
        abort(404)
    return send_from_directory(project_folder.parent / "images", filename)


@app.get("/uploads/audio/<filename>")
def uploaded_audio(filename):
    extension = Path(filename).suffix.lower().lstrip(".")
    if extension not in app.config["ALLOWED_AUDIO_EXTENSIONS"]:
        abort(404)
    response = send_from_directory(app.config["UPLOAD_FOLDER"], filename)
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "message": "Flask backend is running"
    }), 200


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
