import { render, screen, within, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi, beforeEach } from "vitest";
import { KanbanBoard } from "@/components/KanbanBoard";
import { initialData } from "@/lib/kanban";

vi.mock("@/lib/api", () => ({
  api: {
    getBoard: vi.fn(),
    createCard: vi.fn(),
    updateCard: vi.fn(),
    deleteCard: vi.fn(),
    moveCard: vi.fn(),
    renameColumn: vi.fn(),
  },
}));

import { api } from "@/lib/api";

beforeEach(() => {
  vi.mocked(api.getBoard).mockResolvedValue(structuredClone(initialData));
  vi.mocked(api.createCard).mockResolvedValue({ id: "card-new", title: "New card", details: "Notes" });
  vi.mocked(api.deleteCard).mockResolvedValue(undefined);
  vi.mocked(api.renameColumn).mockResolvedValue({ id: "col-backlog", title: "New Name" });
  vi.mocked(api.moveCard).mockResolvedValue({ ok: true });
});

const waitForBoard = () => screen.findAllByTestId(/column-/i);

describe("KanbanBoard", () => {
  it("renders five columns after loading", async () => {
    render(<KanbanBoard onLogout={vi.fn()} />);
    const columns = await waitForBoard();
    expect(columns).toHaveLength(5);
  });

  it("renames a column", async () => {
    render(<KanbanBoard onLogout={vi.fn()} />);
    const [firstColumn] = await waitForBoard();
    const input = within(firstColumn).getByLabelText("Column title");
    await userEvent.clear(input);
    await userEvent.type(input, "New Name");
    expect(input).toHaveValue("New Name");
  });

  it("adds and removes a card", async () => {
    render(<KanbanBoard onLogout={vi.fn()} />);
    const [firstColumn] = await waitForBoard();

    await userEvent.click(within(firstColumn).getByRole("button", { name: /add a card/i }));
    await userEvent.type(within(firstColumn).getByPlaceholderText(/card title/i), "New card");
    await userEvent.type(within(firstColumn).getByPlaceholderText(/details/i), "Notes");
    await userEvent.click(within(firstColumn).getByRole("button", { name: /add card/i }));

    await waitFor(() =>
      expect(within(firstColumn).getByText("New card")).toBeInTheDocument()
    );

    vi.mocked(api.deleteCard).mockResolvedValue(undefined);
    await userEvent.click(within(firstColumn).getByRole("button", { name: /delete new card/i }));

    await waitFor(() =>
      expect(within(firstColumn).queryByText("New card")).not.toBeInTheDocument()
    );
  });
});
