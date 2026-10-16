"""Host the team's HTML drafts alongside the feeds in the sample-data preview.

These routes are registered only by preview.py --demo. Account creation and
Sofia's profile/saved actions still belong to their respective feature owners.
"""

from pathlib import Path

from flask import Blueprint, abort, current_app, redirect, render_template, send_from_directory, url_for
from flask_login import current_user


blueprint = Blueprint("team_demo", __name__, template_folder="project")
PROJECT_DIRECTORY = Path(__file__).with_name("project")
STYLES = {"appScreen", "login", "register", "profilePage", "saved", "demo"}


@blueprint.get("/appScreen.html")
def welcome():
    return render_template("appScreen.html")


@blueprint.get("/login.html")
def login():
    return render_template("login.html")


@blueprint.get("/register.html")
def register():
    return render_template("register.html")


@blueprint.get("/profilePage.html")
def profile():
    user = current_app.extensions["sonder_feed"].find_user(current_user.get_id())
    return render_template("profilePage.html", demo_user=user)


@blueprint.get("/saved.html")
def saved():
    return render_template("saved.html")


@blueprint.get("/generalFeed.html")
def legacy_feed():
    return redirect(url_for("sonder_feed.feed"))


@blueprint.get("/following.html")
def legacy_following():
    return redirect(url_for("sonder_feed.following"))


@blueprint.get("/<name>.css")
def stylesheet(name):
    if name not in STYLES:
        abort(404)
    return send_from_directory(PROJECT_DIRECTORY, name + ".css")
