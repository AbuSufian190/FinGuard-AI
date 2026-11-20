"""Pytest fixtures: isolated SQLite DB + TestClient with real model loaded."""
from __future__ import annotations

import os
import tempfile

import pytest

# Point the app at a throwaway SQLite DB BEFORE importing the app.
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"

from fastapi.testclient import TestClient  # noqa: E402

from app.database import init_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _setup_db():
    init_db()
    yield
    try:
        os.unlink(_tmp.name)
    except OSError:
        pass


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def sample_fraud_tx():
    return {
        "step": 100, "type": "TRANSFER", "amount": 181000.0,
        "oldbalanceOrg": 181000.0, "newbalanceOrig": 0.0,
        "oldbalanceDest": 0.0, "newbalanceDest": 0.0,
    }


@pytest.fixture()
def sample_legit_tx():
    return {
        "step": 100, "type": "PAYMENT", "amount": 120.0,
        "oldbalanceOrg": 9000.0, "newbalanceOrig": 8880.0,
        "oldbalanceDest": 500.0, "newbalanceDest": 620.0,
    }
