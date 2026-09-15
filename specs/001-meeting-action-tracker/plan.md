# Implementation Plan: Meeting Action Tracker (MAT)

**Branch**: `001-meeting-action-tracker` | **Date**: 2026-09-13 | **Spec**: [spec.md](./spec.md)

**Amended**: 2026-09-14 — Authentication switched to Google Sign-In (Firebase Authentication) with
auto-provisioned accounts; database switched to MongoDB; People "Add Member" removed. See spec.md's
2026-09-14 amendment note and constitution v3.0.0.

**Amended**: 2026-09-15 — Reverted the Google Sign-In/Firebase auth change. Authentication is
Employee Mail ID/Password again: no self-registration, and only an Admin creates member accounts
(Employee Name, Employee Mail ID, Employee ID, Password, Role) from the People screen's "Add
Member" action, exactly as the BRD specifies. The Login screen also gains an "I agree to the Terms
and Conditions" checkbox that gates sign-in, with acceptance recorded on the account. See spec.md's
2026-09-15 amendment note.

**Amended**: 2026-09-15 — Reverted the 2026-09-14 MongoDB switch. Storage is a local, file-based
database (SQLite via SQLAlchemy) again, per constitution v4.0.0; MongoDB is no longer part of this
plan. See spec.md's 2026-09-15 amendment note.

