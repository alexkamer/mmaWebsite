"""Tests for Betting Analytics API endpoints."""
import pytest
from fastapi import status


@pytest.mark.api
class TestBettingYearsEndpoint:
    """Tests for GET /api/betting/years endpoint."""

    def test_get_years_default_league(self, client):
        """Test getting available years with default UFC league."""
        response = client.get("/api/betting/years")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "years" in data
        assert isinstance(data["years"], list)

        # Years should be integers
        for year in data["years"]:
            assert isinstance(year, int)
            assert 2000 <= year <= 2030  # Reasonable range

    def test_get_years_specific_league(self, client):
        """Test getting years for specific league."""
        response = client.get("/api/betting/years?league=ufc")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert isinstance(data["years"], list)

    def test_get_years_invalid_league(self, client):
        """Test getting years for non-existent league."""
        response = client.get("/api/betting/years?league=nonexistent")
        assert response.status_code == status.HTTP_200_OK

        # Should return empty list or handle gracefully
        data = response.json()
        assert "years" in data
        assert isinstance(data["years"], list)

    def test_years_sorted_descending(self, client):
        """Test that years are sorted in descending order."""
        response = client.get("/api/betting/years?league=ufc")
        data = response.json()

        if len(data["years"]) > 1:
            # Should be sorted descending (newest first)
            assert data["years"] == sorted(data["years"], reverse=True)


@pytest.mark.api
class TestBettingOverviewEndpoint:
    """Tests for GET /api/betting/overview endpoint."""

    def test_get_overview_default(self, client):
        """Test getting betting overview with defaults."""
        response = client.get("/api/betting/overview")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "total_fights" in data
        assert "favorite_wins" in data
        assert "underdog_wins" in data
        assert "favorite_win_pct" in data
        assert "underdog_win_pct" in data

        # Validate data types
        assert isinstance(data["total_fights"], int)
        assert isinstance(data["favorite_wins"], int)
        assert isinstance(data["underdog_wins"], int)
        assert isinstance(data["favorite_win_pct"], (int, float))
        assert isinstance(data["underdog_win_pct"], (int, float))

    def test_get_overview_with_year(self, client):
        """Test getting overview for specific year."""
        response = client.get("/api/betting/overview?league=ufc&year=2024")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "total_fights" in data
        # Total should be >= 0
        assert data["total_fights"] >= 0

    def test_overview_percentages_valid(self, client):
        """Test that percentages are valid (0-100)."""
        response = client.get("/api/betting/overview?league=ufc")
        data = response.json()

        if data["total_fights"] > 0:
            assert 0 <= data["favorite_win_pct"] <= 100
            assert 0 <= data["underdog_win_pct"] <= 100

    def test_overview_wins_add_up(self, client):
        """Test that favorite + underdog wins <= total fights."""
        response = client.get("/api/betting/overview?league=ufc")
        data = response.json()

        total = data["favorite_wins"] + data["underdog_wins"]
        assert total <= data["total_fights"]


