# Web Application Exercise

A little exercise to build a web application following an agile development process. See the [instructions](instructions.md) for more detail.

## Product vision statement

A web app where users can explore different songs and get recommendations from real users instead of the algorithm.

## User stories

See instructions. Delete this line and place a link to the user stories here.

## Steps necessary to run the software

The current draft runs locally with temporary sample data. Use Python 3.10 or newer:

```sh
git clone https://github.com/software-students-fall2026/web-app-exercise-git-committed.git
cd web-app-exercise-git-committed
python3 .automations/setup.py
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python preview.py --demo
```

Follow the setup script's instructions to approve the course hooks. On Windows,
use `python` and `.venv\Scripts\python.exe` in place of `python3` and `.venv/bin/python`.

Open `http://127.0.0.1:5055/`. Welcome, login/register, General Feed,
Following, Profile, and Saved are linked in one preview. Choose **Continue with
sample account** on the account screens. Real login/registration is not connected;
Profile and Saved show static example content. Explore, Communities, and Create
Post are still pending. Voting, search, and follow/unfollow work in the sample feeds.

No MongoDB credentials are needed for `--demo`. Data resets when the process stops.
See [FEED_DEVELOPMENT.md](FEED_DEVELOPMENT.md) for the feed's database contract,
checks, and steps for connecting it to the team's eventual authenticated app.

## Task boards

See instructions. Delete this line and place a link to the task boards here.
