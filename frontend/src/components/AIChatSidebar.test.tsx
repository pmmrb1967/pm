import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi, beforeEach } from "vitest";
import { AIChatSidebar } from "@/components/AIChatSidebar";

vi.mock("@/lib/api", () => ({
  api: {
    chat: vi.fn(),
  },
}));

import { api } from "@/lib/api";

const onBoardUpdate = vi.fn();

function openSidebar() {
  return userEvent.click(screen.getByRole("button", { name: /open ai chat/i }));
}

beforeEach(() => {
  vi.mocked(api.chat).mockResolvedValue({ reply: "Got it.", board_updated: false });
  onBoardUpdate.mockClear();
});

describe("AIChatSidebar", () => {
  it("is hidden by default, opens on toggle", async () => {
    render(<AIChatSidebar onBoardUpdate={onBoardUpdate} />);
    expect(screen.queryByTestId("ai-sidebar")).not.toBeInTheDocument();
    await openSidebar();
    expect(screen.getByTestId("ai-sidebar")).toBeInTheDocument();
  });

  it("sends a message and shows the reply", async () => {
    render(<AIChatSidebar onBoardUpdate={onBoardUpdate} />);
    await openSidebar();

    await userEvent.type(screen.getByRole("textbox", { name: /message/i }), "Hello");
    await userEvent.click(screen.getByRole("button", { name: /send message/i }));

    await waitFor(() => expect(screen.getByText("Got it.")).toBeInTheDocument());
    expect(screen.getByText("Hello")).toBeInTheDocument();
  });

  it("calls onBoardUpdate when board_updated is true", async () => {
    vi.mocked(api.chat).mockResolvedValue({ reply: "Done.", board_updated: true });
    render(<AIChatSidebar onBoardUpdate={onBoardUpdate} />);
    await openSidebar();

    await userEvent.type(screen.getByRole("textbox", { name: /message/i }), "Add a card");
    await userEvent.click(screen.getByRole("button", { name: /send message/i }));

    await waitFor(() => expect(onBoardUpdate).toHaveBeenCalledOnce());
  });

  it("shows error message on API failure", async () => {
    vi.mocked(api.chat).mockRejectedValue(new Error("network error"));
    render(<AIChatSidebar onBoardUpdate={onBoardUpdate} />);
    await openSidebar();

    await userEvent.type(screen.getByRole("textbox", { name: /message/i }), "Hello");
    await userEvent.click(screen.getByRole("button", { name: /send message/i }));

    await waitFor(() =>
      expect(screen.getByText(/failed to reach/i)).toBeInTheDocument()
    );
  });

  it("closes on close button click", async () => {
    render(<AIChatSidebar onBoardUpdate={onBoardUpdate} />);
    await openSidebar();
    expect(screen.getByTestId("ai-sidebar")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /dismiss/i }));
    expect(screen.queryByTestId("ai-sidebar")).not.toBeInTheDocument();
  });
});
