import { expect, test, type Page } from "@playwright/test";

import { loginAsAdmin } from "./fixtures";

/**
 * User Story 8 (spec.md lines 161-175): browse Previous Meetings — each
 * meeting a person is permitted to see is listed with title, date, and
 * task count, and opening one navigates to its full details.
 *
 * This environment seeds only one user — the default Admin, who is Owner
 * and Attendee for every meeting created here — so scenario 2 ("a Team
 * Member not invited to a meeting does not see it in their list") can't be
 * exercised as a real end-to-end check without a second seeded user. It is
 * covered server-side already (test_previous_meetings_workflow.py). This
 * file covers what's genuinely testable with the single seeded Admin:
 * listing title/date/task count, the count updating as tasks change, and
 * navigating from the list into a meeting's details.
 */

async function createMeeting(page: Page, title: string): Promise<number> {
  const date = new Date().toISOString().slice(0, 10);
  await page.goto(`/meetings/new?date=${date}`);
  await page.getByLabel("Title").fill(title);
  await page.getByLabel("Time").fill("14:00");
  await page.getByLabel("Agenda / Notes").fill("Agenda.");
  await page.getByRole("button", { name: "Save Meeting" }).click();
  await expect(page).toHaveURL(/\/meetings\/\d+$/);
  return Number(page.url().match(/\/meetings\/(\d+)$/)?.[1]);
}

function rowFor(page: Page, title: string) {
  return page.getByRole("row").filter({ has: page.getByText(title, { exact: true }) });
}

test.describe("Previous Meetings (User Story 8)", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  test("every meeting is listed with its title, date, meeting owner, and task count", async ({
    page,
  }) => {
    const date = new Date().toISOString().slice(0, 10);
    const titleA = `E2E Previous A ${Date.now()}`;
    const titleB = `E2E Previous B ${Date.now()}`;
    await createMeeting(page, titleA);
    await createMeeting(page, titleB);

    await page.goto("/previous-meetings");
    await expect(page.getByRole("heading", { name: "Previous Meetings", level: 3 })).toBeVisible();

    for (const title of [titleA, titleB]) {
      const row = rowFor(page, title);
      await expect(row).toBeVisible();
      await expect(row.getByText(date, { exact: true })).toBeVisible();
      await expect(row.getByText("John Admin")).toBeVisible();
      await expect(row.getByText("0 tasks", { exact: true })).toBeVisible();
    }
  });

  test("a meeting's task count updates as tasks are added and removed", async ({ page }) => {
    const meetingTitle = `E2E Previous Count ${Date.now()}`;
    const taskTitle = `Task ${Date.now()}`;
    await createMeeting(page, meetingTitle);

    await page.getByRole("button", { name: "+ Create Task" }).click();
    await page.getByLabel("Task Title").fill(taskTitle);
    await page.getByLabel("Assignee").selectOption({ label: "John Admin" });
    await page.getByRole("button", { name: "Save" }).click();
    await expect(page.getByText(taskTitle, { exact: true })).toBeVisible();

    await page.goto("/previous-meetings");
    await expect(rowFor(page, meetingTitle).getByText("1 tasks", { exact: true })).toBeVisible();

    await page.goBack();
    await expect(page).toHaveURL(/\/meetings\/\d+$/);
    await page.getByText(taskTitle, { exact: true }).click();
    await page.getByRole("button", { name: "Delete Task" }).click();
    await expect(page.getByText(taskTitle, { exact: true })).not.toBeVisible();

    await page.goto("/previous-meetings");
    await expect(rowFor(page, meetingTitle).getByText("0 tasks", { exact: true })).toBeVisible();
  });

  test("selecting a meeting from the list opens its full details", async ({ page }) => {
    const meetingTitle = `E2E Previous Open ${Date.now()}`;
    const meetingId = await createMeeting(page, meetingTitle);

    await page.goto("/previous-meetings");
    await rowFor(page, meetingTitle)
      .getByRole("button", { name: "Open Meeting Details" })
      .click();

    await expect(page).toHaveURL(new RegExp(`/meetings/${meetingId}$`));
    await expect(page.getByRole("heading", { name: meetingTitle })).toBeVisible();
  });
});
