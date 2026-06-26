import os

import pytest
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("LLM_ENABLED", "false")
os.environ.setdefault("OPENROUTER_API_KEY", "")

from app.main import app  # noqa: E402


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
