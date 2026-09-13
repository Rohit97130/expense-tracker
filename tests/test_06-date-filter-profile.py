# Tests for Step 6: Date Filter for Profile Page
#
# These tests are derived purely from .claude/specs/06-date-filter-profile.md.
# They exercise the real (non-mocked) SQLite DB via the seed data created by
# database/db.py::seed_db(), following the pattern already established in
# tests/test_backend_connection.py and tests/conftest.py. Login is simulated
# via client.session_transaction() rather than a real /login POST, matching
# existing test conventions in this repo.
#
# Seed data recap (see database/db.py::seed_db(), for reference only):
#   demo_user_id has 8 expenses spanning from today-1 to today-12 days.
#   empty_user_id has zero expenses.
# Because seed dates are relative to "today", we compute expected date
# windows dynamically using datetime.date, matching the spec's rules for
# "This Month" / "Last 3 Months" / "Last 6 Months" / "All Time".

from datetime import date, timedelta

from flask import url_for


def _month_start(d):
    return d.replace(day=1)


def _months_ago(d, months):
    month_index = d.month - 1 - months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, 1)


def _login(client, user_id, name="Demo User"):
    with client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["user_name"] = name


class TestProfileAuthGuard:
    """Auth guard: unauthenticated requests redirect to login regardless of query params."""

    def test_no_params_redirects_when_logged_out(self, client):
        resp = client.get("/profile")
        assert resp.status_code == 302

    def test_with_preset_params_redirects_when_logged_out(self, client):
        resp = client.get("/profile?date_from=2026-01-01&date_to=2026-01-31")
        assert resp.status_code == 302

    def test_with_malformed_params_redirects_when_logged_out(self, client):
        resp = client.get("/profile?date_from=not-a-date&date_to=also-not-a-date")
        assert resp.status_code == 302


class TestProfileUnfilteredHappyPath:
    """GET /profile with no query params must behave exactly like Step 5 (unfiltered)."""

    def test_no_query_params_returns_full_unfiltered_data(self, client, demo_user_id):
        _login(client, demo_user_id)
        resp = client.get("/profile")
        assert resp.status_code == 200
        # Same totals as the unfiltered Step 5 behaviour (all 8 seeded expenses).
        assert "₹5,594.50".encode("utf-8") in resp.data
        assert b"Shopping" in resp.data

    def test_no_query_params_shows_all_eight_transactions(self, client, demo_user_id):
        _login(client, demo_user_id)
        resp = client.get("/profile")
        assert resp.status_code == 200
        html = resp.data.decode("utf-8")
        # 8 seeded descriptions should all be present when unfiltered.
        for desc in [
            "Groceries",
            "Cab fare",
            "Electricity bill",
            "Pharmacy",
            "Movie tickets",
            "New shoes",
            "Misc",
            "Dinner out",
        ]:
            assert desc in html, f"Expected '{desc}' in unfiltered profile page"

    def test_no_query_params_active_preset_is_all_time(self, client, demo_user_id):
        _login(client, demo_user_id)
        resp = client.get("/profile")
        html = resp.data.decode("utf-8")
        assert 'class="filter-preset active">All Time</a>' in html, (
            "Expected 'All Time' preset to be marked active when no filter is applied"
        )