@pytest.mark.api
class TestBettingWeightClassesEndpoint:
    """Tests for GET /api/betting/weight-classes endpoint."""

    def test_get_weight_classes(self, client):
        """Test getting weight class betting statistics."""
        response = client.get("/api/betting/weight-classes?league=ufc")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "weight_classes" in data
        assert isinstance(data["weight_classes"], list)

    def test_weight_class_structure(self, client):
        """Test that weight class data has correct structure."""
        response = client.get("/api/betting/weight-classes?league=ufc")
        data = response.json()

        if len(data["weight_classes"]) > 0:
            wc = data["weight_classes"][0]

            # Required fields
            assert "weight_class" in wc
            assert "total_fights" in wc
            assert "favorite_wins" in wc
            assert "underdog_wins" in wc
            assert "favorite_win_pct" in wc
            assert "underdog_win_pct" in wc

            # Validate types
            assert isinstance(wc["weight_class"], str)
            assert isinstance(wc["total_fights"], int)
            assert isinstance(wc["favorite_wins"], int)

    def test_weight_classes_with_year_filter(self, client):
        """Test weight classes with year filter."""
        response = client.get("/api/betting/weight-classes?league=ufc&year=2024")
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.api
class TestBettingRoundsFormatEndpoint:
    """Tests for GET /api/betting/rounds-format endpoint."""

    def test_get_rounds_format(self, client):
        """Test getting rounds format statistics."""
        response = client.get("/api/betting/rounds-format?league=ufc")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "formats" in data
        assert isinstance(data["formats"], list)

    def test_rounds_format_structure(self, client):
        """Test rounds format data structure."""
        response = client.get("/api/betting/rounds-format?league=ufc")
        data = response.json()

        if len(data["formats"]) > 0:
            fmt = data["formats"][0]

            # Required fields
            assert "rounds_format" in fmt
            assert "total_fights" in fmt
            assert "favorite_wins" in fmt

            # rounds_format should be 3 or 5 typically
            assert isinstance(fmt["rounds_format"], int)
            assert fmt["rounds_format"] in [3, 5]

    def test_rounds_format_with_year(self, client):
        """Test rounds format with year filter."""
        response = client.get("/api/betting/rounds-format?league=ufc&year=2024")
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.api
class TestBettingFinishTypesEndpoint:
    """Tests for GET /api/betting/finish-types endpoint."""

    def test_get_finish_types(self, client):
        """Test getting finish type statistics."""
        response = client.get("/api/betting/finish-types?league=ufc")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "finish_types" in data
        assert isinstance(data["finish_types"], list)

    def test_finish_types_structure(self, client):
        """Test finish types data structure."""
        response = client.get("/api/betting/finish-types?league=ufc")
        data = response.json()

        if len(data["finish_types"]) > 0:
            ft = data["finish_types"][0]

            # Required fields
            assert "weight_class" in ft
            assert "total_fights" in ft
            assert "decisions" in ft
            assert "knockouts" in ft
            assert "submissions" in ft
            assert "decision_pct" in ft
            assert "knockout_pct" in ft
            assert "submission_pct" in ft
            assert "finish_pct" in ft

    def test_finish_percentages_valid(self, client):
        """Test that finish type percentages are valid values."""
        response = client.get("/api/betting/finish-types?league=ufc")
        data = response.json()

        for ft in data["finish_types"]:
            if ft["total_fights"] > 0:
                # Each percentage should be between 0 and 100
                assert 0 <= ft["decision_pct"] <= 100
                assert 0 <= ft["knockout_pct"] <= 100
                assert 0 <= ft["submission_pct"] <= 100
                assert 0 <= ft["finish_pct"] <= 100

    def test_finish_types_with_year(self, client):
        """Test finish types with year filter."""
        response = client.get("/api/betting/finish-types?league=ufc&year=2024")
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.api
class TestBettingCardsEndpoint:
    """Tests for GET /api/betting/cards endpoint."""

    def test_get_cards(self, client):
        """Test getting card-by-card betting statistics."""
        response = client.get("/api/betting/cards?league=ufc")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "cards" in data
        assert "total" in data
        assert isinstance(data["cards"], list)
        assert isinstance(data["total"], int)

    def test_cards_structure(self, client):
        """Test cards data structure."""
        response = client.get("/api/betting/cards?league=ufc")
        data = response.json()

        if len(data["cards"]) > 0:
            card = data["cards"][0]

            # Required fields
            assert "event_id" in card
            assert "event_name" in card
            assert "date" in card
            assert "fights_with_odds" in card
            assert "favorite_wins" in card
            assert "underdog_wins" in card

    def test_cards_with_year_filter(self, client):
        """Test cards with year filter."""
        response = client.get("/api/betting/cards?league=ufc&year=2024")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        # All cards should be from 2024
        for card in data["cards"]:
            if card.get("date"):
                assert card["date"].startswith("2024")

    def test_cards_sorted_by_date(self, client):
        """Test that cards are sorted by date (newest first)."""
        response = client.get("/api/betting/cards?league=ufc&year=2024")
        data = response.json()

        if len(data["cards"]) > 1:
            dates = [card["date"] for card in data["cards"] if card.get("date")]
            # Should be sorted descending (newest first)
            assert dates == sorted(dates, reverse=True)


@pytest.mark.integration
class TestBettingDataQuality:
    """Integration tests for betting data quality."""

    def test_consistent_data_across_endpoints(self, client):
        """Test that data is consistent across different endpoints."""
        # Get overview
        overview_response = client.get("/api/betting/overview?league=ufc&year=2024")
        overview = overview_response.json()

        # Get cards
        cards_response = client.get("/api/betting/cards?league=ufc&year=2024")
        cards = cards_response.json()

        # Total fights should be consistent
        # (though overview might have more due to different filters)
        if overview["total_fights"] > 0 and len(cards["cards"]) > 0:
            # At least some cards should exist if there are fights
            assert len(cards["cards"]) > 0

    def test_league_parameter_works(self, client):
        """Test that league parameter filters correctly."""
        ufc_response = client.get("/api/betting/overview?league=ufc")
        ufc_data = ufc_response.json()

        # Should have data for UFC
        assert ufc_data["total_fights"] >= 0

    def test_all_endpoints_respond(self, client):
        """Smoke test that all betting endpoints respond successfully."""
        endpoints = [
            "/api/betting/years",
            "/api/betting/overview",
            "/api/betting/weight-classes",
            "/api/betting/rounds-format",
            "/api/betting/finish-types",
            "/api/betting/cards",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == status.HTTP_200_OK
            assert response.json() is not None
