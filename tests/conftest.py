"""Pytest configuration and shared fixtures for Echo tests."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add src to Python path BEFORE imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from main import app  # noqa: E402


@pytest.fixture
def client():
    """FastAPI test client fixture."""
    return TestClient(app)


@pytest.fixture
def sample_campaign_data():
    """Sample campaign data for testing."""
    return {
        "name": "Test Campaign",
        "description": "A test campaign",
        "campaign_schedule": "cron(0 12 * * ? *)",
        "cycle_schedule": "cron(0 0 * * ? *)",
        "max_events": 10,
        "conn_string": "test_connection",
    }
