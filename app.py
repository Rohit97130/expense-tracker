import os

from flask import Flask, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database.db import get_db, init_db, seed_db

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


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    name = session.get("user_name", "")
    initials = "".join(part[0].upper() for part in name.split()[:2]) or "?"

    stats = [
        {"label": "Total spent", "value": "₹5,594.50"},
        {"label": "Transactions", "value": "8"},
        {"label": "Top category", "value": "Shopping"},
    ]

    transactions = [
        {"date": "2026-09-05", "description": "Groceries", "category": "Food", "amount": "₹450.00"},
        {"date": "2026-09-04", "description": "Cab fare", "category": "Transport", "amount": "₹120.50"},
        {"date": "2026-09-03", "description": "Electricity bill", "category": "Bills", "amount": "₹1,500.00"},
        {"date": "2026-09-01", "description": "Pharmacy", "category": "Health", "amount": "₹600.00"},
        {"date": "2026-08-30", "description": "Movie tickets", "category": "Entertainment", "amount": "₹350.00"},
        {"date": "2026-08-29", "description": "New shoes", "category": "Shopping", "amount": "₹2,200.00"},
    ]

    categories = [
        {"category": "Shopping", "amount": "₹2,200.00", "percent": 39},
        {"category": "Bills", "amount": "₹1,500.00", "percent": 27},
        {"category": "Health", "amount": "₹600.00", "percent": 11},
        {"category": "Food", "amount": "₹450.00", "percent": 8},
        {"category": "Entertainment", "amount": "₹350.00", "percent": 6},
        {"category": "Transport", "amount": "₹120.50", "percent": 2},
    ]

    return render_template(
        "profile.html",
        email="demo@spendly.com",
        member_since="August 2026",
        initials=initials,
        stats=stats,
        transactions=transactions,
        categories=categories,
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
