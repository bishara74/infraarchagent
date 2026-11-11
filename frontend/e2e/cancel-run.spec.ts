// AI assistance: written with OpenAI Codex from the author's task
// descriptions; reviewed and modified by the author. See AI_USE.md.
import { expect, test } from "@playwright/test";
import { results, submit, USERNAME } from "./support/flow";

test("FR-UI-02 FR-P-04 cancel a run, reload it and start another", async ({ page }) => {
  const id = await submit(page, "Deploy an AWS web service for the Phase 11 cancellation test.");
  const cancel = page.getByRole("button", { name: "Cancel run", exact: true });
  await expect(page.getByTestId("stage-architect")).toHaveText("running");
  await cancel.click();
  const dialog = page.getByRole("dialog", { name: "Stop this run?" });
  await expect(dialog.getByRole("button", { name: "Keep running" })).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(dialog).toBeHidden();
  await expect(cancel).toBeFocused();
  await cancel.click();
  await expect(dialog).toContainText(
    "Packages without a label are discarded; finished packages are kept.",
  );
  await dialog.getByRole("button", { name: "Stop run" }).click();
  await expect(page.getByRole("link", { name: "View results" })).toBeVisible();
  await expect(cancel).toHaveCount(0);
  await expect(page.getByTestId("stage-architect")).toHaveText("cancelled");
  expect((await results(page, id)).run.status).toBe("cancelled");
  await expect(page.getByText(`cancelled by ${USERNAME}`).first()).toBeVisible();
  await page.reload();
  await expect(page.getByTestId("stage-architect")).toHaveText("cancelled");
  await expect(cancel).toHaveCount(0);
  const next = await submit(page);
  expect(next).not.toBe(id);
  await expect(page.getByRole("link", { name: "View results" })).toBeVisible();
});
