import { expect, test, type Page } from "@playwright/test";

import { ADMIN_MAIL_ID, ADMIN_PASSWORD, loginAsAdmin } from "./fixtures";

/**
 * User Story 9 (spec.md lines 178-197): Admin manages member accounts, roles,
 * and access from the People screen.
 *
 * Unlike every other story tested in this suite, this one is the mechanism
 * that actually creates a second real user account — so, uniquely, the
 * "Team Member can't do X" scenarios here are tested against a genuine
 * Team Member session, not the sessionStorage role-swap trick used elsewhere
 * (see the "Known gap" notes in e2e-test-scenarios.md for auth.spec.ts /
 * task-comments.spec.ts / meeting-edit-delete.spec.ts).
 */

async function login(page: Page, employeeMailId: string, password: string): Promise<void> {
  await page.goto("/login");
  await page.getByLabel("Employee Mail ID").fill(employeeMailId);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByLabel("I agree to the Terms and Conditions").check();
  await page.getByRole("button", { name: "Sign In" }).click();
}

function uniqueMember(prefix: string) {
  const stamp = `${Date.now()}${Math.floor(Math.random() * 10_000)}`;
  return {
    name: `${prefix} ${stamp}`,
    mailId: `${prefix.toLowerCase().replace(/\s+/g, ".")}.${stamp}@example.com`,
    employeeId: `E2E-${stamp}`,
    password: "InitialPass123!",
  };
}

async function addMember(
  page: Page,
  member: { name: string; mailId: string; employeeId: string; password: string; role: "TEAM_MEMBER" | "ADMIN" },
): Promise<void> {
  await page.goto("/people");
  await page.getByRole("button", { name: "+ Add Member" }).click();
  await page.getByLabel("Employee Name").fill(member.name);
  await page.getByLabel("Employee Mail ID").fill(member.mailId);
  await page.getByLabel("Employee ID").fill(member.employeeId);
  await page.getByLabel("Password").fill(member.password);
  await page.locator("#am-role").selectOption(member.role === "ADMIN" ? "Admin" : "Team Member");
  await page.getByRole("button", { name: "Save Member" }).click();
  await expect(page.locator("tr", { hasText: member.mailId })).toBeVisible();
}

function memberRow(page: Page, mailId: string) {
  return page.locator("tr", { hasText: mailId });
}

