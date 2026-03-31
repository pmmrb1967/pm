import { expect, test } from "@playwright/test";

// Helper: log in and return the page ready at the board.
async function loginAndGoToBoard(page: import("@playwright/test").Page) {
  await page.goto("/login");
  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("password");
  await page.getByRole("button", { name: /sign in/i }).click();
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);
}

test("card added in one session is visible after re-login", async ({ page, context }) => {
  await loginAndGoToBoard(page);

  const firstColumn = page.locator('[data-testid^="column-"]').first();
  await firstColumn.getByRole("button", { name: /add a card/i }).click();
  const cardTitle = `persist-${Date.now()}`;
  await firstColumn.getByPlaceholder("Card title").fill(cardTitle);
  await firstColumn.getByPlaceholder("Details").fill("Persisted card");
  await firstColumn.getByRole("button", { name: /add card/i }).click();
  await expect(firstColumn.getByText(cardTitle)).toBeVisible();

  // Log out
  await page.getByRole("button", { name: /log out/i }).click();
  await expect(page).toHaveURL(/\/login/);

  // Log back in using a fresh page (clear localStorage)
  const page2 = await context.newPage();
  await loginAndGoToBoard(page2);
  await expect(page2.locator('[data-testid^="column-"]').first().getByText(cardTitle)).toBeVisible();
});

test("column rename persists across sessions", async ({ page, context }) => {
  await loginAndGoToBoard(page);

  const newTitle = `col-${Date.now()}`;
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  const input = firstColumn.getByLabel("Column title");
  await input.fill(newTitle);
  await input.press("Tab"); // trigger blur/save

  await page.getByRole("button", { name: /log out/i }).click();
  await expect(page).toHaveURL(/\/login/);

  const page2 = await context.newPage();
  await loginAndGoToBoard(page2);
  await expect(page2.locator('[data-testid^="column-"]').first().getByLabel("Column title")).toHaveValue(newTitle);
});
