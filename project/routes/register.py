from flask import Blueprint, request, redirect, flash
from werkzeug.security import generate_password_hash
from pymongo.errors import DuplicateKeyError

from database import users_collection

register_bp = Blueprint('registration', __name__)

@register_bp.route("/api/register" , methods=["POST"])
def register_user():
    display_name = request.form.get("display_name", "").strip()
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not all([display_name, username, email, password]):
        flash("Please fill in all fields", "error")
        return redirect("/register")
    if len(password) < 8:
        flash("Password minimum is 8 characters", "error")
        return redirect("/register")
    existing_user = users_collection.find_one({
        "$or":[
            {"username": username},
            {"email": email}
        ]
    })
    if existing_user:
        flash("Username or email is already registered", "error")
        return redirect("/register")
    user_doc = {
        "display_name": display_name,
        "username": username,
        "email": email,
        "password_hash": generate_password_hash(password) 
    }
    try:
        users_collection.insert_one(user_doc)
    except DuplicateKeyError:
        flash("Username or email is already registered", "error")
        return redirect("/register")
    flash("Account created, please log in", "success")
    return redirect("/login")