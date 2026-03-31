# Database Schema

SQLite, created automatically on first run. File path: `/data/kanban.db` inside the container.

---

## Tables

### `users`

```sql
CREATE TABLE users (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT    NOT NULL UNIQUE
);
```

One row per user. MVP seeds a single row for `user`.

---

### `boards`

```sql
CREATE TABLE boards (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id)
);
```

One board per user (enforced by `UNIQUE(user_id)`). MVP creates one board automatically when seeding.

---

### `columns`

```sql
CREATE TABLE columns (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    board_id INTEGER NOT NULL REFERENCES boards(id),
    slug     TEXT    NOT NULL,
    title    TEXT    NOT NULL,
    position INTEGER NOT NULL,
    UNIQUE(board_id, slug)
);
```

- `slug` — stable string identifier matching the frontend convention (`col-backlog`, `col-discovery`, etc.). Used as the column `id` in API responses so the frontend type `Column.id` stays a string.
- `position` — integer, 0-based, determines column order. Columns are fixed for MVP (no add/delete), only renaming is supported.

---

### `cards`

```sql
CREATE TABLE cards (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    column_id INTEGER NOT NULL REFERENCES columns(id),
    title     TEXT    NOT NULL,
    details   TEXT    NOT NULL DEFAULT '',
    position  INTEGER NOT NULL
);
```

- `position` — integer, 0-based within a column. When a card is moved or reordered, positions of affected cards in the target column are updated (shift up/down). At MVP scale (tens of cards) this is trivially fast.
- Card `id` in API responses is formatted as `"card-{id}"` to match the frontend string convention.

---

## Ordering approach

Card ordering uses a simple integer `position` column rather than a linked list.

**Why:** Linked lists avoid mass-updates on reorder but add query complexity (recursive CTEs or application-side traversal). At the expected scale (single user, ~50 cards), an integer position is simpler to implement, simpler to query (`ORDER BY position`), and trivial to update.

**Move semantics:** When card A at position `p_old` in column `src` is moved to position `p_new` in column `dst`:
- Remove A from `src`: decrement `position` of all cards in `src` where `position > p_old`
- Insert A into `dst`: increment `position` of all cards in `dst` where `position >= p_new`, then set A's `position = p_new` and `column_id = dst.id`

---

## Mapping to frontend types

```
users.username          → session identity
boards                  → BoardData (container)
columns.slug + .title   → Column.id + Column.title
columns ordered by position → BoardData.columns[]
cards ordered by position within column → Column.cardIds[]
"card-{cards.id}"       → Card.id
cards.title             → Card.title
cards.details           → Card.details
```

---

## Seed data

On first run, if the database is empty, the backend seeds:

- One user: `username = "user"`
- One board for that user
- Five columns: Backlog, Discovery, In Progress, Review, Done (matching the frontend `initialData`)
- Eight sample cards (same as `initialData`)
