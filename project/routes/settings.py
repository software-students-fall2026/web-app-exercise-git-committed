import re
from pathlib import Path
from uuid import uuid4

from bson import ObjectId
from flask import (
    Blueprint, abort, current_app, flash, redirect, render_template,
    request, send_from_directory, session, url_for,
)
from flask_login import current_user, fresh_login_required, login_required, logout_user
from pymongo.collation import Collation
from pymongo.errors import DuplicateKeyError, PyMongoError

settings_bp = Blueprint("settings", __name__)
PICTURE_LIMIT = 2 * 1024 * 1024
PICTURE_NAME = re.compile(r"[a-f0-9]{32}\.(jpg|png|webp)")


@settings_bp.app_template_filter("profile_picture_url")
def profile_picture_url(value):
    prefix = "/profile-pictures/"
    if isinstance(value, str) and value.startswith(prefix):
        if PICTURE_NAME.fullmatch(value[len(prefix):]):
            return value
    return ""


def _users():
    from database import users_collection

    return users_collection


def _profile():
    profile = _users().find_one(
        {"_id": ObjectId(current_user.get_id())},
        {"display_name": 1, "username": 1, "school": 1, "profile_picture_url": 1},
    )
    if profile is None:
        abort(404)
    return profile


def _settings_page(error=None, status=200):
    return render_template("settings.html", profile=_profile(), error=error), status


def _picture_folder():
    return Path(current_app.instance_path) / "uploads" / "profile"


def _remove_picture(picture_url):
    prefix = "/profile-pictures/"
    if not isinstance(picture_url, str) or not picture_url.startswith(prefix):
        return
    filename = picture_url[len(prefix):]
    if PICTURE_NAME.fullmatch(filename):
        try:
            (_picture_folder() / filename).unlink(missing_ok=True)
        except OSError:
            current_app.logger.warning("An unused profile picture could not be removed.")


@settings_bp.get("/settings")
@settings_bp.get("/settings.html")
@login_required
def settings():
    return _settings_page()


@settings_bp.post("/settings/profile")
@login_required
def update_profile():
    field = request.form.get("field")
    if field not in {"display_name", "username", "school"}:
        abort(400)
    value = request.form.get("value", "").strip()
    limit = 30 if field == "username" else 100
    if len(value) > limit or (field != "school" and not value):
        return _settings_page("Please enter a valid value.", 400)
    users = _users()
    user_id = ObjectId(current_user.get_id())
    if field == "username":
        if not re.fullmatch(r"[A-Za-z0-9_.-]{3,30}", value):
            return _settings_page("Use 3–30 letters, numbers, dots, underscores, or hyphens.", 400)
        value = value.lower()
        if users.find_one({
            "_id": {"$ne": user_id},
            "username": {"$regex": "^" + re.escape(value) + "$", "$options": "i"},
        }):
            return _settings_page("That username is already taken.", 409)
        users.create_index(
            "username", name="username_unique", unique=True,
            partialFilterExpression={"username": {"$type": "string"}},
            collation=Collation(locale="en", strength=2),
        )
    try:
        users.update_one({"_id": user_id}, {"$set": {field: value}})
    except DuplicateKeyError:
        return _settings_page("That username is already taken.", 409)
    flash("Profile updated.")
    return redirect(url_for("settings.settings"))


@settings_bp.post("/settings/picture")
@login_required
def update_picture():
    profile = _profile()
    if request.form.get("action") == "remove":
        _users().update_one({"_id": profile["_id"]}, {"$unset": {"profile_picture_url": ""}})
        _remove_picture(profile.get("profile_picture_url"))
        flash("Picture removed.")
        return redirect(url_for("settings.settings"))
    if request.form.get("action") != "upload":
        abort(400)
    upload = request.files.get("profile_picture")
    if upload is None or not upload.filename:
        return _settings_page("Choose a picture first.", 400)
    extension = Path(upload.filename).suffix.lower()
    data = upload.read(PICTURE_LIMIT + 1)
    if len(data) > PICTURE_LIMIT:
        return _settings_page("Choose a picture smaller than 2 MB.", 413)
    valid = (
        (extension == ".png" and data.startswith(b"\x89PNG\r\n\x1a\n"))
        or (extension in {".jpg", ".jpeg"} and data.startswith(b"\xff\xd8\xff"))
        or (extension == ".webp" and data[:4] == b"RIFF" and data[8:12] == b"WEBP")
    )
    if not valid:
        return _settings_page("Choose a JPG, PNG, or WebP picture.", 400)
    extension = ".jpg" if extension == ".jpeg" else extension
    filename = uuid4().hex + extension
    folder = _picture_folder()
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / filename
    try:
        target.write_bytes(data)
        _users().update_one(
            {"_id": profile["_id"]}, {"$set": {"profile_picture_url": "/profile-pictures/" + filename}}
        )
    except (OSError, PyMongoError):
        target.unlink(missing_ok=True)
        raise
    _remove_picture(profile.get("profile_picture_url"))
    flash("Picture updated.")
    return redirect(url_for("settings.settings"))


@settings_bp.get("/profile-pictures/<filename>")
def profile_picture(filename):
    if not PICTURE_NAME.fullmatch(filename):
        abort(404)
    response = send_from_directory(_picture_folder(), filename)
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@settings_bp.post("/settings/delete-account")
@fresh_login_required
def delete_account():
    profile = _profile()
    if request.form.get("confirm_username", "") != profile.get("username"):
        return _settings_page("Type your username to confirm account deletion.", 400)
    user_id = profile["_id"]
    db = _users().database
    db.posts.update_many({"author_id": user_id}, {"$set": {"author_id": None}})
    db.votes.delete_many({"user_id": user_id})
    db.follows.delete_many({"$or": [{"follower_id": user_id}, {"following_id": user_id}]})
    db.saves.delete_many({"user_id": user_id})
    db.saved_folders.delete_many({"user_id": user_id})
    db.community_memberships.delete_many({"user_id": user_id})
    db.communities.update_many({"created_by": user_id}, {"$set": {"created_by": None}})
    db.users.delete_one({"_id": user_id})
    _remove_picture(profile.get("profile_picture_url"))
    logout_user()
    session.clear()
    flash("Your account has been deleted.")
    return redirect(url_for("welcome"))


@settings_bp.errorhandler(PyMongoError)
@settings_bp.errorhandler(RuntimeError)
@settings_bp.errorhandler(OSError)
def settings_unavailable(error):
    current_app.logger.warning("Settings storage is unavailable.")
    return "Settings are temporarily unavailable. Please try again later.", 503
