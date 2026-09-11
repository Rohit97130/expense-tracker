# NOTE: The original spec draft stated expected totals of ₹346.24 with top
# category "Bills". Those figures do not match the actual seed data defined
# in database/db.py::seed_db() (8 expenses summing to ₹5,594.50, top category
# Shopping at ₹2,200.00). This test file asserts against the real seeded
# values, per user decision.

from database.queries import (
    get_category_breakdown,
    get_recent_transactions,
    get_summary_stats,
    get_user_by_id,
)


class TestGetRecentTransactions:
    def test_returns_transactions_newest_first(self, demo_user_id):
        txns = get_recent_transactions(demo_user_id, limit=10)
        assert len(txns) == 8
        dates = [t["date"] for t in txns]
        assert dates == sorted(dates, reverse=True)

    def test_amount_is_formatted_currency_string(self, demo_user_id):
        txns = get_recent_transactions(demo_user_id)
        assert all(t["amount"].startswith("₹") for t in txns)

    def test_respects_limit(self, demo_user_id):
        txns = get_recent_transactions(demo_user_id, limit=3)
        assert len(txns) == 3

    def test_zero_expense_user_returns_empty_list(self, empty_user_id):
        assert get_recent_transactions(empty_user_id) == []


class TestGetSummaryStats:
    def test_total_and_count_match_seed_data(self, demo_user_id):
        stats = get_summary_stats(demo_user_id)
        assert stats["total_spent"] == "₹5,594.50"
        assert stats["transaction_count"] == 8
        assert stats["top_category"] == "Shopping"

    def test_zero_expense_user_has_zero_total_no_crash(self, empty_user_id):
        stats = get_summary_stats(empty_user_id)
        assert stats["total_spent"] == "₹0.00"
        assert stats["transaction_count"] == 0
        assert stats["top_category"] == "—"


class TestGetCategoryBreakdown:
    def test_percentages_sum_to_100(self, demo_user_id):
        breakdown = get_category_breakdown(demo_user_id)
        assert sum(c["pct"] for c in breakdown) == 100

    def test_top_category_is_shopping(self, demo_user_id):
        breakdown = get_category_breakdown(demo_user_id)
        assert breakdown[0]["name"] == "Shopping"
        assert breakdown[0]["amount"] == "₹2,200.00"

    def test_zero_expense_user_returns_empty_list(self, empty_user_id):
        assert get_category_breakdown(empty_user_id) == []


class TestGetUserById:
    def test_returns_name_email_member_since(self, demo_user_id):
        user = get_user_by_id(demo_user_id)
        assert user["email"] == "demo@spendly.com"
        assert user["name"] == "Demo User"
        assert user["member_since"]


class TestProfileRoute:
    def test_profile_requires_login(self, client):
        resp = client.get("/profile")
        assert resp.status_code == 302

    def test_profile_renders_real_data_for_logged_in_user(self, client, demo_user_id):
        with client.session_transaction() as sess:
            sess["user_id"] = demo_user_id
            sess["user_name"] = "Demo User"
        resp = client.get("/profile")
        assert resp.status_code == 200
        assert "₹5,594.50".encode("utf-8") in resp.data
        assert b"Shopping" in resp.data
