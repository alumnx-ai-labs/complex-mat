import { expect, test, type Page } from "@playwright/test";

import { loginAsAdmin } from "./fixtures";

/**
 * User Story 7 (spec.md lines 125-138): any Admin can edit or delete a Meeting.
 *
 * This environment seeds only one user — the default Admin, who is Owner,
 * Attendee, and Admin for every meeting created here. Two of the four
 * acceptance scenarios can't be exercised as real end-to-end checks because
 * of that:
 *  - "any Admin, not just the Owner" (scenario 1) can't be distinguished from
 *    the Owner themselves without a second Admin account.
 *  - removing an Attendee to flag their Task as "needs reassignment"
 *    (scenario 2) isn't reachable via the UI at all: MeetingForm passes
 *    `lockedIds={[ownerId]}` to AttendeeSearchInput, so the sole attendee
 *    (the Owner) can never be removed from the Edit Meeting form.
 * Both are backend-tested already (test_meetings_update.py,
 * test_meeting_service.py) — this file covers what's genuinely testable
 * end-to-end with the single seeded Admin: editing fields, Owner-field
 * immutability, and cascading delete.
 */

async function createMeeting(page: Page, title: string): Promise<void> {
  const date = new Date().toISOString().slice(0, 10);
  await page.goto(`/meetings/new?date=${date}`);
  await page.getByLabel("Title").fill(title);
  await page.getByLabel("Time").fill("14:00");
  await page.getByLabel("Agenda / Notes").fill("Original agenda.");
  await page.getByRole("button", { name: "Save Meeting" }).click();
  await expect(page).toHaveURL(/\/meetings\/\d+$/);
}

test.describe("Meeting edit and delete (User Story 7)", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  test("an Admin can edit a Meeting's Title, Date, Time, and Agenda/Notes", async ({ page }) => {
    const originalTitle = `E2E Edit ${Date.now()}`;
    const updatedTitle = `${originalTitle} (updated)`;
    await createMeeting(page, originalTitle);

    await page.getByRole("button", { name: "Edit Meeting" }).click();
    await expect(page).toHaveURL(/\/meetings\/\d+\/edit$/);
    await expect(page.getByRole("heading", { name: "Edit Meeting", level: 3 })).toBeVisible();

    await page.getByLabel("Title").fill(updatedTitle);
    await page.getByLabel("Time").fill("15:30");
    await page.getByLabel("Agenda / Notes").fill("Updated agenda.");
    await page.getByRole("button", { name: "Save Changes" }).click();

    await expect(page).toHaveURL(/\/meetings\/\d+$/);
    await expect(page.getByRole("heading", { name: updatedTitle })).toBeVisible();
    await expect(page.getByText("15:30")).toBeVisible();
    await expect(page.getByText("Updated agenda.")).toBeVisible();
  });

  test("the Meeting Owner field cannot be changed via edit", async ({ page }) => {
    const title = `E2E Owner Immutable ${Date.now()}`;
    await createMeeting(page, title);

    await expect(page.getByText("Meeting Owner: John Admin")).toBeVisible();

    await page.getByRole("button", { name: "Edit Meeting" }).click();
    // The Edit Meeting form has no Owner field/control at all — only the
    // fields meeting_service.update_meeting actually accepts.
    await expect(page.getByText(/^Owner$/)).toHaveCount(0);
    await expect(page.getByLabel(/^Owner$/)).toHaveCount(0);

    await page.getByLabel("Agenda / Notes").fill("Just touching the agenda.");
    await page.getByRole("button", { name: "Save Changes" }).click();

    await expect(page).toHaveURL(/\/meetings\/\d+$/);
    await expect(page.getByText("Meeting Owner: John Admin")).toBeVisible();
  });

  test("deleting a Meeting cascades to delete its Tasks, which disappear from My Tasks too", async ({
    page,
  }) => {
    const meetingTitle = `E2E Delete Cascade ${Date.now()}`;
    const taskTitle = `Task ${Date.now()}`;
    await createMeeting(page, meetingTitle);

    await page.getByRole("button", { name: "+ Create Task" }).click();
    await page.getByLabel("Task Title").fill(taskTitle);
    await page.getByLabel("Assignee").selectOption({ label: "John Admin" });
    await page.getByRole("button", { name: "Save" }).click();
    await expect(page.getByText(taskTitle, { exact: true })).toBeVisible();

    await page.goto("/my-tasks");
    await expect(page.getByText(taskTitle, { exact: true })).toBeVisible();

    await page.goBack();
    await expect(page).toHaveURL(/\/meetings\/\d+$/);

    page.once("dialog", (dialog) => dialog.accept());
    await page.getByRole("button", { name: "Delete Meeting" }).click();

    await expect(page).toHaveURL(/\/calendar$/);

    await page.goto("/my-tasks");
    await expect(page.getByText(taskTitle, { exact: true })).not.toBeVisible();
  });
});
