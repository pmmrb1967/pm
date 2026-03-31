from typing import Annotated

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from auth import get_username
from db import get_db

router = APIRouter(prefix="/api")


# --- dependency helpers ---

async def _get_board_id(username: str, db: aiosqlite.Connection) -> int:
    async with db.execute(
        "SELECT b.id FROM boards b JOIN users u ON u.id = b.user_id WHERE u.username = ?",
        (username,),
    ) as cur:
        row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Board not found")
    return row[0]


# --- response builders ---

async def _board_response(db: aiosqlite.Connection, board_id: int) -> dict:
    async with db.execute(
        "SELECT id, slug, title FROM columns WHERE board_id = ? ORDER BY position",
        (board_id,),
    ) as cur:
        col_rows = await cur.fetchall()

    columns = []
    cards: dict[str, dict] = {}

    for col in col_rows:
        async with db.execute(
            "SELECT id, title, details FROM cards WHERE column_id = ? ORDER BY position",
            (col["id"],),
        ) as cur:
            card_rows = await cur.fetchall()

        card_ids = []
        for card in card_rows:
            card_key = f"card-{card['id']}"
            cards[card_key] = {
                "id": card_key,
                "title": card["title"],
                "details": card["details"],
            }
            card_ids.append(card_key)

        columns.append({
            "id": col["slug"],
            "title": col["title"],
            "cardIds": card_ids,
        })

    return {"columns": columns, "cards": cards}


# --- routes ---

@router.get("/board")
async def get_board(
    username: Annotated[str, Depends(get_username)],
    db: Annotated[aiosqlite.Connection, Depends(get_db)],
):
    board_id = await _get_board_id(username, db)
    return await _board_response(db, board_id)


class CreateCardRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    details: str = Field("", max_length=10_000)
    columnId: str


@router.post("/cards", status_code=201)
async def create_card(
    body: CreateCardRequest,
    username: Annotated[str, Depends(get_username)],
    db: Annotated[aiosqlite.Connection, Depends(get_db)],
):
    board_id = await _get_board_id(username, db)
    async with db.execute(
        "SELECT id FROM columns WHERE board_id = ? AND slug = ?",
        (board_id, body.columnId),
    ) as cur:
        col = await cur.fetchone()
    if not col:
        raise HTTPException(status_code=404, detail="Column not found")

    async with db.execute(
        "SELECT COALESCE(MAX(position) + 1, 0) FROM cards WHERE column_id = ?",
        (col["id"],),
    ) as cur:
        position = (await cur.fetchone())[0]

    await db.execute(
        "INSERT INTO cards (column_id, title, details, position) VALUES (?,?,?,?)",
        (col["id"], body.title, body.details, position),
    )
    await db.commit()
    async with db.execute("SELECT last_insert_rowid()") as cur:
        card_id = (await cur.fetchone())[0]

    return {"id": f"card-{card_id}", "title": body.title, "details": body.details}


class UpdateCardRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    details: str | None = Field(None, max_length=10_000)


@router.patch("/cards/{card_ref}")
async def update_card(
    card_ref: str,
    body: UpdateCardRequest,
    username: Annotated[str, Depends(get_username)],
    db: Annotated[aiosqlite.Connection, Depends(get_db)],
):
    card_id = _parse_card_id(card_ref)
    await _assert_card_owned(db, card_id, username)

    if body.title is not None:
        await db.execute("UPDATE cards SET title = ? WHERE id = ?", (body.title, card_id))
    if body.details is not None:
        await db.execute("UPDATE cards SET details = ? WHERE id = ?", (body.details, card_id))
    await db.commit()

    async with db.execute("SELECT id, title, details FROM cards WHERE id = ?", (card_id,)) as cur:
        row = await cur.fetchone()
    return {"id": f"card-{row['id']}", "title": row["title"], "details": row["details"]}


@router.delete("/cards/{card_ref}", status_code=204)
async def delete_card(
    card_ref: str,
    username: Annotated[str, Depends(get_username)],
    db: Annotated[aiosqlite.Connection, Depends(get_db)],
):
    card_id = _parse_card_id(card_ref)
    col_id, position = await _assert_card_owned(db, card_id, username)

    await db.execute("DELETE FROM cards WHERE id = ?", (card_id,))
    await db.execute(
        "UPDATE cards SET position = position - 1 WHERE column_id = ? AND position > ?",
        (col_id, position),
    )
    await db.commit()


