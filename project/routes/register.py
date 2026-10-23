from flask import Blueprint, render_template

register_bp = Blueprint("register", __name__)


@register_bp.get("/register")
@register_bp.get("/register.html")
def register():
    return render_template("register.html")
