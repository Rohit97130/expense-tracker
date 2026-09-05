 # CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

"Spendly" is a Flask-based personal expense tracker, built incrementally as a step-by-step learning project. Many core pieces are intentionally unimplemented placeholders (see below) — this is expected, not broken code. `file.txt` in the repo root contains the running log of feature prompts/instructions used to build this project so far (footer links, terms/privacy pages, hero redesign, "how it works" modal); treat it as historical context for *why* things look the way they do, not as a spec to re-execute.

## Commands

- Run the dev server: `python app.py` (serves on port 5001, debug mode on)
- Install deps: `pip install -r requirements.txt`
- Run tests: `pytest` (pytest and pytest-flask are declared as dependencies, but no tests currently exist in the repo)

There is no build step, linter, or frontend bundler — templates and static assets are served directly by Flask.

## Architecture

- **`app.py`** — single-file Flask app defining all routes. Real routes (`/`, `/register`, `/login`, `/terms`, `/privacy`) render Jinja templates. A block of placeholder routes (`/logout`, `/profile`, `/expenses/add`, `/expenses/<id>/edit`, `/expenses/<id>/delete`) currently just return plain strings like `"Add expense — coming in Step 7"` — these are stubs for future steps, not bugs.
- **`database/db.py`** — currently just a comment describing the intended interface: `get_db()` (SQLite connection with `row_factory` and foreign keys enabled), `init_db()` (creates tables with `CREATE TABLE IF NOT EXISTS`), `seed_db()` (sample dev data). No SQLite integration exists yet in `app.py`.
- **Templates (`templates/`)** — Jinja2, all extending `base.html` except `landing.html` which also extends `base.html`. `base.html` defines the shared nav/footer shell and exposes `{% block title %}`, `{% block head %}`, `{% block content %}`, and `{% block scripts %}` for child templates to override.
- **Static assets (`static/`)** — `css/style.css` holds all styles (no per-page CSS files, despite `file.txt` referencing a `landing.css` — that split never happened; everything landed in `style.css`). `js/main.js` is effectively empty; page-specific JS (e.g. the "how it works" modal) is currently written inline in `{% block scripts %}` within the template itself rather than in `main.js`.
- **No JS framework or build tooling** — vanilla JS only, per explicit project constraint (see the modal-implementation prompt in `file.txt`).

## Conventions to follow

- When adding a route that needs a template, follow the existing pattern: add the route in `app.py`, add a template extending `base.html`, and use `url_for(...)` for all internal links (never hardcode paths) — this is the convention in every existing template.
- Match the visual style of existing pages (`landing.html`, `terms.html`) when creating new pages, per prior instructions in `file.txt`.
- Keep JS framework-free; if a template needs page-specific script, the existing precedent is inline `{% block scripts %}` rather than adding to `main.js`.
