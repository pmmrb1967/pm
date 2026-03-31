# Code Review — Kanban Studio MVP

**Date:** 2026-03-31
**Reviewer:** Claude Code (automated review)
**Status at review:** Parts 1–10 complete per `docs/PLAN.md`

---

## Summary

The codebase is in solid shape. Architecture is clean, TypeScript is strict throughout, test coverage is good, and the Docker deployment path works end-to-end. No blockers for MVP launch. The actions below are improvements, not fixes to broken things.

Overall grade: **A-**

---

## Actions

Actions are grouped by priority. Each has a clear owner area (frontend/backend/infra) and the specific file(s) to touch.

---

### High Priority

**H1 — Add backend input validation**
File: `backend/routers/board.py`

Card titles, card details, and column titles are stored without length constraints. This risks DB bloat and could produce unrenderable content on the frontend.

Add max-length checks at the Pydantic model layer or at the route handler:
```python
# In your Pydantic request bodies, e.g.:
class CardCreateBody(BaseModel):
    title: str = Field(..., max_length=255)
    details: str = Field("", max_length=10_000)
```
Apply consistently to all create and update routes.

---

**H2 — Fix AI card ID mismatch**
Files: `backend/routers/ai.py`, `docs/AI_PROMPT.md`

The system prompt instructs the AI to generate card IDs (`card-<random>`), but `_apply_board_update()` ignores those IDs and uses the auto-increment from SQLite. This is internally consistent but the prompt is misleading and will confuse future maintainers or prompt tuning.

Two options — pick one:
- **Option A (simpler):** Update `docs/AI_PROMPT.md` and the system prompt string to say "omit `id` for new cards; the server assigns them."
- **Option B:** Parse and honour the AI-provided IDs as a stable reference within a single response (useful if the AI needs to move a card it just created in the same turn).

Option A is sufficient for the current implementation.

---

**H3 — Harden markdown fence stripping in AI response parser**
File: `backend/routers/ai.py`

The current stripping logic:
```python
if text.startswith("```"):
    text = text.split("\n", 1)[-1]
    text = text.rsplit("```", 1)[0].strip()
```
This breaks if the model returns nested code fences or adds a language tag on a separate line, or if there is trailing whitespace before the opening fence. Defensive approach:

```python
import re

def _strip_fences(text: str) -> str:
    text = text.strip()
    match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if match:
        return match.group(1)
    return text
```
Also wrap the `json.loads()` call in a try/except and return a structured error to the frontend rather than a 500.

---

### Medium Priority

**M1 — Add token expiration**
File: `backend/auth.py`

Tokens are stored in a plain dict and never expire. A user who logs in and closes the tab has an indefinitely valid token. For MVP this is low risk (single known user), but it is one line of code to fix.

```python
# Store (username, issued_at) and reject tokens older than N hours
TOKENS: dict[str, tuple[str, float]] = {}
TTL_SECONDS = 8 * 3600

def get_username(token: str = ...) -> str:
    entry = TOKENS.get(token)
    if not entry or (time.time() - entry[1]) > TTL_SECONDS:
        raise HTTPException(status_code=401)
    return entry[0]
```

---

**M2 — Surface API errors visibly to the user**
File: `frontend/src/components/KanbanBoard.tsx`

Optimistic rollback is implemented correctly, but when a write fails (network error, 5xx) the state silently reverts. The user sees their card snap back with no explanation. Add a short error banner or toast on rollback.

A simple approach without a toast library:
```tsx
const [errorMsg, setErrorMsg] = useState<string | null>(null);
// In catch blocks: setErrorMsg("Could not save — changes reverted.")
// Clear after 4s with setTimeout
```

---

**M3 — Document data-persistence limitation for Docker**
File: `README.md` (or add a `docs/DEPLOYMENT.md`)

The SQLite file lives inside the container at `/data/kanban.db`. If the container is removed (`docker rm`), all data is lost. This must be documented prominently before anyone runs this in a shared environment.

The fix is a volume mount — already partially addressed in `scripts/start.sh` but not documented:
```bash
docker run -v kanban_data:/data ...
```

---

**M4 — Validate AI board_update structure before applying**
File: `backend/routers/ai.py`

`_apply_board_update()` assumes the parsed JSON has the expected shape. If the AI returns unexpected keys or wrong types (e.g., `toIndex` as a string), the function will raise an unhandled exception that becomes a 500.

Add a lightweight schema check:
```python
if not isinstance(board_update.get("cards"), list):
    raise ValueError("board_update.cards must be a list")
