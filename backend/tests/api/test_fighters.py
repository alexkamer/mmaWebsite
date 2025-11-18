"""Tests for Fighters API endpoints."""
import pytest
from fastapi import status


@pytest.mark.api
class TestFightersListEndpoint:
    """Tests for GET /api/fighters/ endpoint."""

    def test_list_fighters_success(self, client):
        """Test listing fighters returns 200 with valid data."""
        response = client.get("/api/fighters/")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "fighters" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert isinstance(data["fighters"], list)
        assert isinstance(data["total"], int)

    def test_list_fighters_pagination(self, client):
        """Test pagination parameters work correctly."""
        response = client.get("/api/fighters/?page=1&page_size=10")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 10
        assert len(data["fighters"]) <= 10

    def test_list_fighters_search(self, client):
        """Test search parameter filters fighters."""
        response = client.get("/api/fighters/?search=connor")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        # Results should contain fighters matching the search term
        if data["total"] > 0:
            fighter_names = [f["name"].lower() for f in data["fighters"]]
            assert any("connor" in name for name in fighter_names)

    def test_list_fighters_weight_class_filter(self, client):
        """Test weight class filter."""
        response = client.get("/api/fighters/?weight_class=Welterweight")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        # All returned fighters should be from Welterweight division
        for fighter in data["fighters"]:
            if fighter.get("weight_class"):
                assert "Welterweight" in fighter["weight_class"]

    def test_list_fighters_starts_with_filter(self, client):
        """Test starts_with filter for alphabet navigation."""
        response = client.get("/api/fighters/?starts_with=A")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        # All returned fighters should have names starting with 'A'
        for fighter in data["fighters"]:
            assert fighter["name"][0].upper() == "A"

    def test_list_fighters_invalid_page(self, client):
        """Test invalid page number."""
        response = client.get("/api/fighters/?page=99999")
        assert response.status_code == status.HTTP_200_OK
        # Should return empty results or handle gracefully
        data = response.json()
        assert "fighters" in data


@pytest.mark.api
class TestFighterDetailEndpoint:
    """Tests for GET /api/fighters/{id} endpoint."""

    def test_get_fighter_by_id_success(self, client):
        """Test getting a specific fighter by ID."""
        # First, get a fighter ID from the list
        list_response = client.get("/api/fighters/?page_size=1")
        fighters = list_response.json()["fighters"]

        if len(fighters) > 0:
            fighter_id = fighters[0]["id"]

            # Get the specific fighter
            response = client.get(f"/api/fighters/{fighter_id}")
            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert data["id"] == fighter_id
            assert "name" in data
            assert "weight_class" in data

    def test_get_fighter_not_found(self, client):
        """Test getting a non-existent fighter returns 404."""
        response = client.get("/api/fighters/999999999")
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.api
class TestFighterFiltersEndpoint:
    """Tests for GET /api/fighters/filters endpoint."""

    def test_get_filters(self, client):
        """Test getting available filter options."""
        response = client.get("/api/fighters/filters")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "weight_classes" in data
        assert "nationalities" in data
        assert isinstance(data["weight_classes"], list)
        assert isinstance(data["nationalities"], list)


@pytest.mark.api
class TestFighterFightsEndpoint:
    """Tests for GET /api/fighters/{id}/fights endpoint."""

    def test_get_fighter_fights(self, client):
        """Test getting fights for a specific fighter."""
        # Get a fighter with fights
        list_response = client.get("/api/fighters/?page_size=1")
        fighters = list_response.json()["fighters"]

        if len(fighters) > 0:
            fighter_id = fighters[0]["id"]

            response = client.get(f"/api/fighters/{fighter_id}/fights")
            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert "fights" in data
            assert isinstance(data["fights"], list)

    def test_get_fighter_fights_with_limit(self, client):
        """Test limiting the number of fights returned."""
        list_response = client.get("/api/fighters/?page_size=1")
        fighters = list_response.json()["fighters"]

        if len(fighters) > 0:
            fighter_id = fighters[0]["id"]

            response = client.get(f"/api/fighters/{fighter_id}/fights?limit=5")
            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert len(data["fights"]) <= 5


@pytest.mark.api
class TestFighterCompareEndpoint:
    """Tests for GET /api/fighters/compare/{id1}/{id2} endpoint."""

    def test_compare_fighters_success(self, client):
        """Test comparing two fighters."""
        # Get two fighters
        list_response = client.get("/api/fighters/?page_size=2")
        fighters = list_response.json()["fighters"]

        if len(fighters) >= 2:
            fighter1_id = fighters[0]["id"]
            fighter2_id = fighters[1]["id"]

            response = client.get(f"/api/fighters/compare/{fighter1_id}/{fighter2_id}")
            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert "fighter1" in data
            assert "fighter2" in data
            assert "head_to_head" in data
            assert data["fighter1"]["id"] == fighter1_id
            assert data["fighter2"]["id"] == fighter2_id

    def test_compare_same_fighter(self, client):
        """Test comparing a fighter with themselves."""
        list_response = client.get("/api/fighters/?page_size=1")
        fighters = list_response.json()["fighters"]

        if len(fighters) > 0:
            fighter_id = fighters[0]["id"]

            # This might return an error or handle it gracefully
            response = client.get(f"/api/fighters/compare/{fighter_id}/{fighter_id}")
            # Accept 400 (bad request), 404 (not found), or 200 (handles gracefully)
            assert response.status_code in [
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_404_NOT_FOUND,
                status.HTTP_200_OK
            ]

    def test_compare_invalid_fighters(self, client):
        """Test comparing with non-existent fighter IDs."""
        response = client.get("/api/fighters/compare/999999/999998")
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.integration
class TestFightersDataQuality:
    """Integration tests for data quality and consistency."""

    def test_fighter_fields_consistency(self, client):
        """Test that all fighters have consistent required fields."""
        response = client.get("/api/fighters/?page_size=10")
        fighters = response.json()["fighters"]

        for fighter in fighters:
            # Required fields
            assert "id" in fighter
            assert "name" in fighter
            assert isinstance(fighter["id"], int)
            assert isinstance(fighter["name"], str)
            assert len(fighter["name"]) > 0

    def test_pagination_consistency(self, client):
        """Test that pagination is consistent across pages."""
        page1_response = client.get("/api/fighters/?page=1&page_size=10")
        page1_data = page1_response.json()

        page2_response = client.get("/api/fighters/?page=2&page_size=10")
        page2_data = page2_response.json()

        # Total should be the same across pages
        assert page1_data["total"] == page2_data["total"]

        # Fighters should be different
        page1_ids = {f["id"] for f in page1_data["fighters"]}
        page2_ids = {f["id"] for f in page2_data["fighters"]}

        # No overlap if we have enough fighters
        if page1_data["total"] >= 20:
            assert page1_ids.isdisjoint(page2_ids)
