# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Kanban Studio — a single-board Kanban project management app. The frontend MVP is complete. The backend (FastAPI + SQLite + AI chat) is in progress. Everything will be packaged into a Docker container.

Review `docs/PLAN.md` before starting any implementation work — it contains the detailed roadmap.

## Commands

All commands run from the `frontend/` directory.

```bash
npm run dev              # Start dev server
npm run build            # Production build
npm run lint             # ESLint
npm run test             # Unit tests (Vitest)
npm run test:unit:watch  # Unit tests in watch mode
npm run test:e2e         # E2E tests (Playwright, requires dev server)
npm run test:all         # All tests
```

Run a single unit test file:
```bash
npx vitest run src/lib/kanban.test.ts
```

## Architecture

**Stack**: Next.js 16 (React 19, TypeScript strict) · Tailwind CSS v4 · dnd-kit · Vitest · Playwright
**Planned backend**: Python FastAPI (served at `/`), SQLite, OpenRouter AI (`openai/gpt-oss-120b`), Docker

**Data model** (`frontend/src/lib/kanban.ts`):
```typescript
type Card = { id: string; title: string; details: string }
type Column = { id: string; title: string; cardIds: string[] }
type BoardData = { columns: Column[]; cards: Record<string, Card> }
```
Cards are stored in a flat lookup map; columns hold ordered arrays of card IDs. `moveCard()` handles both reordering within a column and moving between columns. IDs are generated via `createId()` (prefix + random + timestamp).

**Component tree**:
```
layout.tsx → page.tsx → KanbanBoard (owns all state + DndContext)
  └── KanbanColumn (SortableContext droppable)
        ├── KanbanCard (draggable)
        └── NewCardForm
```
`KanbanCardPreview` renders the drag overlay via `DragOverlay`.

**Path alias**: `@/*` maps to `frontend/src/*`.

## Color Scheme

| Token | Hex | Use |
|-------|-----|-----|
| Accent Yellow | `#ecad0a` | highlights, column borders on hover |
| Blue Primary | `#209dd7` | links, key sections |
| Purple Secondary | `#753991` | submit buttons, important actions |
| Dark Navy | `#032147` | main headings |
| Gray Text | `#888888` | labels, supporting text |

Colors are defined as CSS variables in `frontend/src/app/globals.css` and consumed via Tailwind.

## Coding Standards

- Use latest idiomatic versions of all libraries.
- Keep it simple — no over-engineering, no unnecessary defensive programming, no extra features.
- Be concise. No emojis anywhere.
- Always identify root cause before fixing an issue. Prove with evidence, then fix.
- Backend uses `uv` as the Python package manager.
- AI calls go through OpenRouter; the `OPENROUTER_API_KEY` is in `.env` at the project root.