class MoveCardRequest(BaseModel):
    toColumnId: str
    toIndex: int


@router.post("/cards/{card_ref}/move")
async def move_card(
    card_ref: str,
    body: MoveCardRequest,
    username: Annotated[str, Depends(get_username)],
    db: Annotated[aiosqlite.Connection, Depends(get_db)],
):
    card_id = _parse_card_id(card_ref)
    src_col_id, src_pos = await _assert_card_owned(db, card_id, username)

    board_id = await _get_board_id(username, db)
    async with db.execute(
        "SELECT id FROM columns WHERE board_id = ? AND slug = ?",
        (board_id, body.toColumnId),
    ) as cur:
        dst_col = await cur.fetchone()
    if not dst_col:
        raise HTTPException(status_code=404, detail="Target column not found")
    dst_col_id = dst_col["id"]

    async with db.execute(
        "SELECT COUNT(*) FROM cards WHERE column_id = ?", (dst_col_id,)
    ) as cur:
        dst_count = (await cur.fetchone())[0]

    to_index = max(0, min(body.toIndex, dst_count if dst_col_id != src_col_id else dst_count - 1))

    if src_col_id == dst_col_id:
        # Reorder within same column
        if src_pos == to_index:
            return {"ok": True}
        if src_pos < to_index:
            await db.execute(
                "UPDATE cards SET position = position - 1 WHERE column_id = ? AND position > ? AND position <= ? AND id != ?",
                (src_col_id, src_pos, to_index, card_id),
            )
        else:
            await db.execute(
                "UPDATE cards SET position = position + 1 WHERE column_id = ? AND position >= ? AND position < ? AND id != ?",
                (src_col_id, to_index, src_pos, card_id),
            )
        await db.execute("UPDATE cards SET position = ? WHERE id = ?", (to_index, card_id))
    else:
        # Move to different column
        await db.execute(
            "UPDATE cards SET position = position - 1 WHERE column_id = ? AND position > ?",
            (src_col_id, src_pos),
        )
        await db.execute(
            "UPDATE cards SET position = position + 1 WHERE column_id = ? AND position >= ?",
            (dst_col_id, to_index),
        )
        await db.execute(
            "UPDATE cards SET column_id = ?, position = ? WHERE id = ?",
            (dst_col_id, to_index, card_id),
        )

    await db.commit()
    return {"ok": True}


class RenameColumnRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)


@router.patch("/columns/{slug}")
async def rename_column(
    slug: str,
    body: RenameColumnRequest,
    username: Annotated[str, Depends(get_username)],
    db: Annotated[aiosqlite.Connection, Depends(get_db)],
):
    board_id = await _get_board_id(username, db)
    async with db.execute(
        "SELECT id FROM columns WHERE board_id = ? AND slug = ?", (board_id, slug)
    ) as cur:
        col = await cur.fetchone()
    if not col:
        raise HTTPException(status_code=404, detail="Column not found")
    await db.execute("UPDATE columns SET title = ? WHERE id = ?", (body.title, col["id"]))
    await db.commit()
    return {"id": slug, "title": body.title}


# --- helpers ---

def _parse_card_id(card_ref: str) -> int:
    try:
        return int(card_ref.removeprefix("card-"))
    except ValueError:
        raise HTTPException(status_code=404, detail="Card not found")


async def _assert_card_owned(
    db: aiosqlite.Connection, card_id: int, username: str
) -> tuple[int, int]:
    """Return (column_id, position) after confirming the card belongs to this user."""
    async with db.execute(
        """
        SELECT c.id, c.column_id, c.position
        FROM cards c
        JOIN columns col ON col.id = c.column_id
        JOIN boards b ON b.id = col.board_id
        JOIN users u ON u.id = b.user_id
        WHERE c.id = ? AND u.username = ?
        """,
        (card_id, username),
    ) as cur:
        row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Card not found")
    return row["column_id"], row["position"]
