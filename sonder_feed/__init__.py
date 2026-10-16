"""Layan's feed, voting, and following features for the team's Flask app."""

from .repository import FeedRepository


def init_app(app, database):
    """Register these features with an existing Flask / Flask-Login app."""
    from .routes import blueprint

    repository = FeedRepository(database)
    repository.create_indexes()
    app.extensions["sonder_feed"] = repository
    app.register_blueprint(blueprint)
