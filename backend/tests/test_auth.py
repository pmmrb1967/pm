import pytest


@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_login_success(client):
    r = await client.post("/api/login", json={"username": "user", "password": "password"})
    assert r.status_code == 200
    assert "token" in r.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    r = await client.post("/api/login", json={"username": "user", "password": "wrong"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_me_valid(auth_client):
    r = await auth_client.get("/api/me")
    assert r.status_code == 200
    assert r.json()["username"] == "user"


@pytest.mark.asyncio
async def test_me_no_token(client):
    r = await client.get("/api/me")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_board_requires_auth(client):
    r = await client.get("/api/board")
    assert r.status_code == 401
