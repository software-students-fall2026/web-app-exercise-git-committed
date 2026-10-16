"""Local host for the team's page drafts and Layan's feed module.

The --demo flag uses only in-memory sample data and a fictional signed-in user.
Without it, a real MongoDB database and the team's login implementation are needed.
"""

import argparse
import os
import secrets
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, redirect, url_for
from flask_login import LoginManager, UserMixin, current_user, login_user
from pymongo import MongoClient

from sonder_feed import init_app


class PreviewUser(UserMixin):
    def __init__(self, document):
        self.id = str(document["_id"])
        self.display_name = document.get("display_name", document.get("username", "Listener"))


def create_app(database=None, *, demo=False, config=None):
    load_dotenv(Path(__file__).with_name(".env"))
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SONDER_DEMO=demo,
    )
    app.config.update(config or {})
    if demo:
        if database is not None:
            raise ValueError("Demo mode must never use an external database.")
        import mongomock
        from sample_data import seed_sample_data

        database = mongomock.MongoClient(tz_aware=True)["sonder_demo"]
        seed_sample_data(database)
        app.config["SECRET_KEY"] = secrets.token_hex(32)
    elif not app.config["SECRET_KEY"]:
        raise RuntimeError("Set SECRET_KEY in .env, or use --demo for a sample preview.")
    if database is None:
        uri = os.environ.get("MONGO_URI")
        if not uri:
            raise RuntimeError("Set MONGO_URI in .env, or use --demo for a sample preview.")
        client = MongoClient(uri, serverSelectionTimeoutMS=5000, tz_aware=True)
        database = client[os.environ.get("MONGO_DB", "sonder")]
        app.extensions["mongo_client"] = client

    manager = LoginManager(app)
    init_app(app, database)

    @manager.user_loader
    def load_user(user_id):
        document = app.extensions["sonder_feed"].find_user(user_id)
        return PreviewUser(document) if document else None

    if demo:
        from demo_pages import blueprint as demo_pages

        app.register_blueprint(demo_pages)

        @app.before_request
        def use_sample_identity():
            if not current_user.is_authenticated:
                login_user(load_user("demo-alex"))

    @app.get("/")
    def index():
        return redirect(url_for("team_demo.welcome" if demo else "sonder_feed.feed"))

    return app


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true", help="Use temporary in-memory sample data.")
    parser.add_argument("--port", type=int, default=5055)
    args = parser.parse_args()
    create_app(demo=args.demo).run(host="127.0.0.1", port=args.port, debug=False)
