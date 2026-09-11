from datetime import datetime

from database.db import get_db


def _format_currency(amount):
    return f"₹{amount:,.2f}"


# --- Subagent 1: get_recent_transactions --- (only this agent edits below, until next marker)

def get_recent_transactions(user_id, limit=10):
    conn = get_db()
    rows = conn.execute(
        "SELECT date, description, category, amount FROM expenses "
        "WHERE user_id = ? ORDER BY date DESC, id DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    conn.close()

    return [
        {
            "date": row["date"],
            "description": row["description"],
            "category": row["category"],
            "amount": _format_currency(row["amount"]),
        }
        for row in rows
    ]


# --- Subagent 2: get_summary_stats --- (only this agent edits below, until next marker)

def get_summary_stats(user_id):
    conn = get_db()
    total_row = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) AS total, COUNT(*) AS count FROM expenses WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    top_row = conn.execute(
        "SELECT category, SUM(amount) AS category_total FROM expenses WHERE user_id = ? "
        "GROUP BY category ORDER BY category_total DESC LIMIT 1",
        (user_id,),
    ).fetchone()
    conn.close()

    top_category = top_row["category"] if top_row is not None else "—"

    return {
        "total_spent": _format_currency(total_row["total"]),
        "transaction_count": total_row["count"],
        "top_category": top_category,
    }


# --- Subagent 3: get_category_breakdown --- (only this agent edits below, until next marker)

def get_category_breakdown(user_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT category, SUM(amount) AS category_total FROM expenses "
        "WHERE user_id = ? GROUP BY category ORDER BY category_total DESC",
        (user_id,),
    ).fetchall()
    conn.close()

    if not rows:
        return []

    grand_total = sum(row["category_total"] for row in rows)

    raw_pcts = [round(row["category_total"] / grand_total * 100) for row in rows]
    drift = 100 - sum(raw_pcts)
    raw_pcts[0] += drift

    return [
        {
            "name": row["category"],
            "amount": _format_currency(row["category_total"]),
            "pct": pct,
        }
        for row, pct in zip(rows, raw_pcts)
    ]


def get_user_by_id(user_id):
    conn = get_db()
    row = conn.execute(
        "SELECT name, email, created_at FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    conn.close()

    if row is None:
        return None

    created = datetime.strptime(row["created_at"], "%Y-%m-%d %H:%M:%S")

    return {
        "name": row["name"],
        "email": row["email"],
        "member_since": created.strftime("%B %Y"),
    }
