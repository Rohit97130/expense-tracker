import os
from datetime import date, datetime

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database.db import get_db, init_db, seed_db
from database.queries import (
    get_category_breakdown,
    get_recent_transactions,
    get_summary_stats,
    get_user_by_id,
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("landing"))

    if request.method == "GET":
        return render_template("register.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not name or not email or not password:
        return render_template("register.html", error="All fields are required.")

    conn = get_db()
    existing = conn.execute(
        "SELECT id FROM users WHERE email = ?", (email,)
    ).fetchone()
    if existing:
        conn.close()
        return render_template("register.html", error="An account with that email already exists.")

    password_hash = generate_password_hash(password)
    conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        (name, email, password_hash),
    )
    conn.commit()
    conn.close()

    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("landing"))

    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not email or not password:
        return render_template("login.html", error="Invalid email or password.")

    conn = get_db()
    user = conn.execute(
        "SELECT id, name, password_hash FROM users WHERE email = ?", (email,)
    ).fetchone()
    conn.close()

    if not user or not check_password_hash(user["password_hash"], password):
        return render_template("login.html", error="Invalid email or password.")

    session["user_id"] = user["id"]
    session["user_name"] = user["name"]

    return redirect(url_for("profile"))


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


def _parse_date_param(value):
    if not value:
        return None
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return None
    return value


def _month_start(d):
    return d.replace(day=1)


def _months_ago(d, months):
    month_index = d.month - 1 - months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, 1)


def _date_presets():
    today = date.today()
    return {
        "month": (_month_start(today).isoformat(), today.isoformat()),
        "3m": (_months_ago(today, 3).isoformat(), today.isoformat()),
        "6m": (_months_ago(today, 6).isoformat(), today.isoformat()),
    }


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    user_id = session["user_id"]
    name = session.get("user_name", "")
    initials = "".join(part[0].upper() for part in name.split()[:2]) or "?"

    date_from = _parse_date_param(request.args.get("date_from"))
    date_to = _parse_date_param(request.args.get("date_to"))

    if date_from and date_to and date_from > date_to:
        date_from = None
        date_to = None
        flash("Start date must be before end date.")

    presets = _date_presets()
    active_preset = "all"
    if date_from and date_to:
        # None means a custom range that doesn't match any preset —
        # the date inputs (not a preset button) show the active state.
        active_preset = next(
            (key for key, value in presets.items() if value == (date_from, date_to)),
            None,
        )

    user = get_user_by_id(user_id)
    summary = get_summary_stats(user_id, date_from=date_from, date_to=date_to)
    transactions = get_recent_transactions(user_id, limit=10, date_from=date_from, date_to=date_to)
    breakdown = get_category_breakdown(user_id, date_from=date_from, date_to=date_to)

    stats = [
        {"label": "Total spent", "value": summary["total_spent"]},
        {"label": "Transactions", "value": str(summary["transaction_count"])},
        {"label": "Top category", "value": summary["top_category"]},
    ]

    categories = [
        {"category": cat["name"], "amount": cat["amount"], "percent": cat["pct"]}
        for cat in breakdown
    ]

    return render_template(
        "profile.html",
        email=user["email"] if user else "",
        member_since=user["member_since"] if user else "",
        initials=initials,
        stats=stats,
        transactions=transactions,
        categories=categories,
        date_from=date_from,
        date_to=date_to,
        active_preset=active_preset,
        presets=presets,
    )


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
