"""Only the feed / following routes; authentication belongs to the host app."""

import re
from datetime import timezone
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from flask import Blueprint, abort, current_app, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from flask_wtf import FlaskForm
from flask_wtf.csrf import generate_csrf
from wtforms import HiddenField
from wtforms.validators import AnyOf

blueprint = Blueprint(
    "sonder_feed", __name__, template_folder="templates",
    static_folder="static", static_url_path="/sonder-feed-assets"
)

class ActionForm(FlaskForm):
    state = HiddenField(validators=[AnyOf(["on", "off"])])
    return_to = HiddenField()


def repository():
    return current_app.extensions["sonder_feed"]


def spotify_embed_url(value):
    """Build an official player URL, never render arbitrary user-provided HTML."""
    if not isinstance(value, str):
        return None
    try:
        parsed = urlsplit(value)
    except ValueError:
        return None
    if parsed.scheme != "https" or parsed.netloc != "open.spotify.com":
        return None
    match = re.fullmatch(
        r"/(?:intl-[a-z]{2}/)?(track|album|playlist)/([A-Za-z0-9]{22})/?", parsed.path
    )
    if not match:
        return None
    kind, identifier = match.groups()
    return f"https://open.spotify.com/embed/{kind}/{identifier}?theme=0"


def display_date(value):
    if not hasattr(value, "strftime"):
        return "Date unavailable"
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    value = value.astimezone(ZoneInfo(current_app.config.get("SONDER_TIMEZONE", "America/New_York")))
    return value.strftime("%b %d, %Y").replace(" 0", " ")


@blueprint.app_context_processor
def template_helpers():
    return {
        "csrf_token": generate_csrf,
        "spotify_embed_url": spotify_embed_url,
        "display_date": display_date,
        "preview_mode": current_app.config.get("SONDER_DEMO", False),
    }


@blueprint.get("/feed")
@login_required
def feed():
    return render_feed("feed")


@blueprint.get("/following")
@login_required
def following():
    return render_feed("following")


def render_feed(active_page):
    try:
        page = int(request.args.get("page", "1"))
    except ValueError:
        abort(400)
    if page < 1 or page > 10000:
        abort(400)
    query = request.args.get("q", "").strip()[:80]
    people_query = request.args.get("people_q", "").strip()[:80]
    sort = request.args.get("sort", "top") if active_page == "feed" else "newest"
    if sort not in {"top", "newest"}:
        abort(400)
    if active_page == "feed":
        posts, has_next = repository().general_feed(current_user.get_id(), page=page, query=query, sort=sort)
    else:
        posts, has_next = repository().feed(current_user.get_id(), page=page, query=query)
    people = repository().following(current_user.get_id())
    matches = repository().find_people(current_user.get_id(), people_query)
    return render_template(
        "sonder_feed/following.html" if active_page == "following" else "sonder_feed/feed.html",
        active_page=active_page, posts=posts,
        following_count=len(people), people=people, matches=matches,
        query=query, people_query=people_query, sort=sort,
        page=page, has_next=has_next,
        followed_ids={str(person["_id"]) for person in people},
    )


def action_state():
    form = ActionForm()
    if not form.validate_on_submit():
        abort(400, description="This action could not be verified. Reload the page and try again.")
    return form.state.data == "on"


def return_to_page(default_endpoint):
    destination = request.form.get("return_to", "")
    try:
        parsed = urlsplit(destination)
    except ValueError:
        return redirect(url_for(default_endpoint), code=303)
    allowed_paths = {url_for("sonder_feed.feed"), url_for("sonder_feed.following")}
    if not parsed.scheme and not parsed.netloc and parsed.path in allowed_paths:
        return redirect(destination, code=303)
    return redirect(url_for(default_endpoint), code=303)


@blueprint.post("/posts/<post_id>/vote")
@login_required
def vote(post_id):
    enabled = action_state()
    post = repository().find_post(post_id)
    if post is None:
        abort(404)
    repository().set_vote(current_user.get_id(), str(post["_id"]), enabled)
    return return_to_page("sonder_feed.feed")


@blueprint.post("/people/<user_id>/follow")
@login_required
def follow(user_id):
    enabled = action_state()
    person = repository().find_user(user_id)
    if person is None:
        abort(404)
    target_id = str(person["_id"])
    if target_id == current_user.get_id():
        abort(400, description="You cannot follow yourself.")
    repository().set_follow(current_user.get_id(), target_id, enabled)
    return return_to_page("sonder_feed.following")