```
Or use a Pydantic model for `board_update` deserialization, which is cleaner.

---

### Low Priority

**L1 — Wrap `loadBoard` in `useCallback`**
File: `frontend/src/components/KanbanBoard.tsx`

`loadBoard` is defined as a plain async function inside the component and called from a `useEffect`. This causes a new function reference on every render. Wrapping it in `useCallback` is the idiomatic pattern and prevents potential future lint warnings:
```tsx
const loadBoard = useCallback(async () => { ... }, []);
useEffect(() => { loadBoard(); }, [loadBoard]);
```

---

**L2 — Add direct unit tests for `api.ts` and `auth.ts`**
Files: `frontend/src/lib/api.ts`, `frontend/src/lib/auth.ts`

These modules are currently only tested indirectly through component tests. They contain branching logic (token lookup, error propagation) that deserves isolated unit tests. Straight-forward to add — mock `fetch` with `vi.stubGlobal` and assert against each export.

---

**L3 — Accessibility: add ARIA roles to drag-drop regions**
Files: `frontend/src/components/KanbanColumn.tsx`, `KanbanCard.tsx`

dnd-kit injects keyboard listeners automatically, but there are no `aria-label` attributes on the draggable cards or droppable columns. Screen readers will announce the elements as generic `div`s. Minimum fix:
```tsx
<div aria-label={`Card: ${card.title}`} ...>
<div aria-label={`Column: ${column.title}. ${column.cardIds.length} cards`} ...>
```

---

**L4 — AI retry on transient failure**
File: `backend/ai.py`

A single 503 from OpenRouter returns an error to the user. At 60 s timeout the failure mode is already slow. Adding one retry with exponential backoff (e.g., via `tenacity`) would meaningfully improve reliability for flaky network conditions.

---

## Non-actionable Observations

These are recorded for awareness but require no code change:

- **Single-user assumption**: The schema supports multiple users, but all routes assume one. Multi-user migration will require per-user board isolation and a token refresh strategy. Nothing to do now — just keep this in mind when the product evolves.
- **No audit log**: Card moves and edits are not logged. Acceptable for MVP.
- **AI availability**: There is no fallback if OpenRouter is unreachable. The board remains usable; only chat is affected. This is the right trade-off for MVP.
- **`.env` in repo**: The `.gitignore` should ensure `.env` is excluded. Confirm before making the repo public.

---

## Files Reviewed

| Area | Files |
|------|-------|
| Frontend components | `KanbanBoard.tsx`, `KanbanColumn.tsx`, `KanbanCard.tsx`, `KanbanCardPreview.tsx`, `AIChatSidebar.tsx`, `NewCardForm.tsx` |
| Frontend lib | `kanban.ts`, `api.ts`, `auth.ts` |
| Frontend app | `page.tsx`, `layout.tsx`, `globals.css` |
| Frontend tests | `kanban.test.ts`, `KanbanBoard.test.tsx`, `AIChatSidebar.test.tsx`, `login.test.tsx` |
| E2E tests | `kanban.spec.ts`, `auth.spec.ts`, `persistence.spec.ts`, `ai-chat.spec.ts` |
| Backend core | `main.py`, `auth.py`, `db.py`, `ai.py` |
| Backend routers | `board.py`, `ai.py` |
| Backend tests | `conftest.py`, `test_auth.py`, `test_board.py`, `test_ai.py`, `test_ai_chat.py` |
| Config | `next.config.ts`, `tsconfig.json`, `vitest.config.ts`, `playwright.config.ts`, `pyproject.toml`, `Dockerfile` |
| Docs | `PLAN.md`, `DATABASE.md`, `AI_PROMPT.md`, `AGENTS.md`, `CLAUDE.md` |
