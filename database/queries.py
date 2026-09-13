from datetime import datetime

from database.db import get_db


def _format_currency(amount):
    return f"₹{amount:,.2f}"


def _date_range_clause(date_from, date_to, params):
    if date_from and date_to:
        params.extend([date_from, date_to])
        return " AND date BETWEEN ? AND ?"
    return ""


# --- Subagent 1: get_recent_transactions --- (only this agent edits below, until next marker)

def get_recent_transactions(user_id, limit=10, date_from=None, date_to=None):
    sql = "SELECT date, description, category, amount FROM expenses WHERE user_id = ?"
    params = [user_id]

    sql += _date_range_clause(date_from, date_to, params)
    sql += " ORDER BY date DESC, id DESC LIMIT ?"
    params.append(limit)

    conn = get_db()
    rows = conn.execute(sql, params).fetchall()
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

def get_summary_stats(user_id, date_from=None, date_to=None):
    params = [user_id]
    date_filter = _date_range_clause(date_from, date_to, params)

    total_sql = "SELECT COALESCE(SUM(amount), 0) AS total, COUNT(*) AS count FROM expenses WHERE user_id = ?"
    total_sql += date_filter

    top_sql = "SELECT category, SUM(amount) AS category_total FROM expenses WHERE user_id = ?"
    top_sql += date_filter
    top_sql += " GROUP BY category ORDER BY category_total DESC LIMIT 1"

    conn = get_db()
    total_row = conn.execute(total_sql, params).fetchone()
    top_row = conn.execute(top_sql, params).fetchone()
    conn.close()

    top_category = top_row["category"] if top_row is not None else "—"

    return {
        "total_spent": _format_currency(total_row["total"]),
        "transaction_count": total_row["count"],
        "top_category": top_category,
    }


# --- Subagent 3: get_category_breakdown --- (only this agent edits below, until next marker)

def get_category_breakdown(user_id, date_from=None, date_to=None):
    sql = "SELECT category, SUM(amount) AS category_total FROM expenses WHERE user_id = ?"
    params = [user_id]

    sql += _date_range_clause(date_from, date_to, params)
    sql += " GROUP BY category ORDER BY category_total DESC"

    conn = get_db()
    rows = conn.execute(sql, params).fetchall()
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
