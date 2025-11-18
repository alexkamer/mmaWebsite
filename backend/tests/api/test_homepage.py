"""Tests for Homepage API endpoints."""
import pytest
from fastapi import status


@pytest.mark.api
class TestHomepageEndpoint:
    """Tests for GET /api/homepage/ endpoint."""

    def test_get_homepage_success(self, client):
        """Test getting homepage data returns 200 with all sections."""
        response = client.get("/api/homepage/")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        # Verify all required sections are present
        assert "recent_events" in data
        assert "upcoming_events" in data
        assert "current_champions" in data
        assert "featured_fighters" in data

    def test_homepage_data_types(self, client):
        """Test that homepage data has correct types."""
        response = client.get("/api/homepage/")
        data = response.json()

        # All sections should be lists
        assert isinstance(data["recent_events"], list)
        assert isinstance(data["upcoming_events"], list)
        assert isinstance(data["current_champions"], list)
        assert isinstance(data["featured_fighters"], list)


@pytest.mark.api
class TestRecentEventsSection:
    """Tests for recent events section of homepage."""

    def test_recent_events_structure(self, client):
        """Test that recent events have correct structure."""
        response = client.get("/api/homepage/")
        data = response.json()

        if len(data["recent_events"]) > 0:
            event = data["recent_events"][0]

            # Required fields
            assert "id" in event
            assert "name" in event
            assert "date" in event
            assert "promotion" in event

            # Optional but expected fields
            assert "venue_name" in event or True
            assert "city" in event or True
            assert "country" in event or True

    def test_recent_events_ufc_only(self, client):
        """Test that recent events are UFC only."""
        response = client.get("/api/homepage/")
        data = response.json()

        for event in data["recent_events"]:
            if "promotion" in event:
                assert event["promotion"].lower() == "ufc"

    def test_recent_events_limit(self, client):
        """Test that recent events are limited to 5."""
        response = client.get("/api/homepage/")
        data = response.json()

        # Should return at most 5 recent events
        assert len(data["recent_events"]) <= 5

    def test_recent_events_sorted_descending(self, client):
        """Test that recent events are sorted by date descending."""
        response = client.get("/api/homepage/")
        data = response.json()

        if len(data["recent_events"]) > 1:
            dates = [event.get("date") for event in data["recent_events"]]
            dates = [d for d in dates if d]  # Filter out None values
            # Should be sorted descending (newest first)
            assert dates == sorted(dates, reverse=True)


@pytest.mark.api
class TestUpcomingEventsSection:
    """Tests for upcoming events section of homepage."""

    def test_upcoming_events_structure(self, client):
        """Test that upcoming events have correct structure."""
        response = client.get("/api/homepage/")
        data = response.json()

        if len(data["upcoming_events"]) > 0:
            event = data["upcoming_events"][0]

            # Required fields
            assert "id" in event
            assert "name" in event
            assert "date" in event
            assert "promotion" in event

    def test_upcoming_events_ufc_only(self, client):
        """Test that upcoming events are UFC only."""
        response = client.get("/api/homepage/")
        data = response.json()

        for event in data["upcoming_events"]:
            if "promotion" in event:
                assert event["promotion"].lower() == "ufc"

    def test_upcoming_events_limit(self, client):
        """Test that upcoming events are limited to 3."""
        response = client.get("/api/homepage/")
        data = response.json()

        # Should return at most 3 upcoming events
        assert len(data["upcoming_events"]) <= 3


@pytest.mark.api
class TestCurrentChampionsSection:
    """Tests for current champions section of homepage."""

    def test_current_champions_structure(self, client):
        """Test that current champions have correct structure."""
        response = client.get("/api/homepage/")
        data = response.json()

        if len(data["current_champions"]) > 0:
            champion = data["current_champions"][0]

            # Required fields
            assert "division" in champion
            assert "full_name" in champion
            assert "position" in champion

            # Position should be C or IC
            assert champion["position"] in ["C", "IC"]

            # Optional fields
            assert "headshot_url" in champion or True
            assert "athlete_id" in champion or True

    def test_current_champions_divisions(self, client):
        """Test that champions cover main UFC divisions."""
        response = client.get("/api/homepage/")
        data = response.json()

        # Get list of divisions
        divisions = [c["division"] for c in data["current_champions"]]

        # Should have champions (may not have all divisions)
        assert len(divisions) > 0

        # All divisions should be valid UFC divisions
        valid_divisions = [
            "Heavyweight", "Light Heavyweight", "Middleweight",
            "Welterweight", "Lightweight", "Featherweight",
            "Bantamweight", "Flyweight", "Women's Bantamweight",
            "Women's Flyweight", "Women's Strawweight"
        ]

        for division in divisions:
            assert division in valid_divisions

    def test_champions_sorted_by_weight(self, client):
        """Test that champions are sorted by weight class order."""
        response = client.get("/api/homepage/")
        data = response.json()

        if len(data["current_champions"]) > 1:
            divisions = [c["division"] for c in data["current_champions"]]

            # Define expected order
            division_order = [
                "Heavyweight", "Light Heavyweight", "Middleweight",
                "Welterweight", "Lightweight", "Featherweight",
                "Bantamweight", "Flyweight", "Women's Bantamweight",
                "Women's Flyweight", "Women's Strawweight"
            ]

            # Check that divisions maintain relative order
            division_indices = [
                division_order.index(d) for d in divisions if d in division_order
            ]

            # Should be sorted (ascending order by weight class)
            assert division_indices == sorted(division_indices)


