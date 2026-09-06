# Spec: Login And Logout

## Overview

This feature implements session-based authentication for Spendly — turning the existing `/login` GET route (static form only) into a working sign-in flow, and turning the `/logout` stub into a real session-clearing route. This is the second authentication step in the roadmap, building on the `users` table (Step 1) and real user rows created by registration (Step 2). It unblocks every logged-in feature after it (profile, expenses), which all depend on knowing who the current user is.

## Depends on

- Step 1 — Database setup (`database/db.py`: `get_db()`, `users` table).
- Step 2 — Registration (`app.py`: `/register` creates real hashed-password rows in `users`). Must be complete — it is.

## Routes

- `GET /login` — render the sign-in form — public only; redirects logged-in users to `/`
- `POST /login` — validate credentials, start a session, redirect to landing page — public
- `GET /logout` — clear the session, redirect to landing — logged-in (replaces the current stub)
- `GET /register` — render the registration form — public only; redirects logged-in users to `/`

## Database changes

No database changes. The existing `users` table (`id`, `name`, `email`, `password_hash`, `created_at`) already supports authentication as-is.

## Templates

**Create:** none — `templates/login.html` already exists with the required form fields (`email`, `password`) and an `{% if error %}` block.

**Modify:**
- `templates/login.html` — none required for the happy path; the existing `error` block already supports server-side validation messages.
- `templates/base.html` — nav links (`Sign in` / `Get started`) should reflect logged-in state: show `Sign out` (linking to `/logout`) and the user's name instead when a session exists, otherwise keep the current `Sign in` / `Get started` links.

## Files to change

- `app.py`:
  - Set `app.secret_key` (required for Flask session cookies to work) — read from an environment variable with a hardcoded dev fallback, since there's no secrets/config system yet.
  - Change `login()` to accept `GET` and `POST`; if a session already exists, redirect to `/` immediately (regardless of method). Otherwise on `POST`, look up the user by email, verify the password with `werkzeug.security.check_password_hash`, store `user_id` and `user_name` in `session` on success, and redirect to `/` (landing page), or re-render the form with `error` on failure.
  - Change `logout()` to clear the session (`session.clear()`) and redirect to `/` (landing page), replacing the current placeholder string response.
  - Change `register()` to redirect logged-in users straight to `/`, same guard as `login()`, so an authenticated user can't reach the signup form either.
- `templates/base.html` — conditionally render nav links based on `session.get('user_id')`.

## Files to create

None.

## New dependencies

No new dependencies. Uses `werkzeug.security.check_password_hash` (already available via werkzeug, already imported for `generate_password_hash` in Step 2) and Flask's built-in `session`.

## Rules for implementation

- No SQLAlchemy or ORMs
- Parameterised queries only — no string formatting in SQL
- Passwords verified with `werkzeug.security.check_password_hash` — never compare plaintext passwords
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Validate required fields (email, password) server-side, not just via HTML `required`
- On invalid credentials (unknown email OR wrong password), re-render `login.html` with a single generic error message ("Invalid email or password.") — do not reveal whether the email exists, to avoid leaking account existence
- `/logout` must work regardless of whether a session currently exists (clearing an empty session is a no-op, not an error)
- Session must store only `user_id` and `user_name` — never store `password_hash` or any other sensitive field in the session

## Definition of done

- [ ] Visiting `/login` still shows the existing form
- [ ] Submitting valid credentials (e.g. the demo user `demo@spendly.com` / `demo123`, or a user created via `/register`) redirects to `/` and sets a session cookie
- [ ] Submitting an unknown email re-renders `/login` with "Invalid email or password." and does not set a session
- [ ] Submitting a known email with the wrong password re-renders `/login` with "Invalid email or password." and does not set a session
- [ ] Submitting with a missing required field re-renders `/login` with an error message
- [ ] After logging in, the nav bar shows a "Sign out" link instead of "Sign in" / "Get started"
- [ ] Visiting `/logout` after logging in clears the session and redirects to `/`; the nav bar reverts to "Sign in" / "Get started"
- [ ] Visiting `/logout` with no active session does not error, and redirects to `/`
- [ ] While logged in, visiting `/login` or `/register` redirects to `/` instead of showing the form
- [ ] While logged out, `/login` and `/register` still render normally
- [ ] App starts and runs without errors (`python app.py`)
