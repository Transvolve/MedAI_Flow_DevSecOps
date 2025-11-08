# tests/conftest.py
"""Pytest configuration: path bootstrap + TestClient fixture."""
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient

# Add backend directory to Python path (one time)
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.append(str(backend_dir))

from backend.app.main import app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    """Provides a TestClient for calling the FastAPI app in tests."""
    with TestClient(app) as c:
        yield c
