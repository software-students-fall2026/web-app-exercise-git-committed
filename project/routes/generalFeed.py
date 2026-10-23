from flask import Blueprint, render_template

general_feed_bp = Blueprint("general_feed", __name__)


@general_feed_bp.get("/feed")
@general_feed_bp.get("/generalFeed.html")
def general_feed():
    return render_template("generalFeed.html")


@general_feed_bp.get("/following")
@general_feed_bp.get("/following.html")
def following():
    return render_template("following.html")
