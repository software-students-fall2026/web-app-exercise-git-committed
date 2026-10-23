# Web Application Exercise

A little exercise to build a web application following an agile development process. See the [instructions](instructions.md) for more detail.

## Product vision statement

A web app where users can explore different songs and get recommendations from real users instead of the algorithm.

## User stories

See instructions. Delete this line and place a link to the user stories here.

## Steps necessary to run the software

Install Python 3, then clone the repository and set up a virtual environment:

```sh
git clone https://github.com/software-students-fall2026/web-app-exercise-git-committed.git
cd web-app-exercise-git-committed
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp env.example .env
```

On Windows, use `python` instead of `python3`, activate the environment with
`.venv\Scripts\activate`, and use `copy env.example .env` instead of `cp`.

In `.env`, replace `MONGO_URI` with the team's MongoDB connection string and keep
`MONGO_DB=sonder`. The database account and network access must allow your
computer to connect. Set `SECRET_KEY` to a random value generated with:

```sh
python -c "import secrets; print(secrets.token_hex(32))"
```

Keep the real `.env` file local; `env.example` contains dummy settings only.
Start the app from the repository's main directory:

```sh
python project/app.py
```

Open http://127.0.0.1:5000/ and use the page links to navigate. The Flask server
serves the existing HTML, CSS, images, and locally saved audio files. Audio files
are stored in `project/instance/uploads/audio/`.

The pages currently show sample content. Login, registration, uploading audio,
and database actions still need to be connected in the route files. The shared
setup provides session support and references to the MongoDB collections;
MongoDB is contacted when database-backed code runs. Search, sorting, voting,
and follow/unfollow controls remain layout placeholders.

## Task boards

See instructions. Delete this line and place a link to the task boards here.
