import pytest
from werkzeug.security import generate_password_hash

from app import app as flask_app
from database.db import get_db


@pytest.fixture
def app():
    yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def demo_user_id():
    conn = get_db()
    row = conn.execute(
        "SELECT id FROM users WHERE email = ?", ("demo@spendly.com",)
    ).fetchone()
    conn.close()
    return row["id"]


@pytest.fixture
def empty_user_id():
    conn = get_db()
    email = "empty-user-test@spendly.com"
    existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if existing:
        user_id = existing["id"]
    else:
        password_hash = generate_password_hash("password123")
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Empty User", email, password_hash),
        )
        user_id = cursor.lastrowid
        conn.commit()
    conn.close()
    return user_id
