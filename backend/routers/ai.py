import json
from typing import Annotated

import aiosqlite
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from auth import get_username
from db import get_db
from routers.board import _board_response, _get_board_id
from ai import chat

router = APIRouter(prefix="/api/ai")

_SYSTEM_PROMPT_TEMPLATE = """\
You are an assistant for a Kanban board application. You help the user manage their board by answering questions and optionally updating the board.

The user's current board state is:
{board_json}

You must respond with a JSON object that exactly matches this schema:
{{
  "reply": "<string: your message to the user>",
  "board_update": null | <BoardData object with the same structure as the board above>
}}

Rules:
- Always set "reply" to a helpful, concise message.
- Only set "board_update" if the user explicitly asked you to create, move, edit, or delete cards, or rename columns. Otherwise set it to null.
- When providing a "board_update", return the complete board state — all columns and all cards. Do not return a partial update.
- Preserve all existing card IDs and column slugs exactly. When adding a new card, generate a unique ID using the format "card-<random>" (e.g. "card-abc123").
- Column slugs are fixed: col-backlog, col-discovery, col-progress, col-review, col-done. Do not add or remove columns.
- Keep card details concise.
- Respond ONLY with the JSON object. No markdown, no code fences."""


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


async def _apply_board_update(
    db: aiosqlite.Connection, board_id: int, update: dict
) -> None:
    """Replace board state with the AI-provided BoardData."""
    # Rename columns if titles changed
    for col in update.get("columns", []):
        await db.execute(
            "UPDATE columns SET title = ? WHERE board_id = ? AND slug = ?",
            (col["title"], board_id, col["id"]),
        )

    # Resolve slug → column_id map
    async with db.execute(
        "SELECT id, slug FROM columns WHERE board_id = ?", (board_id,)
    ) as cur:
        rows = await cur.fetchall()
    slug_to_id = {row["slug"]: row["id"] for row in rows}

    # Collect current card IDs
    async with db.execute(
        "SELECT c.id FROM cards c JOIN columns col ON col.id = c.column_id WHERE col.board_id = ?",
        (board_id,),
    ) as cur:
        existing_ids = {str(row[0]) for row in await cur.fetchall()}

    new_cards = update.get("cards", {})
    # card keys may be "card-{id}" or plain "{id}"
    new_card_keys = set(new_cards.keys())

    # Delete cards that were removed
    for raw_id in existing_ids:
        card_key = f"card-{raw_id}"
        if card_key not in new_card_keys and raw_id not in new_card_keys:
            await db.execute("DELETE FROM cards WHERE id = ?", (int(raw_id),))

    # Build new column → ordered card list
    col_cards: dict[str, list[str]] = {}
    for col in update.get("columns", []):
        col_cards[col["id"]] = col.get("cardIds", [])

    for col_slug, card_ids in col_cards.items():
        col_id = slug_to_id.get(col_slug)
        if col_id is None:
            continue
        for pos, card_key in enumerate(card_ids):
            raw_id = card_key.removeprefix("card-")
            card_data = new_cards.get(card_key) or new_cards.get(raw_id)
            if card_data is None:
                continue
            if raw_id in existing_ids:
                # Update existing card
                await db.execute(
                    "UPDATE cards SET title = ?, details = ?, column_id = ?, position = ? WHERE id = ?",
                    (card_data["title"], card_data.get("details", ""), col_id, pos, int(raw_id)),
                )
            else:
                # Insert new card (AI-generated ID — store as auto-increment, ignore AI id)
                await db.execute(
                    "INSERT INTO cards (column_id, title, details, position) VALUES (?,?,?,?)",
                    (col_id, card_data["title"], card_data.get("details", ""), pos),
                )

    await db.commit()


@router.post("/chat")
async def ai_chat(
    body: ChatRequest,
    username: Annotated[str, Depends(get_username)],
    db: Annotated[aiosqlite.Connection, Depends(get_db)],
):
    board_id = await _get_board_id(username, db)
    board = await _board_response(db, board_id)

    system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(
        board_json=json.dumps(board, indent=2)
    )

    messages = [{"role": "system", "content": system_prompt}]
    for msg in body.history:
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": body.message})

    raw = await chat(messages)

    # Strip markdown code fences if the model adds them
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        text = text.rsplit("```", 1)[0].strip()

    parsed = json.loads(text)
    reply: str = parsed["reply"]
    board_update = parsed.get("board_update")

    board_updated = False
    if board_update:
        await _apply_board_update(db, board_id, board_update)
        board_updated = True

    return {"reply": reply, "board_updated": board_updated}
