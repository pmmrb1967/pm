# Project Plan

## Part 1: Plan ✅

Enrich this document and get user sign-off. No `frontend/AGENTS.md` needed — `CLAUDE.md` at the root covers the frontend architecture.

---

## Part 2: Scaffolding ✅

Stand up Docker infrastructure with a FastAPI backend that serves a "hello world" HTML page and responds to a test API call. No frontend integration yet.

### Checklist

- [x] Create `backend/` with a minimal FastAPI app (`main.py`)
  - [x] `GET /` returns a static HTML "hello world" page
  - [x] `GET /api/health` returns `{"status": "ok"}`
- [x] Create `backend/pyproject.toml` (managed by `uv`) with FastAPI and uvicorn dependencies
- [x] Create `Dockerfile` at the project root
  - [x] Uses a Python base image
  - [x] Installs dependencies via `uv`
  - [x] Exposes port 8000
  - [x] Starts uvicorn on `0.0.0.0:8000`
- [x] Create `scripts/start.sh` — builds the Docker image and runs the container (port 8000), works on Mac/Linux/PC (Git Bash/WSL)
- [x] Create `scripts/stop.sh` — stops and removes the container
- [x] Verify locally: `scripts/start.sh`, then `curl http://localhost:8000/` returns HTML and `curl http://localhost:8000/api/health` returns JSON

### Success Criteria

- `docker build` completes without errors
- `GET /` returns an HTML page viewable in a browser at `http://localhost:8000`
- `GET /api/health` returns `{"status": "ok"}`
- `scripts/stop.sh` cleanly stops the container

---

## Part 3: Add in Frontend ✅

Statically build the Next.js frontend and serve it from FastAPI. The Kanban board should be accessible at `/`.

### Checklist

- [x] Configure Next.js for static export (`output: 'export'` in `next.config.ts`)
- [x] Update `Dockerfile` to:
  - [x] Install Node.js
  - [x] Run `npm ci && npm run build` in `frontend/`
  - [x] Copy `frontend/out/` into the backend's static files directory
  - [x] FastAPI serves the static export at `/` using `StaticFiles` with `html=True`
- [x] Verify the Kanban board renders correctly at `http://localhost:8000`
- [x] Add a Playwright E2E test (or extend existing) that hits `http://localhost:8000` and confirms the board loads with 5 columns

### Success Criteria

- `http://localhost:8000` serves the Kanban board (not just "hello world")
- Drag-and-drop works in the browser
- E2E test passes against the containerized app

---

## Part 4: Fake User Sign-In ✅

Add a login gate in front of the Kanban board. Hardcoded credentials: `user` / `password`.

### Checklist

- [x] Create a `LoginPage` component with a username/password form
- [x] On submit, POST to `POST /api/login` with `{username, password}`
- [x] Backend `/api/login` validates hardcoded credentials and returns a session token (simple signed JWT or random token stored server-side in memory)
- [x] Frontend stores the token (e.g. `localStorage`) and attaches it to subsequent API requests
- [x] Add a `GET /api/me` endpoint that validates the token and returns the user identity
- [x] Protect `/` — redirect unauthenticated users to `/login`
- [x] Add a "Log out" button that clears the token and redirects to `/login`
- [x] Unit tests: LoginPage renders, form validation, failed login shows error
- [x] E2E tests: login with correct credentials → board shown; login with wrong credentials → error shown; logout → redirected to login

### Success Criteria

- Visiting `/` unauthenticated redirects to `/login`
- Correct credentials (`user` / `password`) → board visible
- Wrong credentials → error message shown, no redirect
- Logout clears session and returns to login page
- All new unit and E2E tests pass

---

## Part 6: Backend API ✅

### Checklist

- [x] Add SQLite setup to the backend (use `aiosqlite` via a dependency in `uv`)
- [x] On startup, create the database and run migrations if the file doesn't exist
- [x] Implement API routes (all require auth token from Part 4):
  - [x] `GET /api/board` — return the user's board as JSON matching the `BoardData` type
  - [x] `POST /api/cards` — create a new card `{title, details, columnId}`
  - [x] `PATCH /api/cards/{id}` — update card title/details
  - [x] `DELETE /api/cards/{id}` — delete a card
  - [x] `POST /api/cards/{id}/move` — move/reorder a card `{toColumnId, toIndex}`
  - [x] `PATCH /api/columns/{id}` — rename a column
- [x] Backend unit tests for each route (test with a temporary in-memory SQLite database)
- [x] Verify all routes work with `curl` or a REST client

---

## Part 5: Database Modeling

Design and document the SQLite schema for the Kanban, then get user sign-off before implementing.

### Checklist

- [ ] Draft schema covering: users, boards, columns, cards (with ordering)
- [ ] Document the schema in `docs/DATABASE.md` including:
  - [ ] Table definitions with column types and constraints
  - [ ] How card ordering is stored (e.g. integer position column vs. linked list)
  - [ ] How the board JSON maps to relational rows
- [ ] Present the schema to the user for approval before proceeding to Part 6

### Success Criteria

- `docs/DATABASE.md` exists with full schema and rationale
- User has explicitly approved the schema