test.describe("People management (User Story 9)", () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  test("an Admin adds a member who can sign in, and a Team Member cannot reach People", async ({
    page,
    browser,
  }) => {
    const member = uniqueMember("New Hire");
    await addMember(page, { ...member, role: "TEAM_MEMBER" });

    const row = memberRow(page, member.mailId);
    await expect(row).toContainText(member.name);
    await expect(row).toContainText(member.employeeId);
    await expect(row.getByText("Active")).toBeVisible();

    const memberContext = await browser.newContext();
    const memberPage = await memberContext.newPage();
    await login(memberPage, member.mailId, member.password);
    await expect(memberPage).toHaveURL(/\/calendar$/);

    const nav = memberPage.getByRole("navigation", { name: "Main navigation" });
    await expect(nav.getByRole("link", { name: /People/ })).not.toBeVisible();
    await expect(nav.getByRole("link", { name: /Activity Log/ })).not.toBeVisible();

    await memberPage.goto("/people");
    await expect(memberPage).not.toHaveURL(/\/people$/);

    await memberContext.close();
  });

  test("changing a member's Role applies the new permissions on their next sign-in", async ({
    page,
    browser,
  }) => {
    const member = uniqueMember("Role Change");
    await addMember(page, { ...member, role: "TEAM_MEMBER" });

    await memberRow(page, member.mailId).getByLabel("Role").selectOption("Admin");
    await expect(memberRow(page, member.mailId).getByLabel("Role")).toHaveValue("ADMIN");

    const memberContext = await browser.newContext();
    const memberPage = await memberContext.newPage();
    await login(memberPage, member.mailId, member.password);
    await expect(memberPage).toHaveURL(/\/calendar$/);

    const nav = memberPage.getByRole("navigation", { name: "Main navigation" });
    await expect(nav.getByRole("link", { name: /People/ })).toBeVisible();
    await expect(nav.getByRole("link", { name: /Activity Log/ })).toBeVisible();

    await memberContext.close();
  });

  test("resetting a member's Password rejects the old one and accepts the new one", async ({
    page,
    browser,
  }) => {
    const member = uniqueMember("Reset Pw");
    await addMember(page, { ...member, role: "TEAM_MEMBER" });

    await memberRow(page, member.mailId).getByRole("button", { name: "Reset Password" }).click();
    const newPassword = "BrandNewPass456!";
    const resetModal = page.locator(".modal", { has: page.getByRole("heading", { name: "Reset Password" }) });
    await resetModal.getByLabel(`New Password for ${member.name}`).fill(newPassword);
    await resetModal.getByRole("button", { name: "Reset Password" }).click();
    await expect(resetModal).not.toBeVisible();

    const memberContext = await browser.newContext();
    const memberPage = await memberContext.newPage();

    await login(memberPage, member.mailId, member.password);
    await expect(memberPage.getByRole("alert")).toHaveText("Incorrect Employee Mail ID or Password.");
    await expect(memberPage).toHaveURL(/\/login$/);

    await memberPage.getByLabel("Password", { exact: true }).fill(newPassword);
    await memberPage.getByRole("button", { name: "Sign In" }).click();
    await expect(memberPage).toHaveURL(/\/calendar$/);

    await memberContext.close();
  });

  test("deactivating a member blocks sign-in and hides them from attendee search; reactivating restores both", async ({
    page,
    browser,
  }) => {
    const member = uniqueMember("Deactivate Me");
    await addMember(page, { ...member, role: "TEAM_MEMBER" });

    await memberRow(page, member.mailId).getByRole("button", { name: "Deactivate" }).click();
    await expect(memberRow(page, member.mailId).getByText("Inactive")).toBeVisible();

    const memberContext = await browser.newContext();
    const memberPage = await memberContext.newPage();
    await login(memberPage, member.mailId, member.password);
    await expect(memberPage.getByRole("alert")).toHaveText("Incorrect Employee Mail ID or Password.");
    await expect(memberPage).toHaveURL(/\/login$/);
    await memberContext.close();

    const date = new Date().toISOString().slice(0, 10);
    await page.goto(`/meetings/new?date=${date}`);
    const attendeeSearch = page.getByPlaceholder("Search internal members by Employee Name or Employee ID…");
    await attendeeSearch.fill(member.name);
    await expect(page.locator(".search-results .opt")).toHaveCount(0);

    await page.goto("/people");
    await memberRow(page, member.mailId).getByRole("button", { name: "Reactivate" }).click();
    await expect(memberRow(page, member.mailId).getByText("Active")).toBeVisible();

    const reactivatedContext = await browser.newContext();
    const reactivatedPage = await reactivatedContext.newPage();
    await login(reactivatedPage, member.mailId, member.password);
    await expect(reactivatedPage).toHaveURL(/\/calendar$/);
    await reactivatedContext.close();

    await page.goto(`/meetings/new?date=${date}`);
    await page.getByPlaceholder("Search internal members by Employee Name or Employee ID…").fill(member.name);
    await expect(page.locator(".search-results .opt", { hasText: member.name })).toBeVisible();
  });

  test("deactivating a member who owns Meetings transfers those Meetings to the default Admin", async ({
    page,
    browser,
  }) => {
    const member = uniqueMember("Owner To Deactivate");
    await addMember(page, { ...member, role: "ADMIN" });

    // This test spans two browser contexts and a create+login+create+deactivate
    // chain — the heaviest in this file — so its network-dependent assertions
    // get explicit headroom rather than relying on the (shorter) local default.
    const HEAVY_TIMEOUT = { timeout: 15_000 };

    const memberContext = await browser.newContext();
    const memberPage = await memberContext.newPage();
    await login(memberPage, member.mailId, member.password);
    await expect(memberPage).toHaveURL(/\/calendar$/, HEAVY_TIMEOUT);

    const meetingTitle = `E2E Ownership Transfer ${Date.now()}`;
    const date = new Date().toISOString().slice(0, 10);
    await memberPage.goto(`/meetings/new?date=${date}`);
    await memberPage.getByLabel("Title").fill(meetingTitle);
    await memberPage.getByLabel("Time").fill("14:00");
    await memberPage.getByRole("button", { name: "Save Meeting" }).click();
    await expect(memberPage).toHaveURL(/\/meetings\/\d+$/, HEAVY_TIMEOUT);
    await expect(memberPage.getByText(`Meeting Owner: ${member.name}`)).toBeVisible(HEAVY_TIMEOUT);
    const meetingUrl = memberPage.url();
    await memberContext.close();

    await page.goto("/people");
    await memberRow(page, member.mailId).getByRole("button", { name: "Deactivate" }).click();
    await expect(memberRow(page, member.mailId).getByText("Inactive")).toBeVisible(HEAVY_TIMEOUT);

    await page.goto(meetingUrl);
    await expect(page.getByText("Meeting Owner: John Admin")).toBeVisible(HEAVY_TIMEOUT);
  });
});
