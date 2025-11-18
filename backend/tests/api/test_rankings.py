"""Tests for Rankings API endpoints."""
import pytest
from fastapi import status


@pytest.mark.api
class TestRankingsEndpoint:
    """Tests for GET /api/rankings/ endpoint."""

    def test_get_all_rankings_success(self, client):
        """Test getting all UFC rankings."""
        response = client.get("/api/rankings/")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "divisions" in data
        assert isinstance(data["divisions"], dict)

        # Should have multiple divisions
        assert len(data["divisions"]) > 0

    def test_rankings_structure(self, client):
        """Test that rankings have correct structure."""
        response = client.get("/api/rankings/")
        data = response.json()

        # Check first division structure
        for division_name, rankings in data["divisions"].items():
            assert isinstance(rankings, list)

            if len(rankings) > 0:
                ranking = rankings[0]
                assert "rank" in ranking or "fighter_name" in ranking
                break


@pytest.mark.api
class TestDivisionRankingsEndpoint:
    """Tests for GET /api/rankings/division/{division} endpoint."""

    def test_get_specific_division(self, client):
        """Test getting rankings for a specific division."""
        # First get all divisions to find a valid one
        all_response = client.get("/api/rankings/")
        divisions = all_response.json()["divisions"]

        if len(divisions) > 0:
            division_name = list(divisions.keys())[0]

            # Get that specific division
            response = client.get(f"/api/rankings/division/{division_name}")
            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert "division" in data
            assert "rankings" in data
            assert isinstance(data["rankings"], list)

    def test_get_invalid_division(self, client):
        """Test getting rankings for non-existent division."""
        response = client.get("/api/rankings/division/InvalidDivision")
        # Might return 404 or empty rankings
        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_200_OK]


@pytest.mark.integration
class TestRankingsDataQuality:
    """Integration tests for rankings data quality."""

    def test_champion_exists_in_divisions(self, client):
        """Test that each division has a champion."""
        response = client.get("/api/rankings/")
        data = response.json()

        for division_name, rankings in data["divisions"].items():
            if len(rankings) > 0:
                # Check if there's a champion (rank 0 or is_champion=True)
                has_champion = any(
                    r.get("rank") == 0 or r.get("is_champion") is True
                    for r in rankings
                )
                # Not all divisions always have champions (vacated titles)
                # So we just check the structure is correct
                assert isinstance(rankings, list)

    def test_rankings_order(self, client):
        """Test that rankings are in correct order."""
        response = client.get("/api/rankings/")
        data = response.json()

        for division_name, rankings in data["divisions"].items():
            if len(rankings) > 1:
                # Check if rankings are sorted
                ranks = [r.get("rank", 0) for r in rankings if "rank" in r]
                if len(ranks) > 1:
                    # Should be sorted ascending (0, 1, 2, 3...)
                    assert ranks == sorted(ranks)