**Input**: Feature specification from `/specs/001-meeting-action-tracker/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

MAT is a shared workspace for one internal organisation's meetings and the tasks that come out of
them, implementing the complete BRD.docx scope as amended 2026-09-15. Employee Mail ID/Password
sign-in (behind a Login screen "I agree to the Terms and Conditions" checkbox that must be checked
before sign-in is enabled) gates all access; every account has exactly one Role (Admin or Team
Member) and is created only by an Admin from the People screen's "Add Member" action (Employee
Name, Employee Mail ID, Employee ID, Password, Role) — there is no self-registration and no
auto-provisioning. Only an Admin can create a Meeting (from Calendar), and the creating Admin
becomes that meeting's Meeting Owner, who alone may assign or reassign its Tasks' Assignees. Tasks
carry Title, Description/Notes, Assignee, Due Date, and Status, worked from a personal "My Tasks"
board and a per-meeting Task Board with drag-and-drop status changes. Tasks support comments with
internal member @mentions and auto-detected, read-only Azure DevOps Story/Feature references, plus
email notifications for assignment, comments, and mentions. Admins additionally manage member
accounts — adding members, changing Role, resetting Password, and deactivating/reactivating them
(People) — and review a workspace-wide Activity Log. Technical approach: a React single-page
frontend talking over REST to a FastAPI backend, backed by a local, file-based (SQLite) database,
per the project constitution.

## Technical Context

**Language/Version**: Python 3.11 (backend); TypeScript, React 18 (frontend)

**Primary Dependencies**: FastAPI + Pydantic + SQLAlchemy (backend, per constitution's layered
architecture); `python-jose` (JWT issuing/verification) and `passlib`/`bcrypt` (Password hashing)
for the Employee Mail ID/Password auth stack — MAT stores and checks a Password itself; there is no
external identity provider. An SMTP client (e.g., stdlib `smtplib` or `aiosmtplib`) behind an
`EmailSender` interface for notifications; an HTTP client (`httpx`) wrapped by an
`AzureDevOpsClient` for Azure DevOps REST calls. React 18, React Router, a lightweight
drag-and-drop library for the Kanban board (frontend)

**Storage**: Local, file-based SQLite database (single database file), accessed through
SQLAlchemy — the single source of truth for all shared data (accounts, meetings, tasks, comments,
mentions, Azure DevOps reference cache, activity log), per constitution Principle IV

**Testing**: pytest + FastAPI's `TestClient`/httpx for backend contract and integration tests
(including Role/Owner-gated access, Employee Mail ID/Password login and Admin-only
account-creation/role-change/password-reset/deactivation flows, notification-failure resilience via
an injected fake `EmailSender`, and a fake `AzureDevOpsClient` for suggestion/reference tests);
Vitest (or Jest) + React Testing Library for frontend component/interaction tests, including the
Login screen's Terms-and-Conditions checkbox gating sign-in

**Target Platform**: Web browser, desktop and mobile viewport widths; single-instance local/dev
server deployment (no multi-region or high-availability requirement for this scope)

**Project Type**: Web application (separate frontend + backend, communicating over REST)

**Performance Goals**: Standard interactive web-app responsiveness — UI actions (opening a screen,
dragging a task) feel immediate; typical API responses complete well within what a user perceives
as instant at this scope's scale; email/Azure DevOps calls run off the request path (background
tasks / short-timeout, fail-soft external calls) so they never become the bottleneck for a
user-facing action (FR-033, FR-038)

**Constraints**: Authentication is required end-to-end (constitution Principle V) — every
non-login endpoint requires a valid session/JWT and enforces Role and, where applicable, Meeting
Owner checks server-side; the Admin-only account-creation path (no self-registration) and Admin-only
Role change/Password reset/deactivate-reactivate MUST be enforced in the backend, not only the
People screen's UI; the Login screen's "I agree to the Terms and Conditions" checkbox MUST block
sign-in client-side until checked, and a successful sign-in MUST record Terms acceptance
server-side against the account; Azure DevOps and email are external dependencies that MUST degrade
gracefully (empty suggestions / logged failure) rather than break core flows when unavailable

**Scale/Scope**: Small-to-medium internal-organisation deployment — tens to low hundreds of
concurrent users, low hundreds to low thousands of meetings/tasks/comments; ten screens (Login,
Calendar, Create Meeting, Edit Meeting, Meeting Details with its Task Board, My Tasks, Task Details,
Previous Meetings, and Admin-only People and Activity Log)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | This plan's compliance |
|---|-----------|-------------------------|
| I | Frontend-Backend Separation | React app and FastAPI app are separate deployable projects (`frontend/`, `backend/`); all communication is REST over HTTP — no shared runtime or direct DB access from the frontend. **Pass.** |
| II | React Component-Based Frontend Architecture | Frontend organized into small components (`components/`) with all HTTP calls isolated in `services/` API modules and `hooks/`; no component calls `fetch` directly; `AuthContext` isolates session/token state from presentation. **Pass.** |
| III | FastAPI Layered Backend Architecture | Backend organized as Router → Service → Repository → Database (`api/` → `services/` → `repositories/` → `models/`/DB session); routers hold no business logic, repositories hold no business rules; auth/Role/Owner checks live in dependencies and the service layer, not routers. **Pass.** |
| IV | Centralized Data Ownership | Accounts, meetings, attendees, tasks, comments, mentions, Azure DevOps reference cache, and the activity log are persisted only in the backend's SQLite database via SQLAlchemy; the frontend's own storage holds only the current session's token (a per-device convenience, not shared data). **Pass.** |
| V | Employee Mail ID/Password, Role-Based Identity | A valid Employee Mail ID/Password credential, verified server-side and resolved to a session/JWT, is required for every endpoint except the login exchange itself; accounts are created only by an Admin from the People screen's "Add Member" action (no self-registration form, no auto-provisioning); exactly two Roles are enforced via a backend dependency, set at account creation and changeable only by an Admin afterward; Meeting-Owner-only Task-Assignee control is enforced as a separate per-meeting ownership check, not conflated with the Role check; the Login screen's Terms-and-Conditions checkbox is enforced client-side (disables sign-in until checked) and acceptance is recorded server-side on successful sign-in. **Pass.** |
| VI | RESTful API Contracts | Every endpoint (Phase 1 contracts) uses resource-oriented URLs and correct HTTP verbs/status codes, with explicit Pydantic request/response DTOs — no raw dict or ORM object crosses the API boundary. **Pass.** |
| VII | Backend-Enforced Business Rules | Rules such as "assignee must be a meeting attendee," "only the Meeting Owner assigns/reassigns a Task's Assignee," "only the Assignee edits their Task's Status/Description," "only Admins create/edit/delete Meetings," and comment-posting eligibility are enforced in the backend service layer, not just the UI. **Pass.** |
| VIII | Responsive UI | Frontend layout plan uses a single responsive component tree with CSS breakpoints (stacked layout on mobile, grid/board layout on desktop) rather than separate device-specific apps, across all ten screens. **Pass.** |
| IX | Code Quality & Maintainability | Layered, single-responsibility module structure on both sides (see Project Structure), including isolated `AzureDevOpsClient` and `EmailSender`/`NotificationService` boundaries so external-integration concerns don't leak into core business logic. **Pass.** |
| X | Testing Discipline | Plan includes backend contract/integration tests per endpoint and per business rule (including Role/Owner gating and external-integration resilience), and frontend tests for the calendar, task board drag-and-drop, Role-gated navigation, and mention/Azure-DevOps-suggestion input behavior. **Pass.** |

No violations identified — the **Complexity Tracking** section below is not needed and has been
omitted. (The scope is substantially larger than the earlier MVP draft of this feature, but that
growth is a direct, faithful implementation of the BRD and the constitution, not an unjustified
deviation from either. The 2026-09-14 amendment's database switch to MongoDB was itself reverted on
2026-09-15 — storage is local, file-based SQLite again, the BRD's original model. The 2026-09-14
switch to Google Sign-In/Firebase auth with auto-provisioning was likewise an interim change that
has since been reverted (2026-09-15); Employee Mail ID/Password sign-in with Admin-only account
creation — the BRD's original model, now restored, plus the newly added Terms-and-Conditions
acceptance requirement — is a direct implementation of the constitution's Principle V, not a
deviation from it.)

## Project Structure

### Documentation (this feature)

```text
specs/001-meeting-action-tracker/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md         # Phase 1 output (/speckit-plan command)
├── quickstart.md         # Phase 1 output (/speckit-plan command)
├── contracts/             # Phase 1 output (/speckit-plan command)
│   ├── auth-api.md
│   ├── users-api.md
│   ├── meetings-api.md
│   ├── tasks-api.md
│   ├── comments-api.md
│   ├── azure-devops-api.md
│   └── activity-log-api.md
└── tasks.md              # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── main.py                     # FastAPI app instance, router registration, CORS
│   ├── core/
│   │   ├── config.py               # Settings (DB file path, JWT secret/expiry, SMTP, Azure DevOps org/PAT, CORS)
│   │   ├── security.py             # Password hashing (passlib/bcrypt) + JWT issuing/verification
│   │   └── exceptions.py           # Domain exceptions -> HTTP error mapping
│   ├── db/
│   │   └── session.py              # SQLAlchemy engine/Session setup, declarative Base
│   ├── models/                     # SQLAlchemy declarative models (one module per entity group)
│   │   ├── user.py                  # User, Role enum
│   │   ├── meeting.py                # Meeting, MeetingAttendee, WorkspaceSettings
│   │   ├── task.py                   # Task, TaskStatus enum, TaskAdoReference
│   │   ├── comment.py                # Comment, CommentMention
│   │   └── activity_log.py           # ActivityLogEntry
│   ├── schemas/                     # Pydantic request/response DTOs (one module per resource above)
│   ├── repositories/                 # Data-access layer (query/persist only), one per entity group
│   ├── services/                     # Business rules and orchestration
│   │   ├── auth_service.py            # Verify Employee Mail ID/Password, issue session/JWT, record Terms acceptance
│   │   ├── user_service.py            # Admin creates/edits members; role/password-reset/deactivate + owner-transfer side effect
│   │   ├── meeting_service.py         # Create/edit/delete, Role/attendee-visibility scoping
│   │   ├── task_service.py            # Create/edit/delete/assign/status, Owner vs Assignee rules
│   │   ├── comment_service.py         # Post comment, permission check, mention/ADO token parsing
│   │   ├── notification_service.py    # Composes + dispatches assignment/comment/mention emails
│   │   └── activity_log_service.py    # log_activity(...) helper called from the services above
│   ├── integrations/
│   │   ├── email_sender.py            # EmailSender interface + SMTP implementation
│   │   └── azure_devops_client.py     # AzureDevOpsClient: search()/get(), fail-soft on error
│   ├── deps/
│   │   └── auth.py                    # get_current_user, require_role(), require_meeting_owner()
│   └── api/                          # Routers (HTTP layer only)
│       ├── auth.py                    # /api/auth/*
│       ├── users.py                   # /api/users/*
│       ├── meetings.py                # /api/meetings/*
│       ├── tasks.py                   # /api/tasks/*, /api/meetings/{id}/tasks
│       ├── comments.py                # /api/tasks/{id}/comments, mention-search
│       ├── azure_devops.py            # /api/azure-devops/*, /api/tasks/{id}/ado-references
│       └── activity_log.py            # /api/activity-log
└── tests/
    ├── contract/                     # Per-endpoint request/response contract tests
    ├── integration/                    # Cross-layer business-rule + workflow tests
    └── unit/                           # Service-layer rule tests in isolation (incl. token parsing)

