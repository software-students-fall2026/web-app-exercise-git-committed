# Layan's General Feed, voting, and Following

This is a local feature draft for Sonder, adapted from Layan's General Feed and
Following frames in the team's SWE Project 2 Figma file. The sample preview also
hosts Yasmine's welcome/login/register drafts and Sofia's profile/saved drafts
from shared main. It connects their navigation without implementing their
authentication, profile, or saved-post features.

Design references: [General Feed](https://www.figma.com/design/B87pv50oweBAdZFf44I97m/SWE-Project-2?node-id=23-130)
and [Following](https://www.figma.com/design/B87pv50oweBAdZFf44I97m/SWE-Project-2?node-id=23-457).
This is a simplified functional version of those two screens. At Layan's request,
the current draft keeps the sidebar and bordered song cards, with simple text
navigation, initial avatars, and black-and-white Arial styling. Decorative
artwork and the duplicate song/following panels have been removed. Headings and
sample captions stay plain. Navigation still connects to the team's other completed page drafts.
The Figma file itself has not been edited.

## Run the local preview

From this checkout, using Python 3.10 or newer:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python preview.py --demo
```

On Windows, use `python` and `.venv\Scripts\python.exe` instead.

Open `http://127.0.0.1:5055/` for the connected demo, or `/feed` to go straight to
Layan's pages. The server binds only to the local computer.
`--demo` creates fictional people and posts in memory, signs in a fictional user,
and labels both screens as a sample preview. Follow/unfollow and votes survive
page reloads in that process, but all demo changes reset when it stops. Demo mode
never connects to a supplied MongoDB server, even if `.env` contains a Mongo URI.

- `/feed`: posts from everyone; switch between Most upvoted and Newest, search songs/artists, and upvote/remove an upvote.
- `/following`: newest posts from followed listeners, plus the following list, name/username search, and follow/unfollow.
- `/appScreen.html`, `/login.html`, `/register.html`: Yasmine's page drafts. The
  demo disables credential fields and offers **Continue with sample account**.
  No account is created and no password is submitted.
- `/profilePage.html`, `/saved.html`: Sofia's static drafts with links back to
  the feeds. They are labeled as examples; unfinished actions are disabled.
- The original `/generalFeed.html` and `/following.html` links redirect to the
  working feeds. Empty Explore, Communities, and Create Post pages remain pending.
- Use a song's Listen button to open its official Spotify player. This reveals
  the player; it does not promise automatic playback or a full-song preview.
- Vote and follow changes use POST forms with CSRF protection and redirect back
  to a fresh server-rendered page. There is no optimistic UI pretending a write succeeded.

## Connect to the team's app

The feature code is a Flask Blueprint. Once Yasmine's Flask-Login setup and the
team's PyMongo database are available, register it with:

```python
from sonder_feed import init_app

# app already has a SECRET_KEY, LoginManager, and user_loader configured.
# db is the PyMongo Database used by the rest of the team.
init_app(app, db)
```

Routes identify the actor using `flask_login.current_user.get_id()`. They do not
accept an actor's user ID from a form. The host app supplies the actual login
page; without an authenticated user these routes return 401 (or the host's login
redirect if configured). `preview.py` is a temporary development host, not a
replacement for Yasmine's account work.

Database contract to agree with the team:

| Collection | Fields used here |
| --- | --- |
| `users` | `_id` (string or ObjectId), `username`, `display_name`; optional `bio`, `genres` |
| `posts` | `_id` (string or ObjectId), `user_id` (string of author's ID), `title`, `artist`, `spotify_url`, `caption`, `created_at` (UTC datetime); optional `genre` |
| `follows` | `follower_id`, `followed_id` (both strings), `created_at` |
| `votes` | `user_id`, `post_id` (both strings), `created_at` |

Ray's Create Post code must write the post fields above, or this adapter must be
updated to the team's agreed schema. As shown in Figma, General Feed means posts
from everyone; Following means posts from followed listeners. Votes are upvotes
only, with at most one per user/post. Top picks ranks all matching posts by vote
count before pagination; Newest and Following stay chronological. Unfollowing
removes that person's posts from Following but leaves them in General Feed.
The Following screen also lets users find accounts by name; the separate
Explore feed remains Jolie and Ray's responsibility.

`init_app` creates unique indexes for each follow pair and vote pair, plus a
post-author/date index. The team's final app should configure these indexes once
at startup. MongoDB is accessed through PyMongo in a normal host app. This local
preview has not verified the team's real MongoDB credentials or persistence.

For a real local Mongo connection in the temporary host, copy `env.example` to
`.env`, supply your own SECRET_KEY and Mongo settings, and run `preview.py`
without `--demo`. Real authentication must then be wired to this host or these
features registered in the team's authenticated app. Do not commit `.env`.

## Checks

```sh
.venv/bin/python -m pytest -q
```

Tests use `mongomock`, not a live MongoDB server. They check follow-driven feed
visibility and ordering, general/following separation, search, ranking before
pagination, saved state across requests, duplicate vote/follow
prevention, pagination, authentication, CSRF, safe music embeds and redirects,
and temporary-demo isolation.

## Short progress demo

1. Open `/feed`: explain that General Feed includes every listener's recommendations.
2. Upvote a song, reload to show it is saved in this running preview, then undo it.
3. Click Newest, then search for a song or artist and clear the search.
4. Follow Noor from a post or Find people.
5. Open Following: Noor's post is included. Unfollow Noor and show it disappear.
6. Open a song's Spotify player if internet is available.
7. Open Profile, then Saved, then return to General Feed. For the full entry flow,
   start at `/`, choose Log In or Register, then Continue with sample account.

The preview uses fictional data and a fictional signed-in identity. All state
resets when its process stops; real shared login and MongoDB integration remain
pending. `demo_pages.py` hosts the linked HTML drafts only in `--demo` mode. Comments,
downvotes, saves, concert attendance, and taste-match percentages are omitted
from this basic two-screen draft. The layout uses plain text and initial avatars;
the earlier decorative artwork and fonts are not included in this feature.

## Sharing this branch

The local branch is `layan-feed-following`. It includes shared main through
Sofia's sidebar-navigation update, PR #21 (`be785b7`). Her General Feed,
Following, Saved, and Profile destinations are preserved. The demo keeps empty
Explore and Communities pages marked as pending. Before sharing, review the
changed files and run the checks above. Commit and push this branch only when
Layan authorizes it.
Open a pull request against **software-students-fall2026/web-app-exercise-git-committed**,
base branch **main**, and have another teammate review and merge it as the
assignment requires. The PR should include the feed module, local demo runner,
and the small navigation/demo-state changes to the existing HTML pages.

If main changes before that step, bring those changes into this branch and
recheck the demo. Keep both teammates' work when resolving any overlapping
navigation edits. Do not replace the team's pages with copies of the feeds.

## Course setup status

This draft used AI assistance. The instructor automation files are unchanged.
This feature does not claim that the setup script was run or that tracking hooks
were approved or activated.
