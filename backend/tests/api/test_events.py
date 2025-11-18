"""Tests for Events API endpoints."""
import pytest
from fastapi import status


@pytest.mark.api
class TestEventsListEndpoint:
    """Tests for GET /api/events/ endpoint."""

    def test_list_events_success(self, client):
        """Test listing events returns 200 with valid data."""
        response = client.get("/api/events/")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "events" in data
        assert "total" in data
        assert isinstance(data["events"], list)
        assert isinstance(data["total"], int)

    def test_list_events_with_year_filter(self, client):
        """Test filtering events by year."""
        response = client.get("/api/events/?year=2025")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        # All events should be from 2025
        for event in data["events"]:
            if event.get("date"):
                assert event["date"].startswith("2025")

    def test_list_events_with_promotion_filter(self, client):
        """Test filtering events by promotion."""
        response = client.get("/api/events/?promotion=UFC")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        # All events should be UFC events
        for event in data["events"]:
            if event.get("promotion"):
                assert event["promotion"].upper() == "UFC"

    def test_list_events_promotion_all(self, client):
        """Test that promotion=all returns all events (regression test for bug fix)."""
        response = client.get("/api/events/?promotion=all&year=2025")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        # Should return events from multiple promotions
        # At minimum, should return events (not empty)
        assert data["total"] > 0

    def test_list_events_with_limit(self, client):
        """Test limiting the number of events returned."""
        response = client.get("/api/events/?limit=5")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert len(data["events"]) <= 5

    def test_list_events_combined_filters(self, client):
        """Test combining multiple filters."""
        response = client.get("/api/events/?year=2024&promotion=UFC&limit=10")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert len(data["events"]) <= 10

        for event in data["events"]:
            if event.get("date"):
                assert event["date"].startswith("2024")
            if event.get("promotion"):
                assert event["promotion"].upper() == "UFC"


@pytest.mark.api
class TestEventDetailEndpoint:
    """Tests for GET /api/events/{id} endpoint."""

    def test_get_event_by_id_success(self, client):
        """Test getting a specific event by ID."""
        # First, get an event ID from the list
        list_response = client.get("/api/events/?limit=1")
        events = list_response.json()["events"]

        if len(events) > 0:
            event_id = events[0]["id"]

            # Get the specific event
            response = client.get(f"/api/events/{event_id}")
            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert data["id"] == event_id
            assert "name" in data
            assert "date" in data

    def test_get_event_with_fights(self, client):
        """Test getting an event includes fights data."""
        list_response = client.get("/api/events/?limit=1")
        events = list_response.json()["events"]

        if len(events) > 0:
            event_id = events[0]["id"]

            response = client.get(f"/api/events/{event_id}")
            data = response.json()

            # Check if fights are included
            if "fights" in data:
                assert isinstance(data["fights"], list)

    def test_get_event_not_found(self, client):
        """Test getting a non-existent event returns 404."""
        response = client.get("/api/events/999999999")
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.api
class TestEventsYearsEndpoint:
    """Tests for GET /api/events/years endpoint."""

    def test_get_available_years(self, client):
        """Test getting list of available years."""
        response = client.get("/api/events/years")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "years" in data
        assert isinstance(data["years"], list)

        # Years should be integers
        for year in data["years"]:
            assert isinstance(year, int)
            assert 1990 <= year <= 2030  # Reasonable range for MMA events

        # Years should be sorted (typically descending)
        if len(data["years"]) > 1:
            # Check if sorted
            assert data["years"] == sorted(data["years"], reverse=True) or \
                   data["years"] == sorted(data["years"])


@pytest.mark.api
class TestUpcomingEventsEndpoint:
    """Tests for GET /api/events/upcoming/next endpoint."""

    def test_get_next_event(self, client):
        """Test getting the next upcoming event."""
        response = client.get("/api/events/upcoming/next")

        # This might return 404 if no upcoming events
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            # API might return a message or actual event data
            if "message" not in data:
                assert "id" in data
                assert "name" in data
                assert "date" in data


@pytest.mark.api
class TestRecentFinishesEndpoint:
    """Tests for GET /api/events/recent-finishes endpoint."""

    def test_get_recent_finishes(self, client):
        """Test getting recent fight finishes."""
        response = client.get("/api/events/recent-finishes")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "finishes" in data
        assert "total" in data
        assert isinstance(data["finishes"], list)

    def test_get_recent_finishes_with_limit(self, client):
        """Test limiting the number of recent finishes."""
        response = client.get("/api/events/recent-finishes?limit=5")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert len(data["finishes"]) <= 5

    def test_get_recent_finishes_with_promotion(self, client):
        """Test filtering recent finishes by promotion."""
        response = client.get("/api/events/recent-finishes?promotion=UFC")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        # All finishes should be from UFC events
        for finish in data["finishes"]:
            # Promotion might be in event or top level
            assert "UFC" in str(finish).upper()


@pytest.mark.integration
class TestEventsDataQuality:
    """Integration tests for data quality and consistency."""

    def test_event_fields_consistency(self, client):
        """Test that all events have consistent required fields."""
        response = client.get("/api/events/?limit=10")
        events = response.json()["events"]

        for event in events:
            # Required fields
            assert "id" in event
            assert "name" in event
            assert isinstance(event["id"], int)
            assert isinstance(event["name"], str)
            assert len(event["name"]) > 0

    def test_event_dates_format(self, client):
        """Test that event dates are in valid format."""
        response = client.get("/api/events/?limit=10")
        events = response.json()["events"]

        for event in events:
            if event.get("date"):
                date_str = event["date"]
                # Should start with YYYY-MM-DD format (might have timestamp)
                # Accept both "2025-01-15" and "2025-01-15 00:00:00.000000"
                assert len(date_str) >= 10
                assert date_str[4] == "-"
                assert date_str[7] == "-"
                # First 10 chars should be valid date
                year = int(date_str[0:4])
                assert 1990 <= year <= 2030

    def test_fights_structure(self, client):
        """Test that event fights have consistent structure."""
        # Get an event with fights
        list_response = client.get("/api/events/?limit=1")
        events = list_response.json()["events"]

        if len(events) > 0:
            event_id = events[0]["id"]
            response = client.get(f"/api/events/{event_id}")
            data = response.json()

            if "fights" in data and len(data["fights"]) > 0:
                fight = data["fights"][0]

                # Check fight structure
                assert "fighter1_name" in fight or "fighter_1_name" in fight
                assert "fighter2_name" in fight or "fighter_2_name" in fight
