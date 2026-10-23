from flask import Blueprint, render_template

communities_bp = Blueprint("communities", __name__)


@communities_bp.get("/communities")
@communities_bp.get("/community.html")
def communities():
    return render_template("community.html")
