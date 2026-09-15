import { expect, test, type Page } from "@playwright/test";

import { ADMIN_MAIL_ID, ADMIN_PASSWORD, loginAsAdmin } from "./fixtures";

/**
 * User Story 10 (spec.md, "Admin Reviews the Activity Log"): an Admin opens
 * Activity Log and sees who did what and when, across meetings, tasks,
 * people, and mentions.
 *
 * `ActivityLogPage.tsx` renders each row as
 * "<Actor> | <Action Title Case> (<EntityType> #<id>) | <timestamp>", built
 * from the raw `action`/`entityType` strings `log_activity(...)` calls write
 * server-side (backend/app/services/*.py) — e.g. `MEETING_CREATED` + `Meeting`
 * becomes "Meeting Created (Meeting #12)". Rows come back newest-first
 * (`ActivityLogRepository.list` orders by timestamp DESC, id DESC).
 */

async function login(page: Page, employeeMailId: string, password: string): Promise<void> {
  await page.goto("/login");
  await page.getByLabel("Employee Mail ID").fill(employeeMailId);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByLabel("I agree to the Terms and Conditions").check();
  await page.getByRole("button", { name: "Sign In" }).click();
}

test.describe("Activity Log (User Story 10)", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  test("a Team Member cannot reach Activity Log", async ({ page, browser }) => {
    const stamp = `${Date.now()}${Math.floor(Math.random() * 10_000)}`;
    const member = {
      name: `Log Viewer ${stamp}`,
      mailId: `log.viewer.${stamp}@example.com`,
      employeeId: `E2E-${stamp}`,
      password: "InitialPass123!",
    };

    await page.goto("/people");
    await page.getByRole("button", { name: "+ Add Member" }).click();
    await page.getByLabel("Employee Name").fill(member.name);
    await page.getByLabel("Employee Mail ID").fill(member.mailId);
    await page.getByLabel("Employee ID").fill(member.employeeId);
    await page.getByLabel("Password").fill(member.password);
    await page.getByRole("button", { name: "Save Member" }).click();
    await expect(page.locator("tr", { hasText: member.mailId })).toBeVisible();

    // This test spans two browser contexts (create the member here, then a
    // fresh login as them), which makes it more exposed to timing pressure
    // under load than the suite's single-context specs — give its
    // network-dependent assertions explicit headroom accordingly.
    const HEAVY_TIMEOUT = { timeout: 15_000 };

    const memberContext = await browser.newContext();
    const memberPage = await memberContext.newPage();
    await login(memberPage, member.mailId, member.password);
    await expect(memberPage).toHaveURL(/\/calendar$/, HEAVY_TIMEOUT);

    await expect(
      memberPage.getByRole("navigation", { name: "Main navigation" }).getByRole("link", { name: /Activity Log/ }),
    ).not.toBeVisible();

    await memberPage.goto("/activity-log");
    await expect(memberPage).not.toHaveURL(/\/activity-log$/, HEAVY_TIMEOUT);

    await memberContext.close();
  });

  test("creating a Meeting, creating a Task, and adding a Member each appear in the Activity Log with actor and timestamp", async ({
    page,
  }) => {
    const meetingTitle = `E2E Activity Log ${Date.now()}`;
    const taskTitle = `Task ${Date.now()}`;
    const stamp = `${Date.now()}${Math.floor(Math.random() * 10_000)}`;
    const member = {
      name: `Logged Member ${stamp}`,
      mailId: `logged.member.${stamp}@example.com`,
      employeeId: `E2E-${stamp}`,
      password: "InitialPass123!",
    };

    const date = new Date().toISOString().slice(0, 10);
    await page.goto(`/meetings/new?date=${date}`);
    await page.getByLabel("Title").fill(meetingTitle);
    await page.getByLabel("Time").fill("14:00");
    await page.getByRole("button", { name: "Save Meeting" }).click();
    await expect(page).toHaveURL(/\/meetings\/\d+$/);
    const meetingId = page.url().match(/\/meetings\/(\d+)$/)?.[1];

    await page.getByRole("button", { name: "+ Create Task" }).click();
    await page.getByLabel("Task Title").fill(taskTitle);
    await page.getByLabel("Assignee").selectOption({ label: "John Admin" });
    await page.getByRole("button", { name: "Save" }).click();
    await expect(page.getByText(taskTitle, { exact: true })).toBeVisible();

    await page.goto("/people");
    await page.getByRole("button", { name: "+ Add Member" }).click();
    await page.getByLabel("Employee Name").fill(member.name);
    await page.getByLabel("Employee Mail ID").fill(member.mailId);
    await page.getByLabel("Employee ID").fill(member.employeeId);
    await page.getByLabel("Password").fill(member.password);
    await page.getByRole("button", { name: "Save Member" }).click();
    await expect(page.locator("tr", { hasText: member.mailId })).toBeVisible();

    await page.goto("/activity-log");
    await expect(page.getByRole("heading", { name: "Activity Log", level: 3 })).toBeVisible();

    const meetingRow = page.locator("tr", { hasText: `Meeting Created (Meeting #${meetingId})` });
    await expect(meetingRow).toBeVisible();
    await expect(meetingRow).toContainText("John Admin");

    const taskRow = page.locator("tr", { hasText: "Task Created (Task #" });
    await expect(taskRow.first()).toContainText("John Admin");

    const memberRow = page.locator("tr", { hasText: "Member Added (User #" });
    await expect(memberRow.first()).toContainText("John Admin");
  });

  test("deleting a Meeting (cascading its Tasks) is recorded in the Activity Log", async ({ page }) => {
    const meetingTitle = `E2E Activity Delete ${Date.now()}`;
    const date = new Date().toISOString().slice(0, 10);
    await page.goto(`/meetings/new?date=${date}`);
    await page.getByLabel("Title").fill(meetingTitle);
    await page.getByLabel("Time").fill("14:00");
    await page.getByRole("button", { name: "Save Meeting" }).click();
    await expect(page).toHaveURL(/\/meetings\/\d+$/);
    const meetingId = page.url().match(/\/meetings\/(\d+)$/)?.[1];

    page.once("dialog", (dialog) => dialog.accept());
    await page.getByRole("button", { name: "Delete Meeting" }).click();
    await expect(page).toHaveURL(/\/calendar$/);

    await page.goto("/activity-log");
    const deletionRow = page.locator("tr", { hasText: `Meeting Deleted (Meeting #${meetingId})` });
    await expect(deletionRow).toBeVisible();
    await expect(deletionRow).toContainText("John Admin");
  });
});
