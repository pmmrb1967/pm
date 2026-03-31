This is the FastAPI backend for Kanban Studio.

Entry point: `main.py`
Dependencies: declared in `pyproject.toml`, managed by `uv`

Current routes:
- `GET /` — hello world HTML page
- `GET /api/health` — returns `{"status": "ok"}`

To run locally (without Docker):
  uv run uvicorn main:app --reload
