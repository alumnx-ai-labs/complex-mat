import { expect, test, type Page } from "@playwright/test";

import { loginAsAdmin } from "./fixtures";

const COMMENT_PLACEHOLDER = "Type @ to mention an attendee or @<number> to link an Azure DevOps item…";

async function createMeeting(page: Page, title: string): Promise<void> {
  const date = new Date().toISOString().slice(0, 10);
  await page.goto(`/meetings/new?date=${date}`);
  await page.getByLabel("Title").fill(title);
  await page.getByLabel("Time").fill("14:00");
  await page.getByLabel("Agenda / Notes").fill("Discuss E2E coverage.");
  await page.getByRole("button", { name: "Save Meeting" }).click();
  await expect(page).toHaveURL(/\/meetings\/\d+$/);
}

async function createTask(
  page: Page,
  { title, descriptionNotes }: { title: string; descriptionNotes?: string },
): Promise<void> {
  await page.getByRole("button", { name: "+ Create Task" }).click();
  await page.getByLabel("Task Title").fill(title);
  await page.getByLabel("Assignee").selectOption({ label: "John Admin" });
  if (descriptionNotes) {
    await page.getByLabel("Description / Notes").fill(descriptionNotes);
  }
  await page.getByRole("button", { name: "Save" }).click();
  await expect(page.getByText(title, { exact: true })).toBeVisible();
}

async function openTask(page: Page, title: string): Promise<void> {
  await page.locator(".t-title", { hasText: title }).click();
  await expect(page.getByRole("heading", { name: "Task Details" })).toBeVisible({ timeout: 20_000 });
}

// These tests chain several sequential network round-trips (create meeting, create task,
// open task, debounced mention/ADO lookup, post comment) on top of the base test cost, so
// their assertions get more headroom than the suite's simpler single-step specs. The
// per-test timeout itself is left to playwright.config.ts, which already scales it for
// remote/cold-start runs (90s) vs. local (30s) — hardcoding it here would only shrink
// that back down under PLAYWRIGHT_BASE_URL, which is exactly what happened before.
const ASSERTION_TIMEOUT = { timeout: 20_000 };

test.describe("Task comments, mentions, and Azure DevOps references", () => {
  // This file is the most network-round-trip-heavy in the suite (create meeting,
  // create task, open task, debounced mention/ADO lookup, post comment — each a
  // separate request), which makes it the one most exposed to transient
  // contention when 5 workers share one dev-mode backend process (locally) or a
  // free-tier instance (remote). Retries here absorb that noise without masking
  // a real regression: a genuine bug still fails on the 3rd attempt too.
  test.describe.configure({ retries: 2 });

  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  test("Owner can post a comment and @mention an attendee", async ({ page }) => {
    const meetingTitle = `E2E Comments ${Date.now()}`;
    const taskTitle = `Task ${Date.now()}`;
    await createMeeting(page, meetingTitle);
    await createTask(page, { title: taskTitle });
    await openTask(page, taskTitle);

    await expect(page.getByText("No comments yet.")).toBeVisible(ASSERTION_TIMEOUT);

    const commentBox = page.getByPlaceholder(COMMENT_PLACEHOLDER);
    await commentBox.fill("Please review @Joh");

    const suggestion = page.locator(".search-results .opt", { hasText: "John Admin" });
    await expect(suggestion).toBeVisible(ASSERTION_TIMEOUT);
    await suggestion.click();
    await expect(commentBox).toHaveValue("Please review @John ");

    await page.getByRole("button", { name: "Post Comment" }).click();

    const postedComment = page.locator(".comment-item").last();
    await expect(postedComment).toContainText("John Admin", ASSERTION_TIMEOUT);
    await expect(postedComment).toContainText("Please review @John");
    await expect(commentBox).toHaveValue("");
  });

  test("an @<number> reference in a comment links an Azure DevOps item, shown as unavailable when ADO isn't configured", async ({
    page,
  }) => {
    const meetingTitle = `E2E ADO Comment ${Date.now()}`;
    const taskTitle = `Task ${Date.now()}`;
    await createMeeting(page, meetingTitle);
    await createTask(page, { title: taskTitle });
    await openTask(page, taskTitle);

    const commentBox = page.getByPlaceholder(COMMENT_PLACEHOLDER);
    await commentBox.fill("See @1234 for the full spec.");
    await page.getByRole("button", { name: "Post Comment" }).click();

    const postedComment = page.locator(".comment-item").last();
    await expect(postedComment).toContainText("ADO #1234", ASSERTION_TIMEOUT);
    await expect(postedComment).toContainText("(unavailable)");
  });

  test("an @<number> reference in the Task Description is linked as an Azure DevOps item on the task", async ({
    page,
  }) => {
    const meetingTitle = `E2E ADO Description ${Date.now()}`;
    const taskTitle = `Task ${Date.now()}`;
    await createMeeting(page, meetingTitle);
    await createTask(page, { title: taskTitle, descriptionNotes: "Tracked by @5678." });
    await openTask(page, taskTitle);

    await expect(page.getByText("Linked Azure DevOps Items")).toBeVisible(ASSERTION_TIMEOUT);
    const referenceChip = page.locator(".chip", { hasText: "ADO #5678" });
    await expect(referenceChip).toBeVisible();
    await expect(referenceChip).toContainText("(unavailable)");
  });

  test("the comment composer is hidden until a Task exists", async ({ page }) => {
    const meetingTitle = `E2E No Comments ${Date.now()}`;
    await createMeeting(page, meetingTitle);
    await page.getByRole("button", { name: "+ Create Task" }).click();

    await expect(page.getByRole("heading", { name: "Create Task" })).toBeVisible();
    await expect(page.getByPlaceholder(COMMENT_PLACEHOLDER)).not.toBeVisible();
  });
});