class TestProfilePresets:
    """Each quick-select preset must apply the correct date range to all sections."""

    def test_this_month_filters_to_current_calendar_month(self, client, demo_user_id):
        _login(client, demo_user_id)
        today = date.today()
        month_start = _month_start(today)

        resp = client.get(
            f"/profile?date_from={month_start.isoformat()}&date_to={today.isoformat()}"
        )
        assert resp.status_code == 200
        html = resp.data.decode("utf-8")

        # Expected: only seeded expenses with date >= month_start survive.
        expected_total = 0.0
        expected_descs = []
        seed_expenses = [
            (450.00, today - timedelta(days=1), "Groceries"),
            (120.50, today - timedelta(days=2), "Cab fare"),
            (1500.00, today - timedelta(days=3), "Electricity bill"),
            (600.00, today - timedelta(days=5), "Pharmacy"),
            (350.00, today - timedelta(days=7), "Movie tickets"),
            (2200.00, today - timedelta(days=8), "New shoes"),
            (99.00, today - timedelta(days=10), "Misc"),
            (275.00, today - timedelta(days=12), "Dinner out"),
        ]
        for amt, d, desc in seed_expenses:
            if d >= month_start:
                expected_total += amt
                expected_descs.append(desc)
            else:
                assert desc not in html, (
                    f"'{desc}' dated {d} is outside 'This Month' window "
                    f"({month_start}..{today}) and should not appear"
                )

        for desc in expected_descs:
            assert desc in html, f"Expected '{desc}' within 'This Month' window to appear"

    def test_this_month_preset_marks_active_state(self, client, demo_user_id):
        _login(client, demo_user_id)
        today = date.today()
        month_start = _month_start(today)
        resp = client.get(
            f"/profile?date_from={month_start.isoformat()}&date_to={today.isoformat()}"
        )
        html = resp.data.decode("utf-8")
        assert 'class="filter-preset active">This Month</a>' in html

    def test_last_3_months_filters_to_three_month_window(self, client, demo_user_id):
        _login(client, demo_user_id)
        today = date.today()
        window_start = _months_ago(today, 3)

        resp = client.get(
            f"/profile?date_from={window_start.isoformat()}&date_to={today.isoformat()}"
        )
        assert resp.status_code == 200
        html = resp.data.decode("utf-8")

        # All seeded expenses (max 12 days back) fall within any 3-month window
        # ending today, so all 8 transactions and the full total must appear.
        assert "₹5,594.50".encode("utf-8") in resp.data
        for desc in ["Groceries", "Cab fare", "Electricity bill", "Dinner out"]:
            assert desc in html

    def test_last_3_months_preset_marks_active_state(self, client, demo_user_id):
        _login(client, demo_user_id)
        today = date.today()
        window_start = _months_ago(today, 3)
        resp = client.get(
            f"/profile?date_from={window_start.isoformat()}&date_to={today.isoformat()}"
        )
        html = resp.data.decode("utf-8")
        assert 'class="filter-preset active">Last 3 Months</a>' in html

    def test_last_6_months_filters_to_six_month_window(self, client, demo_user_id):
        _login(client, demo_user_id)
        today = date.today()
        window_start = _months_ago(today, 6)

        resp = client.get(
            f"/profile?date_from={window_start.isoformat()}&date_to={today.isoformat()}"
        )
        assert resp.status_code == 200
        # All seeded expenses fall within any 6-month window ending today.
        assert "₹5,594.50".encode("utf-8") in resp.data

    def test_last_6_months_preset_marks_active_state(self, client, demo_user_id):
        _login(client, demo_user_id)
        today = date.today()
        window_start = _months_ago(today, 6)
        resp = client.get(
            f"/profile?date_from={window_start.isoformat()}&date_to={today.isoformat()}"
        )
        html = resp.data.decode("utf-8")
        assert 'class="filter-preset active">Last 6 Months</a>' in html

    def test_all_time_removes_filter_and_shows_everything(self, client, demo_user_id):
        _login(client, demo_user_id)
        # First apply a narrow filter that would exclude some expenses...
        today = date.today()
        resp = client.get(f"/profile?date_from={today.isoformat()}&date_to={today.isoformat()}")
        assert resp.status_code == 200

        # ...then hit the clean "All Time" URL (no query params) and confirm
        # everything reappears.
        resp = client.get("/profile")
        assert resp.status_code == 200
        assert "₹5,594.50".encode("utf-8") in resp.data
        assert b"Shopping" in resp.data

    def test_all_time_preset_link_has_no_query_params(self, app, client, demo_user_id):
        _login(client, demo_user_id)
        resp = client.get("/profile")
        html = resp.data.decode("utf-8")
        with app.test_request_context():
            all_time_href = url_for("profile")
        assert f'href="{all_time_href}"' in html, (
            "The 'All Time' preset must link to a clean /profile URL with no query params"
        )


class TestProfileCustomRange:
    """Custom date_from/date_to query params filter all three sections."""

    def test_custom_range_filters_summary_transactions_and_categories(self, client, demo_user_id):
        _login(client, demo_user_id)
        today = date.today()

        # Window covering only the "Groceries" (day-1) and "Cab fare" (day-2)
        # expenses: 450.00 + 120.50 = 570.50
        date_from = (today - timedelta(days=2)).isoformat()
        date_to = today.isoformat()

        resp = client.get(f"/profile?date_from={date_from}&date_to={date_to}")
        assert resp.status_code == 200
        html = resp.data.decode("utf-8")

        # Summary stats section
        assert "₹570.50".encode("utf-8") in resp.data
        assert '<span class="profile-stat-value">2</span>' in html, (
            "Expected transaction_count stat card to render '2' for the filtered range"
        )

        # Recent transactions section
        assert "Groceries" in html
        assert "Cab fare" in html
        assert "Electricity bill" not in html
        assert "Dinner out" not in html

        # Category breakdown section — only Food and Transport should appear
        assert "Food" in html
        assert "Transport" in html
        assert "Bills" not in html
        assert "Shopping" not in html

    def test_custom_range_reflected_in_date_inputs(self, client, demo_user_id):
        _login(client, demo_user_id)
        today = date.today()
        date_from = (today - timedelta(days=5)).isoformat()
        date_to = today.isoformat()

        resp = client.get(f"/profile?date_from={date_from}&date_to={date_to}")
        html = resp.data.decode("utf-8")
        assert f'value="{date_from}"' in html
        assert f'value="{date_to}"' in html


