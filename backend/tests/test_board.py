import pytest


@pytest.mark.asyncio
async def test_get_board_structure(auth_client):
    r = await auth_client.get("/api/board")
    assert r.status_code == 200
    data = r.json()
    assert len(data["columns"]) == 5
    assert data["columns"][0]["id"] == "col-backlog"
    assert len(data["cards"]) == 8


@pytest.mark.asyncio
async def test_create_card(auth_client):
    r = await auth_client.post("/api/cards", json={
        "title": "New card",
        "details": "Some details",
        "columnId": "col-backlog",
    })
    assert r.status_code == 201
    body = r.json()
    assert body["title"] == "New card"
    assert body["id"].startswith("card-")

    board = (await auth_client.get("/api/board")).json()
    assert body["id"] in board["columns"][0]["cardIds"]


@pytest.mark.asyncio
async def test_create_card_invalid_column(auth_client):
    r = await auth_client.post("/api/cards", json={
        "title": "X", "details": "", "columnId": "col-nonexistent"
    })
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_update_card(auth_client):
    board = (await auth_client.get("/api/board")).json()
    card_id = board["columns"][0]["cardIds"][0]

    r = await auth_client.patch(f"/api/cards/{card_id}", json={"title": "Updated"})
    assert r.status_code == 200
    assert r.json()["title"] == "Updated"


@pytest.mark.asyncio
async def test_delete_card(auth_client):
    board = (await auth_client.get("/api/board")).json()
    card_id = board["columns"][0]["cardIds"][0]

    r = await auth_client.delete(f"/api/cards/{card_id}")
    assert r.status_code == 204

    board2 = (await auth_client.get("/api/board")).json()
    assert card_id not in board2["columns"][0]["cardIds"]
    assert card_id not in board2["cards"]


@pytest.mark.asyncio
async def test_move_card_between_columns(auth_client):
    board = (await auth_client.get("/api/board")).json()
    backlog_cards = board["columns"][0]["cardIds"]
    card_id = backlog_cards[0]

    r = await auth_client.post(f"/api/cards/{card_id}/move", json={
        "toColumnId": "col-done", "toIndex": 0
    })
    assert r.status_code == 200

    board2 = (await auth_client.get("/api/board")).json()
    assert card_id not in board2["columns"][0]["cardIds"]
    assert board2["columns"][4]["cardIds"][0] == card_id


@pytest.mark.asyncio
async def test_move_card_within_column(auth_client):
    board = (await auth_client.get("/api/board")).json()
    backlog_cards = board["columns"][0]["cardIds"]
    assert len(backlog_cards) >= 2
    card_id = backlog_cards[0]

    r = await auth_client.post(f"/api/cards/{card_id}/move", json={
        "toColumnId": "col-backlog", "toIndex": 1
    })
    assert r.status_code == 200

    board2 = (await auth_client.get("/api/board")).json()
    assert board2["columns"][0]["cardIds"][1] == card_id


@pytest.mark.asyncio
async def test_rename_column(auth_client):
    r = await auth_client.patch("/api/columns/col-backlog", json={"title": "Queue"})
    assert r.status_code == 200
    assert r.json()["title"] == "Queue"

    board = (await auth_client.get("/api/board")).json()
    assert board["columns"][0]["title"] == "Queue"


@pytest.mark.asyncio
async def test_rename_column_not_found(auth_client):
    r = await auth_client.patch("/api/columns/col-fake", json={"title": "X"})
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_delete_positions_compact(auth_client):
    """After deleting a card, remaining card positions are contiguous."""
    board = (await auth_client.get("/api/board")).json()
    cards = board["columns"][0]["cardIds"]
    assert len(cards) >= 2
    await auth_client.delete(f"/api/cards/{cards[0]}")

    board2 = (await auth_client.get("/api/board")).json()
    assert board2["columns"][0]["cardIds"] == [cards[1]]
