"""Pytest configuration and fixtures for testing"""
import pytest
import os
import tempfile
from mma_website import create_app, db


@pytest.fixture
def app():
    """Create and configure a test application instance"""
    # Create a temporary database for testing
    db_fd, db_path = tempfile.mkstemp()

    app = create_app('testing')
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False,
        'CACHE_TYPE': 'SimpleCache',
    })

    # Create the database tables
    with app.app_context():
        db.create_all()
        # You can add test data here if needed

    yield app

    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Create a test client for the app"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a test CLI runner for the app"""
    return app.test_cli_runner()


@pytest.fixture
def auth_headers():
    """Mock authentication headers for testing"""
    return {'Authorization': 'Bearer test-token'}
