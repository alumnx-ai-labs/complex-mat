# E2E test scenarios

Readable summary of what each Playwright spec in this folder verifies. For how to run these, see the [README](../../README.md#end-to-end-tests).

## `auth.spec.ts` — Authentication

| Scenario | Expectation |
| --- | --- |
| Unauthenticated visit to `/calendar` | Redirected to `/login` |
| Sign in with the wrong password | Alert shows "Incorrect Employee Mail ID or Password."; stays on `/login` |
| Sign in as Admin with valid credentials | Lands on `/calendar` |
| Authenticated user visits `/login` | Redirected back to `/calendar` |
| Fresh browser context (no session) | Session from one context never leaks into another; still redirected to `/login` |

## `calendar.spec.ts` — Calendar

| Scenario | Expectation |
| --- | --- |
| Click "Next month" then "Previous month" | Month label advances, then returns to the original label |
| Click a day cell (as Admin) | Navigates to `/meetings/new?date=YYYY-MM-01`; the "Date" field is prefilled with that date |

## `meeting-creation.spec.ts` — Meeting creation

| Scenario | Expectation |
| --- | --- |
| Admin fills in title, time, and agenda, then saves | Redirected to `/meetings/:id`; the new title and agenda text are visible |
| Save with no title | Alert shows "Title is required."; stays on `/meetings/new` |
| Team Member role tries to open `/meetings/new` | Redirected away, back to `/calendar` |

## Shared fixture

`fixtures.ts` exports `loginAsAdmin(page)`, which logs in with the configured admin credentials and asserts the redirect to `/calendar`. Used as a `test.beforeEach` in `calendar.spec.ts` and `meeting-creation.spec.ts`, and called directly by two `auth.spec.ts` cases.
