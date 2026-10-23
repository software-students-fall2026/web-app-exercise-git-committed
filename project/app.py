import os
import secrets
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, abort, jsonify, send_from_directory

from routes.account import account_bp, login_manager
from routes.communities import communities_bp
from routes.exploreFeed import explore_feed_bp
from routes.generalFeed import general_feed_bp
from routes.login import login_bp
from routes.post import post_bp
from routes.profile import profile_bp
from routes.register import register_bp
from routes.settings import settings_bp

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

login_manager.init_app(app)
login_manager.login_view = "login.login"

app.register_blueprint(account_bp)
app.register_blueprint(login_bp)
app.register_blueprint(register_bp)
app.register_blueprint(general_feed_bp)
app.register_blueprint(explore_feed_bp)
app.register_blueprint(post_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(communities_bp)
app.register_blueprint(settings_bp)


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
