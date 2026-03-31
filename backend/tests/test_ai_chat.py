import json
import os
import pytest
import httpx
from unittest.mock import AsyncMock, patch

_FAKE_KEY = "sk-test-fake"
_OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def _mock_ai(reply_json: dict):
    """Return a context manager that patches ai.httpx.AsyncClient to return reply_json."""
    raw = json.dumps(reply_json)
    mock_response = httpx.Response(
        200,
        json={"choices": [{"message": {"content": raw}}]},
        request=httpx.Request("POST", _OPENROUTER_URL),
    )

    class _ctx:
        def __enter__(self_inner):
            self_inner.env_patch = patch.dict(os.environ, {"OPENROUTER_API_KEY": _FAKE_KEY})
            self_inner.http_patch = patch("ai.httpx.AsyncClient")
            self_inner.env_patch.start()
            mock_cls = self_inner.http_patch.start()
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_cls.return_value = mock_client
            return self_inner

        def __exit__(self_inner, *args):
            self_inner.http_patch.stop()
            self_inner.env_patch.stop()

    return _ctx()


@pytest.mark.asyncio
async def test_chat_reply_only(auth_client):
    """AI responds with a plain reply and no board update."""
    with _mock_ai({"reply": "You have 8 cards.", "board_update": None}):
        r = await auth_client.post("/api/ai/chat", json={"message": "How many cards do I have?"})

    assert r.status_code == 200
    data = r.json()
    assert data["reply"] == "You have 8 cards."
    assert data["board_updated"] is False


@pytest.mark.asyncio
async def test_chat_requires_auth(client):
    r = await client.post("/api/ai/chat", json={"message": "hello"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_chat_board_update_creates_card(auth_client):
    """AI adds a new card to col-backlog."""
    # First fetch the current board to build the update
    board_r = await auth_client.get("/api/board")
    board = board_r.json()

    # Build board_update with one extra card in backlog
    updated_board = json.loads(json.dumps(board))  # deep copy
    new_card_id = "card-newai1"
    updated_board["cards"][new_card_id] = {
        "id": new_card_id,
        "title": "AI created card",
        "details": "From the AI.",
    }
    updated_board["columns"][0]["cardIds"].append(new_card_id)

    with _mock_ai({"reply": "I added a card.", "board_update": updated_board}):
        r = await auth_client.post(
            "/api/ai/chat",
            json={"message": "Add a card called 'AI created card' to backlog"},
        )

    assert r.status_code == 200
    assert r.json()["board_updated"] is True

    # Verify the card is in the DB
    board2 = (await auth_client.get("/api/board")).json()
    titles = [board2["cards"][cid]["title"] for cid in board2["columns"][0]["cardIds"]]
    assert "AI created card" in titles


@pytest.mark.asyncio
async def test_chat_board_update_moves_card(auth_client):
    """AI moves the first backlog card to done."""
    board_r = await auth_client.get("/api/board")
    board = board_r.json()

    card_id = board["columns"][0]["cardIds"][0]

    updated_board = json.loads(json.dumps(board))
    updated_board["columns"][0]["cardIds"].remove(card_id)
    updated_board["columns"][4]["cardIds"].insert(0, card_id)

    with _mock_ai({"reply": "Moved the card to Done.", "board_update": updated_board}):
        r = await auth_client.post(
            "/api/ai/chat",
            json={"message": "Move the first backlog card to done"},
        )

    assert r.status_code == 200
    assert r.json()["board_updated"] is True

    board2 = (await auth_client.get("/api/board")).json()
    assert card_id not in board2["columns"][0]["cardIds"]
    assert card_id in board2["columns"][4]["cardIds"]


@pytest.mark.asyncio
async def test_chat_with_history(auth_client):
    """Conversation history is forwarded to the AI."""
    captured_messages = []

    async def _mock_chat(messages):
        captured_messages.extend(messages)
        return json.dumps({"reply": "Got it.", "board_update": None})

    with patch.dict(os.environ, {"OPENROUTER_API_KEY": _FAKE_KEY}), \
         patch("routers.ai.chat", side_effect=_mock_chat):
        r = await auth_client.post("/api/ai/chat", json={
            "message": "What about now?",
            "history": [
                {"role": "user", "content": "How many cards?"},
                {"role": "assistant", "content": "You have 8."},
            ],
        })

    assert r.status_code == 200
    roles = [m["role"] for m in captured_messages]
    assert roles == ["system", "user", "assistant", "user"]


@pytest.mark.asyncio
async def test_chat_strips_markdown_fences(auth_client):
    """Model response wrapped in ```json ... ``` is handled correctly."""
    raw_with_fences = '```json\n{"reply": "ok", "board_update": null}\n```'
    mock_response = httpx.Response(
        200,
        json={"choices": [{"message": {"content": raw_with_fences}}]},
        request=httpx.Request("POST", _OPENROUTER_URL),
    )

    with patch.dict(os.environ, {"OPENROUTER_API_KEY": _FAKE_KEY}), \
         patch("ai.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_cls.return_value = mock_client

        r = await auth_client.post("/api/ai/chat", json={"message": "hello"})

    assert r.status_code == 200
    assert r.json()["reply"] == "ok"
