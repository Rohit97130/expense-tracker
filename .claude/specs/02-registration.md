# Spec: Registration

## Overview

This feature implements user registration for Spendly — turning the existing `/register` GET route (which only renders a static form) into a working signup flow that creates a real row in the `users` table. This is the first authentication step in the roadmap, building directly on the SQLite data layer from Step 1, and unblocks login (Step 3) and every logged-in feature after it (profile, expenses).

## Depends on

- Step 1 — Database setup (`database/db.py`: `get_db()`, `init_db()`, `users` table). Must be complete — it is.

## Routes

- `GET /register` — render the registration form — public (already exists, unchanged)
- `POST /register` — validate input, create the user, redirect to login — public

## Database changes

No database changes. The existing `users` table (`id`, `name`, `email` UNIQUE, `password_hash`, `created_at`) already supports registration as-is.

## Templates

**Create:** none — `templates/register.html` already exists with the required form fields (`name`, `email`, `password`) and an `{% if error %}` block.

**Modify:**
- `templates/register.html` — none required for the happy path; the existing `error` block already supports server-side validation messages.

## Files to change

- `app.py` — change `register()` to accept `GET` and `POST`; on `POST`, validate input, check for duplicate email, hash the password, insert the user via `get_db()`, and redirect to `/login` on success or re-render the form with `error` on failure.

## Files to create

None.

## New dependencies

No new dependencies.

## Rules for implementation

- No SQLAlchemy or ORMs
- Parameterised queries only — no string formatting in SQL
- Passwords hashed with `werkzeug.security.generate_password_hash` before storing
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Validate required fields (name, email, password) server-side, not just via HTML `required`
- Check for duplicate email before inserting; on conflict, re-render `register.html` with a clear `error` message instead of raising an unhandled exception
- On successful registration, redirect to `/login` (do not log the user in automatically — that's Step 3's job)

## Definition of done

- [ ] Visiting `/register` still shows the existing form
- [ ] Submitting the form with valid, unique data creates a new row in `users` with a hashed password (verify via sqlite3 CLI or a quick script — plaintext password must not appear in the DB)
- [ ] Submitting the form redirects to `/login` on success
- [ ] Submitting with an email that already exists re-renders `/register` with an error message and does not create a duplicate row
- [ ] Submitting with a missing required field re-renders `/register` with an error message and does not create a row
- [ ] App starts and runs without errors (`python app.py`)
