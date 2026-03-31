import pytest
import pytest_asyncio
import aiosqlite
from httpx import AsyncClient, ASGITransport

import auth
import db
from db import get_db
from main import app


@pytest_asyncio.fixture
async def client():
    """Test client with a fresh in-memory SQLite database per test."""
    conn = await aiosqlite.connect(":memory:")
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA foreign_keys = ON")
    await conn.executescript(db._SCHEMA)
    await db._seed_if_empty(conn)
    await conn.commit()

    async def _override_get_db():
        return conn

    app.dependency_overrides[get_db] = _override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()
    await conn.close()


@pytest_asyncio.fixture
async def auth_client(client):
    """client with a valid Authorization header pre-set."""
    token = auth.create_token("user")
    client.headers["Authorization"] = f"Bearer {token}"
    return client
