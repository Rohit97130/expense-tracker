# Spec: Backend Routes For Profile Page

## Overview
This feature replaces the hardcoded mock data in the `/profile` route with real queries against the `expenses` table. Step 4 built the profile page UI using static Python literals so the design could be validated in isolation; this step wires that same template to the logged-in user's actual data — total spent, transaction count, top category, recent transactions, and category breakdown — all computed from SQLite via `get_db()`. No new templates or routes are introduced; the existing `/profile` view function is rewritten to query instead of hardcode.

## Depends on
- Step 1: Database setup (`users` and `expenses` tables must exist)
- Step 2: Registration (user accounts must be creatable)
- Step 3: Login + Logout (session must be set; `/profile` must be a protected route)
- Step 4: Profile page design (`profile.html` template and its expected context shape — `stats`, `transactions`, `categories`, `initials`, `email`, `member_since` — already exist)

## Routes
No new routes. `GET /profile` — existing route, behavior changes from hardcoded context to DB-backed context — logged-in only (redirect to `/login` if not authenticated).

## Database changes
No database changes. The existing `expenses` table (`id, user_id, amount, category, date, description, created_at`) and `users` table are sufficient. No new columns, tables, or constraints needed.

## Templates
- Create: none.
- Modify: none. `templates/profile.html` already consumes `stats`, `transactions`, `categories`, `initials`, `email`, `member_since` in the exact shape the current mock data provides — the new DB-backed context must match that same shape so the template requires no changes.

## Files to change
- `app.py` — rewrite the `/profile` view function to:
  - Keep the existing auth guard (`session.get("user_id")` → redirect to `/login`)
  - Query `expenses` for the current `user_id` (via `session["user_id"]`), ordered by `date DESC`, to build:
    - `transactions`: recent expenses (date, description, category, amount formatted as `₹X,XXX.XX`)
    - `stats`: total spent (sum of all amounts for the user), transaction count, top category (category with highest total spend)
    - `categories`: per-category totals and percentage of overall spend, sorted descending by amount
  - Query `users` for the current user's `email` and `created_at` (formatted as `member_since`, e.g. "August 2026")
  - Keep computing `initials` from `session.get("user_name")` as before
  - Close the DB connection after use

## Files to create
None.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — use raw sqlite3 via `get_db()`
- Parameterised queries only — never string-format SQL
- Passwords hashed with werkzeug (no changes to auth in this step)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Authentication guard stays as-is: check `session.get("user_id")`; if absent, `redirect(url_for("login"))`
- All amount values formatted as strings (`₹X,XXX.XX`) in `app.py` before being passed to the template, matching the existing mock-data format exactly, so `profile.html` needs zero changes
- If a user has zero expenses, the route must still render successfully with empty `transactions`/`categories` lists and zero-valued `stats` (no division-by-zero, no crash)
- Category percentages must sum to ~100% and be computed from the user's own totals only (never another user's data)

## Definition of done
- [ ] Visiting `/profile` without being logged in still redirects to `/login`
- [ ] Logging in as the seeded demo user (`demo@spendly.com` / `demo123`) and visiting `/profile` shows the 8 seeded expenses as real transactions, not the old hardcoded 6
- [ ] "Total spent" stat matches the actual sum of the demo user's seeded expenses
- [ ] "Top category" stat matches the category with the highest real total for that user
- [ ] Category breakdown percentages are computed from real data and sum to ~100%
- [ ] Registering a brand-new user with zero expenses and visiting `/profile` renders without errors, showing empty/zero state instead of crashing
- [ ] No other user's expenses ever appear on a given user's profile page
- [ ] No hex colour values appear in any modified code — only CSS variables in templates/CSS
