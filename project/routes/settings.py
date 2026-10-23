from flask import Blueprint, render_template

settings_bp = Blueprint("settings", __name__)


@settings_bp.get("/settings")
@settings_bp.get("/settings.html")
def settings():
    return render_template("settings.html")
