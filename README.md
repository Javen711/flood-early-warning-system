# AFEWS — AI-Powered Early Warning System for Flood Risk

Final year project: an AI-powered flood early warning system for informal
settlements, using a Random Forest model over rainfall/drainage/elevation data,
with SMS + mobile alerting.

## Project structure

    afews_project/
      backend/     Django REST API + MySQL (this is what Phase 0 sets up)
      frontend/    React admin/officer dashboard        (Phase 7)
      ml/          Model training & experimentation      (Phase 4)
      mobile/      Flutter/React Native resident app     (Phase 8)
      docs/        Diagrams, roadmap, and other project docs

See `Development_Roadmap.md` in `docs/` for the full phase-by-phase build plan.

## Backend setup (Phase 0)

**Prerequisites:** Python 3.10+, MySQL Server running locally (or a connection
string to a remote instance).

1. **Clone and enter the backend folder**
   ```bash
   cd afews_project/backend
   ```

2. **Create and activate a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate        # Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create your local `.env` file**
   ```bash
   cp .env.example .env
   ```
   Then open `.env` and fill in:
   - `DJANGO_SECRET_KEY` — generate one with:
     ```bash
     python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
     ```
   - `DB_NAME`, `DB_USER`, `DB_PASSWORD` — matching a MySQL database/user you create next.

5. **Create the MySQL database and user**
   ```sql
   CREATE DATABASE afews_db CHARACTER SET utf8mb4;
   CREATE USER 'afews_user'@'localhost' IDENTIFIED BY 'change-me';
   GRANT ALL PRIVILEGES ON afews_db.* TO 'afews_user'@'localhost';
   FLUSH PRIVILEGES;
   ```
   (Use the same values you put in `.env`.)

6. **Run migrations**
   ```bash
   python manage.py migrate
   ```

7. **Create an admin superuser** (for the Django admin panel)
   ```bash
   python manage.py createsuperuser
   ```

8. **Run the dev server**
   ```bash
   python manage.py runserver
   ```

9. **Confirm everything is wired up correctly** by visiting:
   - http://127.0.0.1:8000/api/health/ — should return
     `{"service": "AFEWS backend", "status": "ok", "database": "connected"}`
   - http://127.0.0.1:8000/admin/ — Django admin login

If `database` shows `"unreachable"` instead of `"connected"`, double-check your
`.env` values and that MySQL is actually running.

## Git workflow

- `main` — always working.
- Create a feature branch per roadmap task, e.g. `feature/1.1-database-schema`.
- Commit at the checkbox level from `Development_Roadmap.md` — small, reviewable
  commits make it much easier to show incremental progress to your supervisor.

## What's next

Phase 0 is done once `python manage.py runserver` works and `/api/health/`
reports a connected database. From there, move to **Phase 1 — Database Layer**:
turning the ER diagram into real Django models for `Zone`, `Resident`,
`EnvironmentalData`, `AlertThreshold`, `FloodPrediction`, `Alert`,
`AlertDelivery`, and `Feedback`.
