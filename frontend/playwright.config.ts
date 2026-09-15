import { defineConfig, devices } from "@playwright/test";

const FRONTEND_PORT = 5173;
const BACKEND_PORT = 8000;

export const ADMIN_MAIL_ID = process.env.E2E_ADMIN_MAIL_ID ?? "john@example.com";
export const ADMIN_PASSWORD = process.env.E2E_ADMIN_PASSWORD ?? "ChangeMe123!";

const rawBaseURL = process.env.PLAYWRIGHT_BASE_URL;
const REMOTE_BASE_URL = rawBaseURL
  ? /^https?:\/\//.test(rawBaseURL)
    ? rawBaseURL
    : `https://${rawBaseURL}`
  : undefined;

const VERCEL_BYPASS_TOKEN = process.env.VERCEL_PROTECTION_BYPASS;

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: process.env.CI
    ? [["junit", { outputFile: "playwright-report/results.xml" }], ["html", { open: "never" }]]
    : "html",
  use: {
    baseURL: REMOTE_BASE_URL ?? `http://localhost:${FRONTEND_PORT}`,
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    ...(VERCEL_BYPASS_TOKEN
      ? {
          extraHTTPHeaders: {
            "x-vercel-protection-bypass": VERCEL_BYPASS_TOKEN,
            "x-vercel-set-bypass-cookie": "true",
          },
        }
      : {}),
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: REMOTE_BASE_URL
    ? undefined
    : [
        {
          command: "npm run dev -- --port 5173 --strictPort",
          cwd: import.meta.dirname,
          url: `http://localhost:${FRONTEND_PORT}`,
          reuseExistingServer: !process.env.CI,
          timeout: 120_000,
        },
        {
          command:
            "node -e \"require('fs').rmSync('e2e-test.db', { force: true })\" && python -m app.seed && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000",
          cwd: `${import.meta.dirname}/../backend`,
          url: `http://localhost:${BACKEND_PORT}/docs`,
          reuseExistingServer: !process.env.CI,
          timeout: 120_000,
          env: {
            DATABASE_PATH: "./e2e-test.db",
            CORS_ORIGINS: `http://localhost:${FRONTEND_PORT}`,
            DEFAULT_ADMIN_MAIL_ID: ADMIN_MAIL_ID,
            DEFAULT_ADMIN_PASSWORD: ADMIN_PASSWORD,
          },
        },
      ],
});
