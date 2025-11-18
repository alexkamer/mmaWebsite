"""Pytest configuration and fixtures for backend tests."""
import pytest
from fastapi.testclient import TestClient

from backend.api.main import app


@pytest.fixture(scope="module")
def client():
    """Create a test client for API endpoint testing."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
def sample_fighter():
    """Sample fighter data for testing."""
    return {
        "id": 1,
        "name": "Test Fighter",
        "nickname": "The Tester",
        "weight_class": "Welterweight",
        "nationality": "USA",
        "wins": 10,
        "losses": 2,
        "draws": 0,
        "height": "6'0\"",
        "weight": "170 lbs",
        "reach": "74\"",
        "stance": "Orthodox"
    }


@pytest.fixture(scope="function")
def sample_event():
    """Sample event data for testing."""
    return {
        "id": 1,
        "name": "UFC 300: Test Event",
        "date": "2025-12-31",
        "location": "Las Vegas, Nevada",
        "promotion": "UFC"
    }


@pytest.fixture(scope="function")
def sample_ranking():
    """Sample ranking data for testing."""
    return {
        "rank": 1,
        "fighter_id": 1,
        "fighter_name": "Test Fighter",
        "division": "Welterweight",
        "is_champion": True,
        "is_interim": False
    }
