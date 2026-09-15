import { expect, test } from "@playwright/test";

import { ADMIN_MAIL_ID, ADMIN_PASSWORD, loginAsAdmin } from "./fixtures";

test.describe("Authentication", () => {
  test("redirects an unauthenticated user to /login", async ({ page }) => {
    await page.goto("/calendar");
    await expect(page).toHaveURL(/\/login$/);
  });

  test("shows an error for incorrect credentials", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel("Employee Mail ID").fill(ADMIN_MAIL_ID);
    await page.getByLabel("Password", { exact: true }).fill("wrong-password");
    await page.getByLabel("I agree to the Terms and Conditions").check();
    await page.getByRole("button", { name: "Sign In" }).click();

    await expect(page.getByRole("alert")).toHaveText("Incorrect Employee Mail ID or Password.");
    await expect(page).toHaveURL(/\/login$/);
  });

  test("logs the admin in and lands on the calendar", async ({ page }) => {
    await loginAsAdmin(page);
    await expect(page.getByLabel("Previous month")).toBeVisible();
  });

  test("redirects an authenticated user away from /login", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/login");
    await expect(page).toHaveURL(/\/calendar$/);
  });

  test("credentials do not carry over to a fresh browser context", async ({ browser }) => {
    const context = await browser.newContext();
    const page = await context.newPage();
    await page.goto("/calendar");
    await expect(page).toHaveURL(/\/login$/);
    await context.close();
  });

  test("selecting the Team Member sign-in option doesn't change an Admin account's actual role", async ({
    page,
  }) => {
    await page.goto("/login");
    // The "Continue as" cards are cosmetic UI state only — authApi.login() never
    // sends the selected option, so an Admin account must still land as Admin.
    await page.getByRole("radio", { name: /^Team Member/ }).click();
    await page.getByLabel("Employee Mail ID").fill(ADMIN_MAIL_ID);
    await page.getByLabel("Password", { exact: true }).fill(ADMIN_PASSWORD);
    await page.getByLabel("I agree to the Terms and Conditions").check();
    await page.getByRole("button", { name: "Sign In" }).click();

    await expect(page).toHaveURL(/\/calendar$/);
    await expect(page.getByRole("link", { name: /People/ })).toBeVisible();
    await expect(page.getByRole("link", { name: /Activity Log/ })).toBeVisible();
  });

  test("an Admin sees Calendar, My Tasks, Previous Meetings, People, and Activity Log", async ({ page }) => {
    await loginAsAdmin(page);

    const nav = page.getByRole("navigation", { name: "Main navigation" });
    await expect(nav.getByRole("link", { name: /Calendar/ })).toBeVisible();
    await expect(nav.getByRole("link", { name: /My Tasks/ })).toBeVisible();
    await expect(nav.getByRole("link", { name: /Previous Meetings/ })).toBeVisible();
    await expect(nav.getByRole("link", { name: /People/ })).toBeVisible();
    await expect(nav.getByRole("link", { name: /Activity Log/ })).toBeVisible();
  });

  test("a Team Member does not see People or Activity Log navigation", async ({ page }) => {
    await loginAsAdmin(page);

    // This environment seeds only an Admin account, so a Team Member's own
    // session is simulated client-side (same technique as
    // meeting-creation.spec.ts's "a non-admin cannot reach Create Meeting"
    // test) purely to exercise NavSidebar's role-gating logic, not the
    // backend's role assignment.
    await page.evaluate(() => {
      const session = JSON.parse(sessionStorage.getItem("mat.session") ?? "null");
      if (session) {
        session.user.role = "TEAM_MEMBER";
        sessionStorage.setItem("mat.session", JSON.stringify(session));
      }
    });
    await page.reload();

    const nav = page.getByRole("navigation", { name: "Main navigation" });
    await expect(nav.getByRole("link", { name: /Calendar/ })).toBeVisible();
    await expect(nav.getByRole("link", { name: /My Tasks/ })).toBeVisible();
    await expect(nav.getByRole("link", { name: /Previous Meetings/ })).toBeVisible();
    await expect(nav.getByRole("link", { name: /People/ })).not.toBeVisible();
    await expect(nav.getByRole("link", { name: /Activity Log/ })).not.toBeVisible();
  });

  test("the Login screen has no sign-up option", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByRole("link", { name: /sign up|register|create an account/i })).toHaveCount(0);
    await expect(page.getByRole("button", { name: /sign up|register|create an account/i })).toHaveCount(0);
  });
});
