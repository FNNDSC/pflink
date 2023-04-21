import pytest
from starlette.testclient import TestClient
import asyncio
from app.main import app


@pytest.fixture(scope="module")
def test_app():
    client = TestClient(app)
    yield client


@pytest.fixture
def loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
