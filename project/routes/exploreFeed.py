from flask import Blueprint, render_template

explore_feed_bp = Blueprint("explore_feed", __name__)


@explore_feed_bp.get("/explore")
@explore_feed_bp.get("/exploreFeed.html")
def explore():
    return render_template("exploreFeed.html")
