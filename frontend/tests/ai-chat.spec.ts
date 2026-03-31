import { expect, test } from "@playwright/test";
import { initialData } from "../src/lib/kanban";

// Mock all API calls — AI chat tests run against the dev server.
test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem("kanban_token", "test-token");
  });
  await page.route("/api/me", (route) =>
    route.fulfill({ status: 200, body: JSON.stringify({ username: "user" }) })
  );
  await page.route("/api/board", (route) =>
    route.fulfill({ status: 200, body: JSON.stringify(initialData) })
  );
  await page.route("/api/cards/**", (route) =>
    route.fulfill({ status: 200, body: JSON.stringify({ ok: true }) })
  );
});

test("AI sidebar opens and closes", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("ai-sidebar")).not.toBeVisible();
  await page.getByRole("button", { name: /open ai chat/i }).click();
  await expect(page.getByTestId("ai-sidebar")).toBeVisible();
  await page.getByRole("button", { name: /dismiss ai chat/i }).click();
  await expect(page.getByTestId("ai-sidebar")).not.toBeVisible();
});

test("sends a message and displays the reply", async ({ page }) => {
  await page.route("/api/ai/chat", (route) =>
    route.fulfill({
      status: 200,
      body: JSON.stringify({ reply: "You have 8 cards.", board_updated: false }),
    })
  );

  await page.goto("/");
  await page.getByRole("button", { name: /open ai chat/i }).click();
  await page.getByRole("textbox", { name: /message/i }).fill("How many cards?");
  await page.getByRole("button", { name: /send message/i }).click();

  await expect(page.getByText("You have 8 cards.")).toBeVisible();
});

test("refreshes board when board_updated is true", async ({ page }) => {
  let boardCallCount = 0;
  await page.unroute("/api/board");
  await page.route("/api/board", (route) => {
    boardCallCount++;
    route.fulfill({ status: 200, body: JSON.stringify(initialData) });
  });

  await page.route("/api/ai/chat", (route) =>
    route.fulfill({
      status: 200,
      body: JSON.stringify({ reply: "Added a card.", board_updated: true }),
    })
  );

  await page.goto("/");
  await page.getByRole("button", { name: /open ai chat/i }).click();
  await page.getByRole("textbox", { name: /message/i }).fill("Add a card");
  await page.getByRole("button", { name: /send message/i }).click();

  await expect(page.getByText("Added a card.")).toBeVisible();
  // Board should have been fetched at least twice: initial load + after AI update
  expect(boardCallCount).toBeGreaterThanOrEqual(2);
});
