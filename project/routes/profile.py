from flask import Blueprint, render_template

profile_bp = Blueprint("profile", __name__)


@profile_bp.get("/profile")
@profile_bp.get("/profilePage.html")
def profile():
    return render_template("profilePage.html")


@profile_bp.get("/saved")
@profile_bp.get("/saved.html")
def saved():
    return render_template("saved.html")
