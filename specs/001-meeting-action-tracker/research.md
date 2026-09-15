# Phase 0 Research: Meeting Action Tracker (MAT)

Most technology choices are fixed by the ratified project constitution (React, FastAPI, local
database, REST). This phase resolves the concrete patterns needed to deliver the full BRD scope —
authentication/RBAC, Meeting Owner enforcement, comments/@mentions, Azure DevOps referencing, and
email notifications — on top of that stack. No `[NEEDS CLARIFICATION]` markers remain.

## 1. Local database engine

- **Decision**: SQLite, accessed through SQLAlchemy, as a single file under the backend project
  (e.g., `backend/mat.db`).
- **Rationale**: The constitution specifies a "local, file-based database." SQLite requires no
  separate server process and is sufficient for this scope's data volume; SQLAlchemy gives the
  repository layer a clean, swappable data-access boundary if a heavier database is needed later.
  *(A 2026-09-14 amendment briefly switched this decision to MongoDB; it was reverted on
  2026-09-15 back to SQLite, per constitution v4.0.0.)*
- **Alternatives considered**: A client/server database (PostgreSQL) — rejected as an unnecessary
  deployment dependency for the constitution's "local database" framing at this scale; MongoDB — a
  brief 2026-09-14 amendment, reverted 2026-09-15 (no benefit over SQLite/SQLAlchemy at this
  scope, and it would have forced every entity id from an integer to a string across the whole
  stack for no functional gain).

## 2. Backend web framework structure

- **Decision**: FastAPI with the layered structure Router → Service → Repository → SQLAlchemy
  models, using Pydantic models as the DTO layer at the router boundary.
- **Rationale**: Directly mandated by constitution Principle III. FastAPI's dependency-injection
  system (`Depends`) is used both for repository/service wiring and for the authentication/role
  guards described in item 3 below.
- **Alternatives considered**: N/A — framework is fixed by the constitution.

## 3. Authentication and role enforcement

- **Decision** *(2026-09-15 revert)*: Employee Mail ID/Password credentials, verified by the
  backend itself. Passwords are hashed with `passlib`/`bcrypt` (never stored or logged in
  plaintext). `POST /api/auth/login` (see [auth-api.md](./contracts/auth-api.md)) validates the
  submitted Employee Mail ID/Password against the stored `password_hash`, rejects a deactivated
  account, records `terms_accepted = true` on the matched account when the request confirms the
  Terms-and-Conditions checkbox was checked (FR-046), and returns a signed JWT (`python-jose`)
  whose access token is the API's bearer credential thereafter. Every other endpoint's
  `get_current_user` dependency verifies that JWT and resolves the `User` it identifies.
  `require_role(Role.ADMIN)` and a `require_meeting_owner` dependency wrap `get_current_user` for
  Admin-only and Owner-only routes respectively. There is no self-registration endpoint; accounts
  exist only via `POST /api/users` (Admin-only, People "Add Member" — see
  [users-api.md](./contracts/users-api.md)).
- **Rationale**: Constitution Principle V and spec.md's 2026-09-15 amendment restore the BRD's
  original Employee Mail ID/Password + Admin-provisioned-account model, reverting the interim
  2026-09-14 Google Sign-In/Firebase auto-provisioning change. Principle VII still requires these
  rules enforced in the backend, not just hidden UI controls. Distinguishing "Role" from "Meeting
  Owner" is unchanged from the original decision.
- **Alternatives considered**: Re-adopting Google Sign-In/Firebase Authentication — rejected, since
  the 2026-09-15 amendment explicitly reverts it; a server-side session store instead of a JWT —
  rejected as unnecessary added infrastructure at this scale, when a signed, short-lived JWT already
  satisfies "authentication required end-to-end" without a session table.

## 4. Frontend auth/session state

- **Decision** *(2026-09-15 revert)*: A React Context (`AuthContext`) holding the signed-in user and
  the JWT returned by `POST /api/auth/login` (obtained via `authApi.ts`), backed by
  `sessionStorage` so a reload keeps the session but closing the tab/browser ends it. The Login
  screen renders visually separate Team Member/Admin sign-in options, Employee Mail ID and Password
  fields, and an "I agree to the Terms and Conditions" checkbox that keeps the Sign In control
  disabled until checked (FR-045); both options submit to the same `POST /api/auth/login`, and the
  account's actual stored Role — not the option clicked — determines access (FR-002). Route guards
  are unchanged (unauthenticated → Login; Admin-only routes hidden/redirected for Team Members).
- **Rationale**: Centralizes "who is signed in and with what Role" in one place, unchanged from the
  original rationale; keeping the login form's HTTP call inside `authApi.ts` (constitution
  Principle II) is what lets tests mock login without a real network call.
- **Alternatives considered**: `localStorage` for the token — rejected in favor of `sessionStorage`,
  unchanged from the original decision.

## 5. Meeting Owner vs. Admin role enforcement