frontend/
├── src/
│   ├── main.tsx                     # App bootstrap
│   ├── App.tsx                       # Route layout (nav shell, Role-gated destinations)
│   ├── routes/
│   │   └── router.tsx                 # React Router route definitions + Role-gated route guards
│   ├── context/
│   │   └── AuthContext.tsx            # Signed-in user + session/JWT (Employee Mail ID/Password gate + provider)
│   ├── pages/
│   │   ├── LoginPage.tsx               # Team Member / Admin Employee Mail ID/Password sign-in options + Terms checkbox
│   │   ├── CalendarPage.tsx
│   │   ├── CreateMeetingPage.tsx
│   │   ├── EditMeetingPage.tsx
│   │   ├── MeetingDetailsPage.tsx       # Includes the Task Board
│   │   ├── MyTasksPage.tsx
│   │   ├── TaskDetailsPage.tsx          # Comments, mentions, Azure DevOps references
│   │   ├── PreviousMeetingsPage.tsx
│   │   ├── PeoplePage.tsx               # Admin only
│   │   └── ActivityLogPage.tsx          # Admin only
│   ├── components/
│   │   ├── calendar/                  # MonthGrid, DayCell, MeetingPill, MonthNavigator
│   │   ├── meetings/                  # MeetingForm, AttendeeSearchInput, MeetingSummaryRow
│   │   ├── tasks/                     # TaskBoard, TaskColumn, TaskCard, TaskEditModal, AssigneeControl
│   │   ├── comments/                  # CommentThread, CommentComposer (mention/ADO "@" trigger logic)
│   │   ├── people/                    # MemberTable, AddMemberModal, RoleSelect, PasswordResetModal
│   │   └── layout/                    # NavSidebar/TopBar (Role-gated items), ResponsiveShell
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useMeetings.ts
│   │   ├── useTasks.ts
│   │   ├── useComments.ts
│   │   ├── useMentionAndAdoSuggestions.ts
│   │   └── useUsers.ts
│   ├── services/                     # All backend calls live here (no component calls fetch directly)
│   │   ├── apiClient.ts               # Base fetch wrapper, attaches bearer token, error handling
│   │   ├── authApi.ts
│   │   ├── meetingsApi.ts
│   │   ├── tasksApi.ts
│   │   ├── commentsApi.ts
│   │   ├── azureDevOpsApi.ts
│   │   ├── usersApi.ts
│   │   └── activityLogApi.ts
│   └── styles/                       # Global styles + responsive breakpoints
└── tests/
    ├── components/                    # Component-level tests (calendar, board, forms, comment composer)
    └── integration/                    # User-story-level flow tests (login+role gating, create meeting,
                                         # assign task, drag task, post comment/mention/ADO, manage people)
```

**Structure Decision**: Standard two-project "web application" layout — `backend/` (FastAPI,
layered per constitution Principle III) and `frontend/` (React, component + service/hook
architecture per constitution Principle II) — communicating exclusively over the REST contracts
defined in `contracts/`. New `integrations/` (email, Azure DevOps) and `deps/` (auth/Role/Owner
guards) modules on the backend, and new Login/People/Activity Log/Task Details surfaces on the
frontend, are additive to this same structure — no deviation from the constitution's Technology
Stack section (React, FastAPI, SQLite, REST) was required to accommodate the full BRD scope.

**2026-09-15 revert — documents regenerated**: `research.md`, `data-model.md`,
`contracts/auth-api.md`, `contracts/users-api.md`, and `quickstart.md` have been regenerated against
this plan to restore the Employee Mail ID/Password + Admin-creates-accounts model (including the new
Terms-and-Conditions acceptance flag) and the original local, file-based SQLite storage approach —
both the 2026-09-14 Google Sign-In/Firebase and MongoDB amendments are fully reverted. The
already-implemented code (User Stories 1–5) has been migrated back to SQLAlchemy/SQLite accordingly.

## Complexity Tracking

> Not applicable — no Constitution Check violations were identified in this plan.