---

## Part 6: Backend API

Implement API routes for reading and mutating the Kanban. The SQLite database is created automatically if it doesn't exist.

### Checklist

- [ ] Add SQLite setup to the backend (use `aiosqlite` or `sqlite3` via a dependency in `uv`)
- [ ] On startup, create the database and run migrations if the file doesn't exist
- [ ] Implement API routes (all require auth token from Part 4):
  - [ ] `GET /api/board` — return the user's board as JSON matching the `BoardData` type
  - [ ] `POST /api/cards` — create a new card `{title, details, columnId}`
  - [ ] `PATCH /api/cards/{id}` — update card title/details
  - [ ] `DELETE /api/cards/{id}` — delete a card
  - [ ] `POST /api/cards/{id}/move` — move/reorder a card `{toColumnId, toIndex}`
  - [ ] `PATCH /api/columns/{id}` — rename a column
- [ ] Backend unit tests for each route (test with a temporary in-memory SQLite database)
- [ ] Verify all routes work with `curl` or a REST client

### Success Criteria

- All routes return correct data and status codes
- Invalid/missing auth token returns 401
- Database file is created automatically on first run
- All backend unit tests pass

---

## Part 7: Frontend + Backend Integration ✅

Wire the frontend to the backend API, replacing all in-memory state with persistent server-side data.

### Checklist

- [x] Replace `initialData` usage in `KanbanBoard` with a `GET /api/board` fetch on load
- [x] Add loading and error states to `KanbanBoard`
- [x] Wire each user action to the corresponding API call:
  - [x] Add card → `POST /api/cards`
  - [x] Delete card → `DELETE /api/cards/{id}`
  - [x] Move/reorder card → `POST /api/cards/{id}/move`
  - [x] Rename column → `PATCH /api/columns/{id}`
- [x] Apply optimistic updates where appropriate; roll back on API error
- [x] E2E tests for the full flow: login → add card → move card → rename column → logout → login again → changes persisted

### Success Criteria

- Board state survives a container restart
- All E2E tests pass against the containerised app
- No in-memory-only state for board data remains in the frontend

---

## Part 8: AI Connectivity ✅

Verify the backend can call OpenRouter successfully before building AI features.

### Checklist

- [x] Add `httpx` (or `openai` SDK) to backend dependencies for HTTP calls
- [x] Read `OPENROUTER_API_KEY` from environment (passed into Docker via `--env-file .env`)
- [x] Implement `POST /api/ai/ping` — sends `{"messages": [{"role": "user", "content": "What is 2+2?"}]}` to OpenRouter and returns the raw response
- [x] Update `scripts/start.sh` to pass the `.env` file to the container
- [x] Manual test: `POST /api/ai/ping` returns a response containing "4"
- [x] Backend unit test: mock the OpenRouter HTTP call and verify the endpoint returns the model's response

### Success Criteria

- `POST /api/ai/ping` returns a valid response from `openai/gpt-oss-120b`
- API key is not hardcoded anywhere — read from environment only
- Backend test passes with a mocked HTTP call

---

## Part 9: AI Board Integration ✅

Extend the AI endpoint to accept the user's question plus board state, and respond with structured output that optionally updates the board.

### Checklist

- [x] Define the structured output schema:
  ```json
  {
    "reply": "string (message shown to user)",
    "board_update": null | { BoardData }
  }
  ```
- [x] Implement `POST /api/ai/chat`:
  - [x] Accepts `{message: string, history: [{role, content}]}`
  - [x] Fetches the user's current board, serialises it to JSON
  - [x] Calls OpenRouter with system prompt (board JSON) + conversation history + user message
  - [x] Uses structured outputs / response format to enforce the schema
  - [x] If `board_update` is non-null, atomically applies the update to the database
  - [x] Returns `{reply, board_updated: bool}`
- [x] Backend unit tests: mock OpenRouter, test reply-only and reply+board-update paths
- [x] Document the system prompt in `docs/AI_PROMPT.md`

### Success Criteria

- `POST /api/ai/chat` returns a `reply` and correctly applies any `board_update`
- All backend tests pass
- System prompt is documented

---

## Part 10: AI Chat Sidebar UI ✅

Add a chat sidebar to the Kanban board that streams AI responses and auto-refreshes the board when the AI makes changes.

### Checklist

- [x] Add a sidebar panel component (`AIChatSidebar`) to the main layout
  - [x] Input field + send button
  - [x] Scrollable message history (user + assistant turns)
  - [x] Disabled/loading state while awaiting response
- [x] On send, call `POST /api/ai/chat` and append the reply to the history
- [x] If `board_updated: true` is returned, re-fetch `GET /api/board` and update the Kanban state
- [x] Sidebar is togglable (show/hide button) so the board can be used full-width
- [x] Style using the existing design system (CSS variables, Tailwind)
- [x] E2E test: send a message that causes a board update (mocked backend), confirm the board reflects the change without a full page reload

### Success Criteria

- Chat sidebar is functional and styled consistently
- Board updates from AI are reflected immediately without a page reload
- All E2E tests pass
- No visual regressions on the Kanban board
