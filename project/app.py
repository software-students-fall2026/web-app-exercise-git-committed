import os
import secrets
from pathlib import Path

from bson import ObjectId
from bson.errors import InvalidId
from dotenv import load_dotenv
from flask import Flask, abort, jsonify, render_template, send_from_directory
from flask_login import LoginManager, UserMixin

load_dotenv()

app = Flask(__name__, template_folder=".")
project_folder = Path(app.root_path)

app.config.update(
    # A configured key keeps sessions valid between local server restarts.
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


class User(UserMixin):
    def __init__(self, document):
        self.id = str(document["_id"])
        self.username = document.get("username", "")
        self.display_name = document.get("display_name", self.username)
        self.email = document.get("email", "")


@login_manager.user_loader
def load_user(user_id):
    if not isinstance(user_id, str):
        return None
    try:
        object_id = ObjectId(user_id)
    except (InvalidId, TypeError):
        return None

    # Connect when loading a signed-in user, so sample pages can open without MongoDB.
    from database import users_collection

    document = users_collection.find_one({"_id": object_id})
    return User(document) if document is not None else None


@app.get("/")
@app.get("/appScreen.html")
def welcome():
    return render_template("appScreen.html")


@app.get("/login")
@app.get("/login.html")
def login():
    return render_template("login.html")


@app.get("/register")
@app.get("/register.html")
def register():
    return render_template("register.html")


@app.get("/feed")
@app.get("/generalFeed.html")
def general_feed():
    return render_template("generalFeed.html")


@app.get("/following")
@app.get("/following.html")
def following():
    return render_template("following.html")


@app.get("/explore")
@app.get("/exploreFeed.html")
def explore():
    return render_template("exploreFeed.html")


@app.get("/create-post")
@app.get("/createPost.html")
def create_post():
    return render_template("createPost.html")


@app.get("/profile")
@app.get("/profilePage.html")
def profile():
    return render_template("profilePage.html")


@app.get("/saved")
@app.get("/saved.html")
def saved():
    return render_template("saved.html")


@app.get("/communities")
@app.get("/community.html")
def communities():
    return render_template("community.html")


@app.get("/settings")
@app.get("/settings.html")
def settings():
    return render_template("settings.html")


@app.get("/<filename>.css")
def stylesheet(filename):
    # Keep the existing pages' relative stylesheet links working.
    if filename == "ExploreFeed":
        filename = "exploreFeed"
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
