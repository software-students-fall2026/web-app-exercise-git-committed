# Web Application Exercise

A little exercise to build a web application following an agile development process. See the [instructions](instructions.md) for more detail.

## Product vision statement

A web app where users can explore different songs and get recommendations from real users instead of the algorithm.

## User stories

[User stories](https://github.com/software-students-fall2026/web-app-exercise-git-committed/issues)

## Steps necessary to run the software

Install Git and Python 3.11 or newer. You also need a MongoDB connection string
and a database user with read/write access to the `sonder` database. For the
team's Atlas cluster, get the credentials privately from a teammate and add
your current public IP address to the project's IP Access List.

Check your Python version with `python3 --version` on macOS/Linux or
`python --version` on Windows. If it is older than 3.11, use your newer Python
executable (for example, `python3.13`) when creating the virtual environment.

1. Clone the shared repository:

   ```sh
   git clone https://github.com/software-students-fall2026/web-app-exercise-git-committed.git
   cd web-app-exercise-git-committed
   ```

2. Create a virtual environment and install the dependencies. Run these commands
   from the repository's main folder.

   macOS/Linux:

   ```sh
   python3 -m venv .venv
   .venv/bin/python -m pip install -r requirements.txt
   ```

   Windows (PowerShell):

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

3. Copy `env.example` to `.env` in the repository's main folder. Keep your
   existing `.env` if you already have one. Replace the dummy values:

   - `MONGO_URI`: your MongoDB connection string, including the database username
     and password. URL-encode special characters in the username or password.
   - `MONGO_DB`: `sonder` for the team's database.
   - `SECRET_KEY`: a random secret for Flask sessions. Generate one with the
     following command, then paste the output into `.env`.

   macOS/Linux:

   ```sh
   .venv/bin/python -c "import secrets; print(secrets.token_hex(32))"
   ```

   Windows (PowerShell):

   ```powershell
   .\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
   ```

   Keep `.env` private. It is ignored by Git; `env.example` contains dummy values
   only. MongoDB creates collections when the app first writes data to them.

4. Start Flask from the repository's main folder.

   macOS/Linux:

   ```sh
   .venv/bin/python -m flask --app project/app.py run --port 5055
   ```

   Windows (PowerShell):

   ```powershell
   .\.venv\Scripts\python.exe -m flask --app project/app.py run --port 5055
   ```

5. Open http://127.0.0.1:5055/ in your browser. Keep the terminal running and
   press Ctrl+C there to stop the app. The Flask backend status is available at
   http://127.0.0.1:5055/api/health.

If the port is already in use, stop the other local server or use another port
with `--port`, then open that port in your browser. If MongoDB cannot connect,
check your `.env` credentials, Atlas IP Access List, and internet connection.

## Task boards

- [Git Committed – Sprint 1.](https://github.com/orgs/software-students-fall2026/projects/42)
- [Git Committed – Sprint 2](https://github.com/orgs/software-students-fall2026/projects/86)
