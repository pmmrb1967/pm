import os
import aiosqlite

DB_PATH = os.environ.get("DB_PATH", "/data/kanban.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT    NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS boards (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS columns (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    board_id INTEGER NOT NULL REFERENCES boards(id),
    slug     TEXT    NOT NULL,
    title    TEXT    NOT NULL,
    position INTEGER NOT NULL,
    UNIQUE(board_id, slug)
);

CREATE TABLE IF NOT EXISTS cards (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    column_id INTEGER NOT NULL REFERENCES columns(id),
    title     TEXT    NOT NULL,
    details   TEXT    NOT NULL DEFAULT '',
    position  INTEGER NOT NULL
);
"""

_SEED_COLUMNS = [
    ("col-backlog", "Backlog"),
    ("col-discovery", "Discovery"),
    ("col-progress", "In Progress"),
    ("col-review", "Review"),
    ("col-done", "Done"),
]

_SEED_CARDS = [
    ("col-backlog", "Align roadmap themes", "Draft quarterly themes with impact statements and metrics."),
    ("col-backlog", "Gather customer signals", "Review support tags, sales notes, and churn feedback."),
    ("col-discovery", "Prototype analytics view", "Sketch initial dashboard layout and key drill-downs."),
    ("col-progress", "Refine status language", "Standardize column labels and tone across the board."),
    ("col-progress", "Design card layout", "Add hierarchy and spacing for scanning dense lists."),
    ("col-review", "QA micro-interactions", "Verify hover, focus, and loading states."),
    ("col-done", "Ship marketing page", "Final copy approved and asset pack delivered."),
    ("col-done", "Close onboarding sprint", "Document release notes and share internally."),
]


async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA foreign_keys = ON")
    return db


async def init_db(db_path: str = DB_PATH) -> None:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        await db.executescript(_SCHEMA)
        await _seed_if_empty(db)
        await db.commit()


async def _seed_if_empty(db: aiosqlite.Connection) -> None:
    async with db.execute("SELECT COUNT(*) FROM users") as cur:
        row = await cur.fetchone()
        if row[0] > 0:
            return

    await db.execute("INSERT INTO users (username) VALUES (?)", ("user",))
    async with db.execute("SELECT id FROM users WHERE username = ?", ("user",)) as cur:
        user_id = (await cur.fetchone())[0]

    await db.execute("INSERT INTO boards (user_id) VALUES (?)", (user_id,))
    async with db.execute("SELECT id FROM boards WHERE user_id = ?", (user_id,)) as cur:
        board_id = (await cur.fetchone())[0]

    slug_to_col_id: dict[str, int] = {}
    for pos, (slug, title) in enumerate(_SEED_COLUMNS):
        await db.execute(
            "INSERT INTO columns (board_id, slug, title, position) VALUES (?,?,?,?)",
            (board_id, slug, title, pos),
        )
        async with db.execute("SELECT id FROM columns WHERE board_id=? AND slug=?", (board_id, slug)) as cur:
            slug_to_col_id[slug] = (await cur.fetchone())[0]

    col_card_counts: dict[str, int] = {}
    for col_slug, title, details in _SEED_CARDS:
        pos = col_card_counts.get(col_slug, 0)
        col_card_counts[col_slug] = pos + 1
        await db.execute(
            "INSERT INTO cards (column_id, title, details, position) VALUES (?,?,?,?)",
            (slug_to_col_id[col_slug], title, details, pos),
        )
