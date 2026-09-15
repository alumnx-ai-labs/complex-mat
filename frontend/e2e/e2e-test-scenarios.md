# E2E test scenarios

Readable summary of what each Playwright spec in this folder verifies. For how to run these, see the [README](../../README.md#end-to-end-tests).

## `auth.spec.ts` — Authentication (User Story 1)

| Scenario | Expectation |
| --- | --- |
| Unauthenticated visit to `/calendar` | Redirected to `/login` |
| Sign in with the wrong password | Alert shows "Incorrect Employee Mail ID or Password."; stays on `/login` |
| Sign in as Admin with valid credentials | Lands on `/calendar` |
| Authenticated user visits `/login` | Redirected back to `/calendar` |
| Fresh browser context (no session) | Session from one context never leaks into another; still redirected to `/login` |
| Selecting the "Team Member" sign-in card, then signing in with Admin credentials | Still lands as Admin (People/Activity Log nav visible) — the card is cosmetic client-side state; `authApi.login()` never sends it |
| Admin views the main navigation | Calendar, My Tasks, Previous Meetings, People, and Activity Log are all present |
| A Team Member views the main navigation | Calendar, My Tasks, and Previous Meetings are present; People and Activity Log are not |
| Login screen | No sign-up/register/create-account option anywhere on it |

Known gap: this environment seeds only an Admin account, so the "Team Member" scenario simulates the role client-side by patching `sessionStorage` after a real Admin login (same technique as `meeting-creation.spec.ts`'s "a non-admin cannot reach Create Meeting" test) and reloading. This exercises `NavSidebar`'s role-gating logic, not the backend's actual role assignment/authorization for a real Team Member account.

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

## `task-comments.spec.ts` — Comments, @mentions, and Azure DevOps references (User Story 5)

| Scenario | Expectation |
| --- | --- |
| Owner types `@Joh` in the comment box | Attendee suggestion "John Admin" appears; selecting it inserts `@John ` |
| Owner posts a comment | Comment appears in the thread with the author's name and message |
| Owner types `@1234` (a numeric token) in a comment | Comment renders a linked "ADO #1234" chip; shown as "(unavailable)" since this e2e environment has no Azure DevOps credentials configured |
| Task Description/Notes contains `@5678` at creation time | Task's "Linked Azure DevOps Items" section shows an "ADO #5678" chip, also "(unavailable)" |
| Creating a new Task (no Task yet) | Comment composer is not rendered until the Task exists |

Note: this environment seeds only a single default Admin (also the Meeting Owner and Task Assignee for every task created here), so the "a non-Owner/non-Assignee/non-Admin cannot comment" rule (enforced server-side in `comment_service._can_comment`) isn't exercised by these tests — there's no Team Member creation flow yet (see `specs/001-meeting-action-tracker/tasks.md` T036/T038).

## `meeting-edit-delete.spec.ts` — Meeting edit and delete (User Story 7)

| Scenario | Expectation |
| --- | --- |
| Admin opens Edit Meeting and changes Title, Time, and Agenda/Notes | Saved; Meeting Details reflects the new values |
| Admin edits a Meeting | The edit form has no Owner field/control at all; the Owner pill is unchanged after saving |
| Admin deletes a Meeting that has a Task | Confirmed via the browser `confirm()` dialog; redirected to `/calendar`; the Task is gone from My Tasks too |

Known gaps (backend-tested already, not reachable via this UI with a single seeded user): "any Admin, not just the Owner, can edit" (scenario 1) can't be distinguished from the Owner themselves without a second Admin account; removing an Attendee to flag their Task as "needs reassignment" (scenario 2) isn't reachable at all — `MeetingForm` passes `lockedIds={[ownerId]}` to `AttendeeSearchInput`, so the sole attendee (the Owner) can never be removed from the Edit Meeting form.

## `task-assignment-notifications.spec.ts` — Assignment notifications (User Story 6)

| Scenario | Expectation |
| --- | --- |
| Owner assigns a Task to an attendee at creation time | `POST /api/meetings/:id/tasks` responds `2xx` well within 5s — the (no-op, unconfigured-SMTP) notification email is scheduled via FastAPI `BackgroundTasks` and can't block the response (FR-038); the Task appears on the board |

Only the task-assignment notification trigger (FR-034) is implemented in the backend (`notification_service.notify_task_assigned`, wired from `backend/app/api/tasks.py`). Comment-posted (FR-035) and @mention (FR-036) notifications have no implementation yet — `tasks.md` T032 marks this story "partial" — and there is no notifications UI anywhere in the frontend, so neither is testable via Playwright today. Actual email delivery also can't be observed from the browser: SMTP is unconfigured in this e2e environment (`backend/.env` `SMTP_HOST` is blank), so `EmailSender.send()` is a no-op that only logs.

Known gaps (shared with `task-comments.spec.ts`): this environment seeds only one user (the default Admin), who is Meeting Owner, Task Assignee, and Admin for every task created in these tests. A true *reassignment* to a different Assignee — the other trigger for `notify_task_assigned` — isn't reachable without a second seeded user, since there's no Team Member creation flow yet (`tasks.md` T036/T038).

## `previous-meetings.spec.ts` — Previous Meetings (User Story 8)

| Scenario | Expectation |
| --- | --- |
| Two or more meetings exist | Every meeting is listed with its title, date, meeting owner, and task count |
| A meeting's tasks are added then deleted | The task count in Previous Meetings updates from 0 to 1 and back to 0 |
| A meeting is selected from the list | Its full details open at `/meetings/:id` |

Known gap (shared with other files): this environment seeds only one user (the default Admin), who is Owner and Attendee for every meeting created here, so "a Team Member not invited to a meeting does not see it in their list" (acceptance scenario 2) isn't reachable as a real end-to-end check — it's covered server-side already (`test_previous_meetings_workflow.py`).

## Shared fixture

`fixtures.ts` exports `loginAsAdmin(page)`, which logs in with the configured admin credentials, checks the "I agree to the Terms and Conditions" box (User Story 1), and asserts the redirect to `/calendar`. Used as a `test.beforeEach` in `calendar.spec.ts`, `meeting-creation.spec.ts`, `meeting-edit-delete.spec.ts`, and `previous-meetings.spec.ts`, and called directly by several `auth.spec.ts` cases.