class TestProfileValidationErrors:
    """Malformed dates and inverted ranges fall back to unfiltered view without crashing."""

    def test_malformed_date_from_falls_back_to_unfiltered(self, client, demo_user_id):
        _login(client, demo_user_id)
        resp = client.get("/profile?date_from=not-a-date&date_to=2026-01-31")
        assert resp.status_code == 200, "Malformed date must not crash the app"
        # Falls back to unfiltered (all expenses / full total), per spec rule:
        # "on ValueError, treat the param as absent (fall back to no filter)".
        assert "₹5,594.50".encode("utf-8") in resp.data

    def test_malformed_date_to_falls_back_to_unfiltered(self, client, demo_user_id):
        _login(client, demo_user_id)
        resp = client.get("/profile?date_from=2026-01-01&date_to=also-bad")
        assert resp.status_code == 200
        assert "₹5,594.50".encode("utf-8") in resp.data

    def test_both_dates_malformed_falls_back_to_unfiltered(self, client, demo_user_id):
        _login(client, demo_user_id)
        resp = client.get("/profile?date_from=garbage&date_to=garbage2")
        assert resp.status_code == 200
        assert "₹5,594.50".encode("utf-8") in resp.data

    def test_date_from_after_date_to_falls_back_to_unfiltered(self, client, demo_user_id):
        _login(client, demo_user_id)
        today = date.today()
        # Inverted range: date_from is after date_to.
        date_from = today.isoformat()
        date_to = (today - timedelta(days=30)).isoformat()

        resp = client.get(f"/profile?date_from={date_from}&date_to={date_to}")
        assert resp.status_code == 200
        assert "₹5,594.50".encode("utf-8") in resp.data, (
            "date_from > date_to must fall back to the unfiltered (all expenses) view"
        )

    def test_date_from_after_date_to_shows_flash_message(self, client, demo_user_id):
        _login(client, demo_user_id)
        today = date.today()
        date_from = today.isoformat()
        date_to = (today - timedelta(days=30)).isoformat()

        resp = client.get(
            f"/profile?date_from={date_from}&date_to={date_to}", follow_redirects=True
        )
        assert b"Start date must be before end date." in resp.data, (
            "Expected the flash error message to be rendered on the page"
        )

    def test_date_from_after_date_to_active_preset_is_all_time(self, client, demo_user_id):
        _login(client, demo_user_id)
        today = date.today()
        date_from = today.isoformat()
        date_to = (today - timedelta(days=30)).isoformat()

        resp = client.get(f"/profile?date_from={date_from}&date_to={date_to}")
        html = resp.data.decode("utf-8")
        assert 'class="filter-preset active">All Time</a>' in html, (
            "After falling back due to an invalid range, 'All Time' should show as active"
        )


class TestProfileEmptyRangeResult:
    """A date range with zero matching expenses must show empty state with no errors."""

    def test_range_with_no_matching_expenses_shows_zero_totals(self, client, demo_user_id):
        _login(client, demo_user_id)
        # Far future window guaranteed to contain none of the seeded expenses.
        resp = client.get("/profile?date_from=2099-01-01&date_to=2099-01-31")
        assert resp.status_code == 200
        assert "₹0.00".encode("utf-8") in resp.data
        html = resp.data.decode("utf-8")
        # None of the seeded descriptions should appear.
        for desc in ["Groceries", "Cab fare", "Electricity bill", "Pharmacy"]:
            assert desc not in html

    def test_empty_user_with_no_filter_shows_zero_totals_no_errors(self, client, empty_user_id):
        _login(client, empty_user_id, name="Empty User")
        resp = client.get("/profile")
        assert resp.status_code == 200
        assert "₹0.00".encode("utf-8") in resp.data

    def test_empty_user_with_custom_range_shows_zero_totals_no_errors(self, client, empty_user_id):
        _login(client, empty_user_id, name="Empty User")
        resp = client.get("/profile?date_from=2020-01-01&date_to=2020-12-31")
        assert resp.status_code == 200
        assert "₹0.00".encode("utf-8") in resp.data


class TestProfileCurrencyFormatting:
    """All amounts must continue to display the ₹ symbol regardless of active filter."""

    def test_unfiltered_amounts_use_rupee_symbol(self, client, demo_user_id):
        _login(client, demo_user_id)
        resp = client.get("/profile")
        assert "₹".encode("utf-8") in resp.data

    def test_filtered_amounts_use_rupee_symbol(self, client, demo_user_id):
        _login(client, demo_user_id)
        today = date.today()
        resp = client.get(
            f"/profile?date_from={(today - timedelta(days=2)).isoformat()}"
            f"&date_to={today.isoformat()}"
        )
        assert "₹".encode("utf-8") in resp.data

    def test_zero_result_amount_uses_rupee_symbol(self, client, demo_user_id):
        _login(client, demo_user_id)
        resp = client.get("/profile?date_from=2099-01-01&date_to=2099-01-31")
        assert "₹0.00".encode("utf-8") in resp.data
