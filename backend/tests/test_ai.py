import os
import pytest
import httpx
from unittest.mock import AsyncMock, patch

_FAKE_KEY = "sk-test-fake"
_FAKE_REQUEST = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")


@pytest.mark.asyncio
async def test_ai_ping_returns_reply(auth_client):
    mock_response = httpx.Response(
        200,
        json={"choices": [{"message": {"content": "4"}}]},
        request=_FAKE_REQUEST,
    )

    with patch.dict(os.environ, {"OPENROUTER_API_KEY": _FAKE_KEY}), \
         patch("ai.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        r = await auth_client.post("/api/ai/ping")

    assert r.status_code == 200
    assert "4" in r.json()["reply"]


@pytest.mark.asyncio
async def test_ai_ping_requires_auth(client):
    r = await client.post("/api/ai/ping")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_ai_ping_propagates_api_error(auth_client):
    mock_response = httpx.Response(429, json={"error": "rate limited"}, request=_FAKE_REQUEST)

    with patch.dict(os.environ, {"OPENROUTER_API_KEY": _FAKE_KEY}), \
         patch("ai.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        r = await auth_client.post("/api/ai/ping")

    assert r.status_code == 500
