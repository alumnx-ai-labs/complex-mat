import { expect, test, type Page } from "@playwright/test";

import { loginAsAdmin } from "./fixtures";

/**
 * User Story 6 (spec.md lines 107-121) covers three notification triggers:
 * task assignment (FR-034), comment-posted (FR-035), and @mention (FR-036) — all
 * required to complete even if email delivery fails (FR-038).
 *
 * Only the task-assignment path is actually wired up in the backend today
 * (backend/app/api/tasks.py -> notification_service.notify_task_assigned,
 * scheduled via FastAPI BackgroundTasks so it can never block the request).
 * Comment-posted and @mention notifications (FR-035/FR-036) have no
 * implementation yet (tasks.md T032 marks this "partial" and comments.py has
 * no notification wiring), and there is no notifications UI in the frontend
 * to assert against either way. Email delivery itself can't be observed from
 * the browser: SMTP is unconfigured in this e2e environment (backend/.env
 * SMTP_HOST is blank), so EmailSender.send() is a no-op that only logs.
 *
 * What IS observable and worth locking down end-to-end: assigning a Task
 * completes promptly and successfully regardless of the (no-op) notification
 * attempt riding along on a BackgroundTask — i.e. FR-038's "never blocks the
 * underlying operation" guarantee, as experienced through the UI.
 */

async function createMeeting(page: Page, title: string): Promise<void> {
  const date = new Date().toISOString().slice(0, 10);
  await page.goto(`/meetings/new?date=${date}`);
  await page.getByLabel("Title").fill(title);
  await page.getByLabel("Time").fill("14:00");
  await page.getByLabel("Agenda / Notes").fill("Discuss E2E coverage.");
  await page.getByRole("button", { name: "Save Meeting" }).click();
  await expect(page).toHaveURL(/\/meetings\/\d+$/);
}

test.describe("Task assignment notifications (User Story 6)", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  test("assigning a Task on creation succeeds promptly and is not blocked by the notification email", async ({
    page,
  }) => {
    const meetingTitle = `E2E Assignment Notify ${Date.now()}`;
    const taskTitle = `Task ${Date.now()}`;
    await createMeeting(page, meetingTitle);

    await page.getByRole("button", { name: "+ Create Task" }).click();
    await page.getByLabel("Task Title").fill(taskTitle);
    await page.getByLabel("Assignee").selectOption({ label: "John Admin" });

    // Time only the actual network round-trip (request sent -> response
    // received), not the click that triggers it: with launchOptions.slowMo
    // configured (see playwright.config.ts / PW_SLOWMO), Playwright inserts a
    // real delay into every simulated action, which would otherwise get
    // counted against this budget and has nothing to do with what FR-038
    // guarantees.
    let requestSentAt = 0;
    page.on("request", (request) => {
      if (/\/api\/meetings\/\d+\/tasks$/.test(request.url()) && request.method() === "POST") {
        requestSentAt = Date.now();
      }
    });
    const createTaskResponse = page.waitForResponse(
      (response) =>
        /\/api\/meetings\/\d+\/tasks$/.test(response.url()) && response.request().method() === "POST",
    );
    await page.getByRole("button", { name: "Save" }).click();

    const response = await createTaskResponse;
    const elapsedMs = Date.now() - requestSentAt;

    expect(response.ok()).toBe(true);
    // FastAPI's BackgroundTasks run only after the response is sent, so a
    // fast response here demonstrates the (no-op) notification attempt isn't
    // holding up task creation — the FR-038 guarantee, observed via the API.
    // Generous ceiling: this only needs to catch a genuine synchronous block
    // (e.g. a slow SMTP call inline on the request), not fluctuate with
    // ordinary network/cold-start latency.
    expect(elapsedMs).toBeLessThan(15_000);

    await expect(page.getByText(taskTitle, { exact: true })).toBeVisible();
  });

  // A genuine *reassignment* (PATCH with a changed assignee_id, which is the other
  // trigger for notify_task_assigned per backend/app/api/tasks.py) can't be exercised
  // here: this environment seeds only one user (the Admin), who is the only option in
  // the Assignee dropdown, so there's no second attendee to reassign to. See
  // e2e-test-scenarios.md, "Known gaps".
});