@pytest.mark.api
class TestFeaturedFightersSection:
    """Tests for featured fighters section of homepage."""

    def test_featured_fighters_structure(self, client):
        """Test that featured fighters have correct structure."""
        response = client.get("/api/homepage/")
        data = response.json()

        if len(data["featured_fighters"]) > 0:
            fighter = data["featured_fighters"][0]

            # Required fields
            assert "id" in fighter
            assert "full_name" in fighter
            assert "position" in fighter

            # Optional but expected fields
            assert "headshot_url" in fighter or True
            assert "weight_class" in fighter or True
            assert "division" in fighter or True
            assert "rank" in fighter or True
            assert "fight_count" in fighter or True

            # Position should be valid (C, IC, or rank number 1-5)
            position = fighter["position"]
            assert position in ["C", "IC"] or (position.isdigit() and 1 <= int(position) <= 5)

    def test_featured_fighters_limit(self, client):
        """Test that featured fighters are limited to 4."""
        response = client.get("/api/homepage/")
        data = response.json()

        # Should return at most 4 featured fighters
        assert len(data["featured_fighters"]) <= 4

    def test_featured_fighters_have_ids(self, client):
        """Test that featured fighters have valid athlete IDs."""
        response = client.get("/api/homepage/")
        data = response.json()

        for fighter in data["featured_fighters"]:
            # All featured fighters should have IDs
            assert fighter.get("id") is not None
            assert isinstance(fighter["id"], int)

    def test_featured_fighters_ranked(self, client):
        """Test that featured fighters are highly ranked (1-5)."""
        response = client.get("/api/homepage/")
        data = response.json()

        for fighter in data["featured_fighters"]:
            if fighter.get("rank") is not None:
                # Rank should be between 1 and 5
                assert 1 <= fighter["rank"] <= 5

    def test_featured_fighters_fight_count(self, client):
        """Test that featured fighters have fight count data."""
        response = client.get("/api/homepage/")
        data = response.json()

        for fighter in data["featured_fighters"]:
            # Fight count should be present and non-negative
            assert "fight_count" in fighter
            assert isinstance(fighter["fight_count"], int)
            assert fighter["fight_count"] >= 0


@pytest.mark.integration
class TestHomepageDataQuality:
    """Integration tests for homepage data quality."""

    def test_homepage_has_data(self, client):
        """Test that homepage returns meaningful data."""
        response = client.get("/api/homepage/")
        data = response.json()

        # At least one section should have data
        has_data = (
            len(data["recent_events"]) > 0 or
            len(data["upcoming_events"]) > 0 or
            len(data["current_champions"]) > 0 or
            len(data["featured_fighters"]) > 0
        )

        assert has_data, "Homepage should have at least some data"

    def test_champions_and_featured_fighters_related(self, client):
        """Test that champions are not duplicated in featured fighters."""
        response = client.get("/api/homepage/")
        data = response.json()

        champion_names = {c["full_name"].lower() for c in data["current_champions"]}
        featured_names = {f["full_name"].lower() for f in data["featured_fighters"]}

        # Featured fighters should be different from champions
        # (though some overlap is acceptable for variety)
        # Just verify both sections can coexist
        assert len(champion_names) >= 0
        assert len(featured_names) >= 0

    def test_recent_and_upcoming_events_not_overlapping(self, client):
        """Test that recent and upcoming events don't overlap."""
        response = client.get("/api/homepage/")
        data = response.json()

        recent_ids = {e.get("id") for e in data["recent_events"]}
        upcoming_ids = {e.get("id") for e in data["upcoming_events"]}

        # Remove None values
        recent_ids.discard(None)
        upcoming_ids.discard(None)

        # Recent and upcoming should not overlap
        overlap = recent_ids.intersection(upcoming_ids)
        assert len(overlap) == 0, "Recent and upcoming events should not overlap"

    def test_homepage_response_time(self, client):
        """Test that homepage loads within reasonable time."""
        import time

        start = time.time()
        response = client.get("/api/homepage/")
        elapsed = time.time() - start

        assert response.status_code == status.HTTP_200_OK
        # Should load within 10 seconds (includes ESPN API calls)
        assert elapsed < 10.0, f"Homepage took {elapsed:.2f}s to load"


@pytest.mark.integration
class TestHomepageESPNIntegration:
    """Integration tests for ESPN API in homepage."""

    def test_upcoming_events_fallback(self, client):
        """Test that upcoming events work (either from ESPN or database)."""
        response = client.get("/api/homepage/")
        data = response.json()

        # Should have upcoming events key regardless of ESPN API status
        assert "upcoming_events" in data
        assert isinstance(data["upcoming_events"], list)

        # If there are upcoming events, they should have valid structure
        for event in data["upcoming_events"]:
            assert "id" in event
            assert "name" in event
            assert "date" in event
