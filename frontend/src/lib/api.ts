import { getToken } from "@/lib/auth";
import type { BoardData } from "@/lib/kanban";

function authHeaders(): HeadersInit {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${getToken() ?? ""}`,
  };
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const res = await fetch(path, {
    method,
    headers: authHeaders(),
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`${method} ${path} → ${res.status}`);
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  getBoard: (): Promise<BoardData> => request("GET", "/api/board"),

  createCard: (columnId: string, title: string, details: string) =>
    request<{ id: string; title: string; details: string }>("POST", "/api/cards", {
      columnId,
      title,
      details,
    }),

  updateCard: (cardId: string, patch: { title?: string; details?: string }) =>
    request<{ id: string; title: string; details: string }>("PATCH", `/api/cards/${cardId}`, patch),

  deleteCard: (cardId: string) => request<void>("DELETE", `/api/cards/${cardId}`),

  moveCard: (cardId: string, toColumnId: string, toIndex: number) =>
    request<{ ok: boolean }>("POST", `/api/cards/${cardId}/move`, { toColumnId, toIndex }),

  renameColumn: (columnId: string, title: string) =>
    request<{ id: string; title: string }>("PATCH", `/api/columns/${columnId}`, { title }),
};
