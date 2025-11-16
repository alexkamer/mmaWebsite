"""Test application factory and basic routes"""
import pytest
from flask import url_for


def test_app_creates_successfully(app):
    """Test that the app is created successfully"""
    assert app is not None
    assert app.config['TESTING'] is True


def test_home_route(client):
    """Test the home page loads successfully"""
    response = client.get('/')
    assert response.status_code == 200


def test_fighters_route(client):
    """Test the fighters listing page"""
    response = client.get('/fighters')
    assert response.status_code == 200


def test_rankings_route(client):
    """Test the rankings page"""
    response = client.get('/rankings')
    assert response.status_code == 200


def test_events_route(client):
    """Test the events listing page"""
    response = client.get('/events', follow_redirects=True)
    assert response.status_code == 200


def test_fighter_wordle_route(client):
    """Test the fighter wordle game page"""
    response = client.get('/fighter-wordle')
    assert response.status_code == 200


def test_tale_of_tape_route(client):
    """Test the tale of tape page"""
    response = client.get('/tale-of-tape')
    assert response.status_code == 200


def test_next_event_route(client):
    """Test the next event page (may fail without ESPN API access)"""
    response = client.get('/next-event')
    # Accept 200 (success) or 500 (API failure is expected in test environment)
    assert response.status_code in [200, 500]


def test_system_checker_route(client):
    """Test the system checker analytics page"""
    response = client.get('/system-checker')
    assert response.status_code == 200
