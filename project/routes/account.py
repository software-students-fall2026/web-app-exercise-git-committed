from bson import ObjectId
from bson.errors import InvalidId
from flask import Blueprint, render_template
from flask_login import LoginManager, UserMixin

account_bp = Blueprint("account", __name__)
login_manager = LoginManager()


class User(UserMixin):
    def __init__(self, document):
        self.id = str(document["_id"])
        self.username = document.get("username", "")
        self.display_name = document.get("display_name", self.username)
        self.email = document.get("email", "")


@login_manager.user_loader
def load_user(user_id):
    if not isinstance(user_id, str):
        return None
    try:
        object_id = ObjectId(user_id)
    except (InvalidId, TypeError):
        return None

    # Connect only when loading a signed-in user, not when opening a sample page.
    from database import users_collection

    document = users_collection.find_one({"_id": object_id})
    return User(document) if document is not None else None


@account_bp.get("/")
@account_bp.get("/appScreen.html")
def welcome():
    return render_template("appScreen.html")
