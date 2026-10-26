import re
import secrets
from datetime import datetime, timezone
from pathlib import Path

from bson import ObjectId
from flask import Blueprint, current_app, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from database import db

create_post_bp = Blueprint("create_post", __name__)

CAPTION_LIMIT = 200
SPOTIFY_TRACK = re.compile(r"https://open\.spotify\.com/track/[A-Za-z0-9]{22}")


def get_communities():
    return list(db.communities.find().sort("name", 1))


def show_form(error=None):
    return render_template(
        "createPost.html",
        communities=get_communities(),
        error=error,
        form=request.form,
    )

def save_audio(audio_file):
    extension = Path(secure_filename(audio_file.filename)).suffix.lower().lstrip(".")
    if extension not in current_app.config["ALLOWED_AUDIO_EXTENSIONS"]:
        return None
    filename = f"{secrets.token_hex(16)}.{extension}"
    audio_file.save(Path(current_app.config["UPLOAD_FOLDER"]) / filename)
    return f"/uploads/audio/{filename}"


@create_post_bp.route("/create-post", methods=["GET", "POST"])
@create_post_bp.route("/createPost.html", methods=["GET", "POST"])
@login_required
def create_post():
    if request.method == "GET":
        return show_form()

    song_title = request.form.get("song_title", "").strip()
    artist = request.form.get("artist", "").strip()
    spotify_url = request.form.get("spotify_url", "").strip()
    caption = request.form.get("caption", "").strip()
    community_arg = request.form.get("community_id", "").strip()
    audio_file = request.files.get("audio_file")

    if not song_title or not artist:
        return show_form("Please enter the song title and artist.")
    if len(caption) > CAPTION_LIMIT:
        return show_form(f"Your note must be {CAPTION_LIMIT} characters or fewer.")
    if spotify_url and not SPOTIFY_TRACK.fullmatch(spotify_url):
        return show_form("Please paste a valid Spotify track link.")

    audio_url = ""
    if audio_file and audio_file.filename:
        audio_url = save_audio(audio_file)
        if audio_url is None:
            return show_form("Audio must be an mp3, wav, ogg, m4a or flac file.")

    if not spotify_url and not audio_url:
        return show_form("Add a Spotify link or upload an audio clip.")

    community_id = None
    if community_arg:
        if not ObjectId.is_valid(community_arg):
            return show_form("That community does not exist.")
        community_id = ObjectId(community_arg)
        if db.communities.find_one({"_id": community_id}) is None:
            return show_form("That community does not exist.")

    db.posts.insert_one({
        "author_id": ObjectId(current_user.id),
        "song_title": song_title,
        "artist": artist,
        "spotify_url": spotify_url,
        "audio_url": audio_url,
        "caption": caption,
        "community_id": community_id,
        "created_at": datetime.now(timezone.utc),
    })

    return redirect(url_for("general_feed.general_feed"))