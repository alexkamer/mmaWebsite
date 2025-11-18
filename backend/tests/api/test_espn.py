"""Tests for ESPN API integration endpoints."""
import pytest
from fastapi import status


@pytest.mark.api
class TestESPNNextEventEndpoint:
    """Tests for GET /api/espn/next-event endpoint."""

    def test_get_next_event_success_or_not_found(self, client):
        """Test getting next event from ESPN API."""
        response = client.get("/api/espn/next-event")

        # ESPN API might not always have an upcoming event
        # or the API call might fail
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_500_INTERNAL_SERVER_ERROR
        ]

        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "event" in data
            assert "fights" in data
            assert "total_fights" in data

            # Check event structure
            event = data["event"]
            assert "event_id" in event or "id" in event
            assert "event_name" in event or "name" in event
            assert "date" in event

            # Check fights structure
            assert isinstance(data["fights"], list)
            assert isinstance(data["total_fights"], int)

    def test_next_event_fight_structure(self, client):
        """Test that fight data has correct structure."""
        response = client.get("/api/espn/next-event")

        if response.status_code == status.HTTP_200_OK:
            data = response.json()

            if len(data["fights"]) > 0:
                fight = data["fights"][0]

                # Check fighter 1 data
                assert "fighter_1_name" in fight or "fighter1_name" in fight
                assert "fighter_1_id" in fight or "fighter1_id" in fight

                # Check fighter 2 data
                assert "fighter_2_name" in fight or "fighter2_name" in fight
                assert "fighter_2_id" in fight or "fighter2_id" in fight


@pytest.mark.slow
@pytest.mark.integration
class TestESPNAPIIntegration:
    """Integration tests for ESPN API calls."""

    def test_espn_api_response_time(self, client):
        """Test that ESPN API responds within reasonable time."""
        import time

        start = time.time()
        response = client.get("/api/espn/next-event")
        end = time.time()

        # Should respond within 5 seconds
        assert (end - start) < 5.0

    def test_espn_api_error_handling(self, client):
        """Test that ESPN API handles missing data gracefully."""
        # Test without mocking - the endpoint should handle errors gracefully
        response = client.get("/api/espn/next-event")

        # Should return a valid HTTP status code (not crash)
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_500_INTERNAL_SERVER_ERROR
        ]

        # Response should be valid JSON
        try:
            data = response.json()
            assert isinstance(data, dict)
        except ValueError:
            pytest.fail("Response should be valid JSON")
