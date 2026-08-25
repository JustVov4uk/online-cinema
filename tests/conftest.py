import os

import pytest
from fastapi.testclient import TestClient

os.environ["CELERY_TASK_ALWAYS_EAGER"] = "true"
os.environ["EMAIL_ENABLED"] = "false"

from src.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client
