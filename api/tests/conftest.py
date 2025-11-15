"""
Pytest configuration and fixtures.

Provides reusable test fixtures for the entire test suite.
"""

import sys
from pathlib import Path

# Add parent directory to path for funcpipe import
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def sample_csv_data():
    """Sample CSV data for testing."""
    return b"""name,age,salary
Alice,30,50000
Bob,25,45000
Charlie,35,60000
Diana,28,52000"""


@pytest.fixture
def sample_json_data():
    """Sample JSON data for testing."""
    return b"""[
    {"name": "Alice", "age": 30, "salary": 50000},
    {"name": "Bob", "age": 25, "salary": 45000},
    {"name": "Charlie", "age": 35, "salary": 60000},
    {"name": "Diana", "age": 28, "salary": 52000}
]"""


@pytest.fixture
def sample_pipeline_config():
    """Sample pipeline configuration."""
    return {
        "operations": [
            {
                "type": "filter",
                "operation": "greater_than",
                "config": {"field": "age", "value": 27}
            },
            {
                "type": "transform",
                "operation": "capitalize_field",
                "config": {"field": "name"}
            }
        ]
    }