- **Decision**: `Meeting.owner_id` is set once, at creation, to the creating Admin's user id, and is
  never directly editable by any endpoint. Two independent backend checks exist: (a) "is an Admin"
  (Role check) gates create/edit/delete-meeting and most Task fields; (b) "is this meeting's Owner"
  (ownership check) additionally gates only the Task-Assignee field. A request from an Admin who is
  not the Owner attempting to set/change `Task.assignee_id` is rejected with 403 even though the
  same Admin can edit every other field on that meeting/task.
- **Rationale**: The BRD is explicit that "Admins may edit or delete any Meeting or Task
  workspace-wide, except changing a Task's Assignee" — this is a narrower, per-meeting authority
  layered on top of the Admin role, not a role of its own, so it cannot be modeled as a third Role
  value.
- **Alternatives considered**: Modeling "Meeting Owner" as a role — rejected, since it is per-meeting
  and every Admin can hold it for meetings they create, which a single global Role field cannot
  express.

## 6. Comment posting permissions, @mentions, and Azure DevOps reference detection

- **Decision**: A single regex-based parser runs over a Task's `title`, `description_notes`, and
  each `Comment.message` whenever they are written: a token matching `@[A-Za-z][\w]*` is treated as
  a member-mention candidate (resolved against that meeting's Attendees by display name), and a
  token matching `@\d+` is treated as an Azure DevOps reference candidate (the digits are the work
  item ID). Mentions are stored as normalized `(comment_id_or_task_id, mentioned_user_id)` rows at
  write time (for reliable notification and to avoid re-parsing on every read); Azure DevOps
  references are stored as normalized `(task_id, ado_id)` rows at write time, but their display
  title/type/availability is refreshed from the Azure DevOps API at read time (with a short cache)
  since that state can change outside MAT. Posting a comment is allowed only for the Task's parent
  Meeting's Owner, the Task's Assignee, or any Admin — enforced in the comment service before the
  parser ever runs.
- **Rationale**: Storing mentions/references at write time makes "who to notify" and "what's linked"
  cheap to query without re-parsing text on every request, while re-checking Azure DevOps
  availability at read time is what makes the "unavailable indicator" (FR-032) accurate even when an
  item is deleted after the reference was created. Digits-vs-letters immediately after `@` is the
  single disambiguation rule the BRD specifies, so one parser serves both concerns.
- **Alternatives considered**: Parsing only at read time — rejected, since notifying a mentioned
  member (FR-036) must happen once, at write time, not on every future read of the same comment.

## 7. Azure DevOps integration

- **Decision**: A dedicated `AzureDevOpsClient` service wraps the Azure DevOps REST API (work item
  lookup/search by ID and free-text, scoped by the connected organization/project) behind a small
  interface (`search(query, as_user)`, `get(work_item_id, as_user)`). All calls are wrapped so a
  timeout, auth failure, or non-2xx response from Azure DevOps is caught and translated into "no
  suggestions" or "unavailable" rather than propagating as a MAT-level error — satisfying "MAT
  remains usable if Azure DevOps is temporarily unavailable" (FR-033). Referencing a work item is
  strictly read-only: MAT never calls a create/update endpoint against Azure DevOps.
- **Rationale**: Isolating all Azure DevOps calls behind one client keeps the rest of the backend
  unaware of Azure DevOps-specific failure modes and makes the "read-only, never duplicates a work
  item" rule (FR-031) trivially true — there is simply no write method on the client to call.
- **Alternatives considered**: Calling the Azure DevOps SDK directly from the task service —
  rejected as it would spread external-API error handling and auth details across business logic,
  conflicting with constitution Principle IX (single clear responsibility per module).

## 8. Email notifications

- **Decision**: A `NotificationService` with one method per triggering event (task assigned, comment
  posted, mention made) that composes the message and hands it to an `EmailSender` interface (an
  SMTP-backed implementation for this project), invoked via FastAPI `BackgroundTasks` so the HTTP
  response for the triggering action (assign/comment/mention) is never delayed or failed by email
  delivery. A delivery failure is caught and logged inside the background task, never raised back
  into the request that triggered it.
- **Rationale**: Directly satisfies "email delivery failure never loses or blocks the underlying
  operation" (FR-038) — the triggering database write has already committed before the background
  email task runs. A single `NotificationService` entry point per event keeps "what to include in
  the email" (FR-037) defined in one place rather than duplicated at each call site.
- **Alternatives considered**: Sending email synchronously in the request path — rejected, since an
  SMTP timeout or error would then risk blocking or failing the task/comment/mention operation
  itself, directly violating FR-038.

## 9. Internal member search

- **Decision**: A simple case-insensitive substring query (SQL `LIKE`) over `employee_name` and
  `employee_id`, scoped to all active users for Attendee search and to a given meeting's Attendees
  for Assignee search — no full-text search engine. Spec.md FR-011/FR-026's "display name or email
  address" wording (from the 2026-09-14 amendment) was confirmed wording-only, not a behavior
  change — this search still matches `employee_name`/`employee_id`, not `employee_mail_id`.
- **Rationale**: Matches the BRD's description of a simple name/ID lookup at internal-workspace
  scale; a dedicated search engine would be disproportionate infrastructure for this data volume,
  conflicting with constitution Principle IX (avoid premature complexity).
- **Alternatives considered**: A dedicated search index (e.g., Elasticsearch) — rejected as
  unjustified complexity at this scale.

## 10. Meeting Owner continuity on deactivation

- **Decision** *(2026-09-15 revert)*: The workspace has exactly one configured "default Admin"
  (`WorkspaceSettings.default_admin_user_id`), set by a one-time seed step that creates the very
  first Admin account (Employee Name, Employee Mail ID, Employee ID, an initial Password, Role
  `ADMIN`) when the `users` collection is empty — since accounts are otherwise only ever created by
  an existing Admin via People "Add Member," something has to bootstrap the first one. Deactivating
  a user remains a single service-layer operation that, if that user owns any Meetings, reassigns
  `Meeting.owner_id` to the configured default Admin for every one of them, in the same transaction
  as the deactivation (FR-040; User Story 9's deactivation logic is not yet implemented).
- **Rationale**: The BRD requires automatic ownership transfer "to the workspace's configured
  default Admin" on Meeting-Owner deactivation (FR-040); with no self-registration or
  auto-provisioning path (2026-09-15 revert), a one-time seed step is the only way to bootstrap the
  first Admin/default Admin account.
- **Alternatives considered**: Auto-provisioning the first Admin from an external identity
  provider's first sign-in — rejected along with the rest of the 2026-09-14 Google
  Sign-In/Firebase amendment; leaving `owner_id` null until manually reassigned — rejected, since
  the BRD requires the transfer to be automatic, not a follow-up manual step.

## 11. Activity Log

- **Decision**: An append-only `ActivityLogEntry` collection, written by a single `log_activity(actor,
  action, entity_type, entity_id)` service-layer helper called at the end of each significant
  service method (meeting/task create-edit-delete, member auto-provisioned/role-change/deactivate,
  notification sent, mention made, Azure DevOps reference detected) — never written directly by a
  router.
- **Rationale**: A single helper, called from the service layer where the business action already
  succeeded, guarantees the log reflects what actually happened without duplicating logging logic
  per endpoint, and keeps routers free of business/audit logic per constitution Principle III.
- **Alternatives considered**: Deriving the Activity Log from a generic request-level middleware —
  rejected, since it cannot easily express "which business action" occurred (e.g., distinguishing a
  role change from a deactivation, both `PATCH /users/{id}`) as precisely as an explicit call site.

## 12. Frontend drag-and-drop and calendar

- **Decision**: A hand-built month-grid component (no calendar library) for Calendar/Create Meeting
  date selection, and a lightweight, actively-maintained drag-and-drop library (e.g.,
  `@dnd-kit/core`) for the Task Board/My Tasks columns, paired with an always-available non-drag
  status control on each card.
- **Rationale**: Unchanged from the original MVP research — the calendar and Kanban requirements
  themselves did not change in the full-BRD scope, only who may create/edit meetings and what a task
  carries.
- **Alternatives considered**: See original rationale — a calendar library and `react-beautiful-dnd`
  were both rejected as heavier than needed / unmaintained, respectively.

## 13. Testing approach

- **Decision**: Backend — pytest with FastAPI's `TestClient`, one contract test per endpoint plus
  integration tests per business rule and user story (including Role-gated and Owner-gated access,
  mention/Azure DevOps token disambiguation, and the notification-never-blocks-the-action guarantee,
  simulated by injecting a failing `EmailSender`). Frontend — Vitest + React Testing Library for the
  calendar, task board drag-and-drop, Role-gated navigation/UI, and the `@`-trigger
  mention-vs-Azure-DevOps-suggestion behavior in text inputs.
- **Rationale**: Matches constitution Principle X and the spec's Given/When/Then acceptance
  scenarios, which map directly onto integration tests, including the newly added Role/Owner and
  external-integration-resilience cases.
- **Alternatives considered**: End-to-end browser testing (e.g., Playwright) — not ruled out later,
  not required to satisfy Principle X at this scope.

**Addendum** *(2026-09-15)*: Both suites stay fully offline against fakes, matching the original
decision's spirit for external dependencies. Backend: the existing in-memory SQLite engine covers
the Terms-and-Conditions login flow too — JWTs are issued/verified against a fixed test signing
key with a fake `password_hash`/login fixture, no real external identity provider needed. Frontend:
`authApi.login` is mocked at the module boundary exactly like `meetingsApi`/`usersApi` already are,
including cases covering the Terms-and-Conditions checkbox disabling Sign In — no real backend call
ever runs under `vitest`/`jsdom`.
