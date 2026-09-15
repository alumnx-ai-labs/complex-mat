---

description: "Task list template for feature implementation"
---

# Tasks: Meeting Action Tracker (MAT)

**Input**: Design documents from `/specs/001-meeting-action-tracker/`

**Source of the user story below**: Azure DevOps work item **#176** — "MAT US4: Team Member Tracks
and Updates Their Own Tasks" (tags: `MAT; meeting-action-tracker; spec-001; US4`; parent #172),
retrieved via the `azure-devops` MCP server. Its Description and Acceptance Criteria fields are
quoted verbatim below and are the sole source of the story/goal/acceptance-criteria content in this
file — spec.md's own (differently-worded) User Story 4 section was **not** used for that content.
Everything else needed to make tasks executable (existing file paths, naming conventions, the
`Task` entity shape, and API contract shapes) still comes from this repo's plan.md, data-model.md,
and contracts/, since ADO work item #176 does not itself specify those.

**Scope of this file**: Only this one story. No Setup/Foundational phase and no other user stories
are included.

**ADO Work Item #176 — Description** (verbatim): "As a Team Member, I want to see and update my
assigned tasks across accessible meetings so that I can manage my action items without changing
task ownership details." Priority: P2.

**ADO Work Item #176 — Acceptance Criteria** (verbatim, numbered as in ADO):

1. My Tasks shows every task assigned to the current Team Member across accessible meetings,
   labelled with its meeting name.
2. My Tasks and a meeting's Task Board use exactly To Do, In Progress, and Completed columns.
3. The Team Member can drag their own task or use a direct status control to update status
   immediately; counts and other permitted views reflect the change.
4. A Team Member cannot change the status of another person's task.
5. The assignee can edit only their own task's Description/Notes; Title, Due Date, and Assignee
   remain unchanged and uneditable by them.
6. The assignee cannot delete their task, and completed tasks remain visible in Completed.

**Prerequisites already satisfied in the codebase** (User Stories 1 & 2 are implemented on this
branch): auth (`backend/app/deps/auth.py`, JWT), the `User` model/repository, and the `Meeting`
model/repository/service/router.

**Known cross-story gap**: No `Task` model/table exists yet anywhere in the codebase on this branch.
None of ADO #176's six acceptance criteria can be met without one, so this phase includes the
minimal `Task` model, schema, and repository needed to satisfy them — status updates, description
edits, and the My Tasks listing only. It does not add task creation, deletion, or Owner/Admin-editable
fields, since ADO #176 does not ask for those (its AC5/AC6 explicitly keep Title/Due Date/Assignee
and deletion out of the Assignee's reach, not build them). Tests seed `Task` rows directly against
the repository/DB rather than via a create endpoint.

**Tests**: Included, one per acceptance criterion above, following this codebase's existing
contract/integration test structure.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[US4]**: All tasks below belong to ADO #176 / US4
- Exact file paths are included in each description

---

## Phase: US4 - Team Member Tracks and Updates Their Own Tasks (ADO #176, Priority: P2)

**Goal** (ADO #176 Description): A Team Member can see and update their assigned tasks across
accessible meetings without changing task ownership details.

**Independent Test**: Seed a task assigned to a Team Member, sign in as that member, open My Tasks,
change the task's status by drag or direct control, edit its Description/Notes, and confirm Title,
Due Date, and Assignee stay unchanged and there is no delete control (ADO #176 AC1–AC6).

### Backend

- [X] T001 [P] [US4] Create `Task` model and `TaskStatus` enum (`TODO`, `IN_PROGRESS`, `COMPLETED`
  — AC2) in `backend/app/models/task.py`, per the Task entity table in
  [data-model.md](./data-model.md#task): `id`, `meeting_id` (FK → meetings), `title`,
  `description_notes`, `assignee_id` (FK → users), `due_date`, `status`, `needs_reassignment`,
  `created_at`.
- [X] T002 [P] [US4] Create Task DTOs in `backend/app/schemas/task.py` using the existing
  `CamelModel` pattern (see `backend/app/schemas/meeting.py`): `TaskResponse`;
  `TaskWithMeetingResponse` (includes `meetingTitle` so each card can be "labelled with its meeting
  name" — AC1); `TaskStatusUpdateRequest` (`status`); `TaskDescriptionUpdateRequest`
  (`description_notes`).
- [X] T003 [US4] Create `TaskRepository` in `backend/app/repositories/task_repository.py`
  (depends on T001): `get_by_id(task_id)`, `list_by_assignee(user_id)` (joins `Meeting` for its
  title — AC1), `update_status(task, status)`, `update_description_notes(task, description_notes)`.
- [X] T004 [US4] Create `backend/app/services/task_service.py` (depends on T003):
  `list_my_tasks(db, current_user)` — AC1; `update_task_status(db, current_user, task_id, status)`
  — raises `ForbiddenError` unless `current_user.id == task.assignee_id` (AC3, AC4), `NotFoundError`
  if missing, `ValidationFailedError` if `status` isn't one of the three enum values;
  `update_task_description(db, current_user, task_id, description_notes)` — same 403/404 rules,
  changing only `description_notes` (AC5). Reuse `app.core.exceptions` exactly as
  `meeting_service.py` does.
- [X] T005 [US4] Create `backend/app/api/tasks.py` (depends on T004), mirroring
  `backend/app/api/meetings.py`'s router/response-mapping style: `GET /api/tasks/mine` →
  `list[TaskWithMeetingResponse]` (AC1); `PATCH /api/tasks/{task_id}/status` → `TaskResponse`
  (AC3, AC4); `PATCH /api/tasks/{task_id}` → `TaskResponse`, accepting only `description_notes`
  from the body — any other field present (`title`, `dueDate`, `assigneeId`) → `403` (AC5). No
  `DELETE` route is added (AC6). All routes depend on `get_current_user` only — no role
  restriction, since the Assignee may be either Role.
- [X] T006 [US4] Register `tasks_router` in `backend/app/main.py` (depends on T005), following the
  existing `auth_router`/`meetings_router`/`users_router` `include_router` pattern.
- [X] T007 [P] [US4] Add `make_meeting` and `make_task` fixtures to `backend/tests/conftest.py`,
  following the existing `make_user`/`auth_header` fixture style, so tests can seed a `Meeting`
  (with attendees) and a `Task` (assigned to one of those attendees) directly, without a
  create-task endpoint.
- [X] T008 [P] [US4] Contract test in `backend/tests/contract/test_tasks_mine.py` for AC1: a Team
  Member sees only their own tasks, each with `meetingTitle`; a task assigned to someone else never
  appears.
- [X] T009 [P] [US4] Contract test in `backend/tests/contract/test_tasks_status.py` for AC2–AC4:
  the assignee can `PATCH /api/tasks/{id}/status` through all three status values (`TODO` /
  `IN_PROGRESS` / `COMPLETED`) and the change persists; a non-assignee (including the meeting's
  Owner/Admin) gets `403`; an invalid status value gets `422`.
- [X] T010 [P] [US4] Contract test in `backend/tests/contract/test_tasks_update.py` for AC5: the
  assignee can `PATCH /api/tasks/{id}` with `descriptionNotes` and it saves; the same request also
  containing `title`/`dueDate`/`assigneeId` is rejected with `403` and none of those fields change.
- [X] T011 [US4] Integration test in `backend/tests/integration/test_my_tasks_workflow.py`
  (depends on T007–T010) covering AC1, AC3, AC5, AC6 end-to-end against the `TestClient`: seed a
  meeting + task assigned to a Team Member, confirm My Tasks scoping, status change via the status
  endpoint, description edit, and that a `COMPLETED` task remains visible in the Completed column
  afterward.

### Frontend

- [X] T012 [P] [US4] Create `frontend/src/services/tasksApi.ts` (mirroring
  `frontend/src/services/meetingsApi.ts`'s `apiRequest` usage): `TaskWithMeeting` type,
  `listMyTasks()`, `updateTaskStatus(taskId, status)`, `updateTaskDescription(taskId,
  descriptionNotes)`.
- [X] T013 [P] [US4] Create `frontend/src/hooks/useTasks.ts` (mirroring
  `frontend/src/hooks/useMeetings.ts`'s `refresh`/`isLoading`/`error` shape): `useMyTasks()`
  returning `{ tasks, isLoading, error, refresh, updateStatus, updateDescription }`, calling
  `refresh()` after each mutation so counts stay in sync (AC3).
- [X] T014 [P] [US4] Create `frontend/src/components/tasks/TaskCard.tsx`: renders title, meeting
  name label (AC1), due date, description snippet; draggable via `@dnd-kit/core` only when the
  signed-in user is the task's assignee (AC4); no delete control ever rendered (AC6).
- [X] T015 [P] [US4] Create `frontend/src/components/tasks/TaskColumn.tsx`: one status column —
  exactly To Do / In Progress / Completed (AC2) — as a `@dnd-kit/core` droppable region with a
  live task count in its header.
- [X] T016 [US4] Create `frontend/src/components/tasks/TaskBoard.tsx` (depends on T014, T015):
  composes the three `TaskColumn`s under a `@dnd-kit/core` `DndContext`; on drop, calls
  `updateStatus` only for the current user's own cards; also exposes a direct status `<select>`
  per card as the non-drag alternative (AC3).
- [X] T017 [US4] Create `frontend/src/components/tasks/TaskEditModal.tsx`: edits only
  Description/Notes for the current user's own task; Title/Due Date/Assignee are rendered
  read-only, not as editable inputs (AC5).
- [X] T018 [US4] Implement `frontend/src/pages/MyTasksPage.tsx` (depends on T013, T016, T017),
  replacing the current `<PlaceholderPage title="My Tasks" />`: fetches via `useMyTasks()`, renders
  `TaskBoard`, opens `TaskEditModal` for a selected card.
- [X] T019 [US4] Update `frontend/src/routes/router.tsx` (depends on T018): swap the `/my-tasks`
  route's `<PlaceholderPage title="My Tasks" />` for `<MyTasksPage />` inside its existing
  `RequireAuth` wrapper.
- [X] T020 [P] [US4] Component test in `frontend/tests/components/TaskBoard.test.tsx` for AC3/AC4:
  dragging a card the user owns calls the status-update handler; dragging a card the user does not
  own is a no-op.
- [X] T021 [P] [US4] Integration test in `frontend/tests/integration/myTasks.test.tsx` (depends on
  T019) for AC1, AC5, AC6: signed-in Team Member sees only their own tasks labelled by meeting,
  edits Description/Notes successfully, and sees no delete control.

**Checkpoint**: All six of ADO #176's acceptance criteria are satisfied — a seeded task can be
status-changed and description-edited only by its assignee, My Tasks is correctly scoped, and
Completed tasks stay visible.

---

## Dependencies & Execution Order

- T001 and T002 have no dependencies on each other and can start immediately; both block T003.
- T003 blocks T004; T004 blocks T005; T005 blocks T006.
- T007 can be written as soon as T001 exists; it blocks T008–T011.
- T008, T009, T010 can run in parallel once T006 and T007 are done; T011 depends on all three.
- T012 and T013 have no dependencies on each other; T013 depends on T012.
- T014 and T015 have no dependencies on each other; both block T016.
- T016 and T017 block T018; T018 blocks T019.
- T020 depends on T016; T021 depends on T019.
- Frontend tasks do not block backend tasks or vice versa, but a working backend (through T006) is
  needed for T021's integration test to pass against a live API in CI.

## Parallel Example: US4 (ADO #176)

```bash
# Backend model/schema, in parallel:
Task: "Create Task model and TaskStatus enum in backend/app/models/task.py"
Task: "Create Task DTOs in backend/app/schemas/task.py"

# Frontend leaf components, in parallel:
Task: "Create TaskCard component in frontend/src/components/tasks/TaskCard.tsx"
Task: "Create TaskColumn component in frontend/src/components/tasks/TaskColumn.tsx"

# Backend contract tests, in parallel, once the router is registered:
Task: "Contract test for GET /api/tasks/mine (AC1) in backend/tests/contract/test_tasks_mine.py"
Task: "Contract test for PATCH /api/tasks/{id}/status (AC2-AC4) in backend/tests/contract/test_tasks_status.py"
Task: "Contract test for PATCH /api/tasks/{id} (AC5) in backend/tests/contract/test_tasks_update.py"
```

## Implementation Strategy

1. Backend: T001 → T002 → T003 → T004 → T005 → T006, then T007 → (T008, T009, T010 in parallel) →
   T011.
2. Frontend: (T012, T013) then (T014, T015 in parallel) → T016 → T017 → T018 → T019, then (T020,
   T021 in parallel).
3. **Stop and validate** against all six acceptance criteria of ADO work item #176 before
   considering this story done.

---

## Phase 2: Convergence

Appended by `/speckit-converge`, assessing the full `spec.md`/`plan.md` (all 10 user stories, 44
FRs, 10 SCs) against the current codebase — not just the User Story 4 scope of Phase 1 above. Two
items (T022, T023) are partial gaps on already-shipped User Story 4 work; the rest are entire
user stories (3, 5–10) with no implementation yet. Ordered HIGH severity first, then MEDIUM; no
CRITICAL (constitution) violations were found. See the in-session Convergence Findings table
(F1–F19) for full evidence per item.

- [ ] T022 Embed the Task list in `GET /api/meetings/{meeting_id}` (extend `MeetingDetailResponse`
  in `backend/app/schemas/meeting.py` and `_to_detail` in `backend/app/api/meetings.py`) and render
  it read-only on `frontend/src/pages/MeetingDetailsPage.tsx`, so a status/description change made
  from My Tasks is visible from the meeting's own Task Board per FR-043, SC-005,
  [meetings-api.md](./contracts/meetings-api.md) (partial)
- [ ] T023 Extend `PATCH /api/tasks/{task_id}` (`backend/app/api/tasks.py`,
  `backend/app/services/task_service.py`) to support the Meeting-Owner-editable
  (`title`/`dueDate`/`assigneeId`, validated against attendees) and other-Admin-editable
  (`title`/`dueDate`) field paths, replacing today's unconditional 403 on those fields, per
  FR-016, FR-017, [tasks-api.md](./contracts/tasks-api.md) (partial)
- [ ] T024 Add `POST /api/meetings/{meeting_id}/tasks` (create Task) — new route in
  `backend/app/api/tasks.py`, `task_service.create_task`, `task_repository.create` — enforcing
  Meeting-Owner-only assignment and that the Assignee is an Attendee of the meeting, per FR-016,
  FR-017, FR-019 (missing)
- [ ] T025 Add `DELETE /api/tasks/{task_id}` — new route in `backend/app/api/tasks.py`,
  `task_service.delete_task` — Admin-only, never available to the Assignee, per FR-023, US3
  Acceptance Scenario 6 (missing)
- [ ] T026 Implement `needs_reassignment` flagging in `backend/app/services/user_service.py`
  (on deactivation) and `backend/app/services/meeting_service.py` (on Attendee removal) when a
  Task's Assignee is deactivated or removed from the Meeting's Attendee list, per FR-024 (missing)
- [ ] T027 Build the Meeting Owner's Task Board on `frontend/src/pages/MeetingDetailsPage.tsx`:
  an add-task form scoped to the meeting's Attendees, a per-task Assignee-reassignment control
  visible only to the Meeting Owner, and a delete control visible only to Admins, reusing
  `frontend/src/components/tasks/*` from Phase 1, per US3 Acceptance Scenarios 1–6 (missing)
- [X] T028 Add `Comment`/`CommentMention`/`TaskAdoReference` models in
  `backend/app/models/comment.py` and `GET`/`POST /api/tasks/{task_id}/comments` per
  [comments-api.md](./contracts/comments-api.md), enforcing that only the Meeting Owner, the
  Task's Assignee, or any Admin may post, per FR-027
- [X] T029 Add `@Name` mention search (`GET
  /api/meetings/{meeting_id}/attendees/mention-search`) and `@<number>` Azure DevOps token
  parsing into `TaskAdoReference` rows, disambiguated by letters vs. digits, per FR-028, FR-029,
  FR-030. Also applied to a Task's own `title`/`description_notes` (not just Comments) via
  `reference_service.sync_task_content_references`, called from `task_service.create_task`,
  `update_task`, and `update_task_description` — required by FR-030's "Title, Description/Notes,
  or Comments" wording and US5 Acceptance Scenario 4.
- [X] T030 Add `backend/app/integrations/azure_devops_client.py` (fail-soft `AzureDevOpsClient`)
  and `GET /api/azure-devops/suggestions` + `GET /api/tasks/{task_id}/ado-references` per
  [azure-devops-api.md](./contracts/azure-devops-api.md), per FR-031, FR-032, FR-033. `search()`
  resolves the typed digits as a direct work-item-ID lookup rather than a true prefix search,
  since the Azure DevOps REST API has no numeric-ID prefix search without the optional Search
  extension.
- [X] T031 Add a `CommentThread`/`MentionAdoInput`/`AdoReferenceList` component set and surface
  them from the existing `TaskEditModal` (Owner/Admin, opened from `MeetingDetailsPage`) and
  `MyTaskEditModal` (Assignee, opened from `MyTasksPage`) — both already function as this app's
  "Task Details" view (the Task's own Title/Description inputs also route through
  `MentionAdoInput` for the same "@" trigger) — per US5 Acceptance Scenarios 1–6, rather than
  building a separate `TaskDetailsPage`/route as originally sketched, since Task Board access
  already funnels through exactly the Owner/Admin/Assignee actors FR-027 permits.
- [ ] T032 Add `backend/app/integrations/email_sender.py` (`EmailSender` interface + SMTP
  implementation) and `backend/app/services/notification_service.py`, invoked via FastAPI
  `BackgroundTasks` on task-assignment, comment, and mention events, per FR-034, FR-035, FR-036,
  FR-037, FR-038 (missing)
- [ ] T033 Add `PATCH /api/meetings/{meeting_id}` and `DELETE /api/meetings/{meeting_id}` to
  `backend/app/api/meetings.py` + `meeting_service.py`, Admin-only (not Owner-restricted), with
  cascading Task deletion, per FR-012, FR-013 (missing)
- [ ] T034 Add `frontend/src/pages/EditMeetingPage.tsx` (new route) and a delete-meeting control
  on `MeetingDetailsPage.tsx`, both visible to any Admin, per US7 Acceptance Scenarios 1–4
  (missing)
- [ ] T035 Implement `frontend/src/pages/PreviousMeetingsPage.tsx` (replacing its
  `PlaceholderPage`), listing meetings via the existing `GET /api/meetings` with title/date/task
  count and a link into Meeting Details, per FR-039 (missing)
- [ ] T036 Add `POST /api/users`, `PATCH /api/users/{user_id}/role`, `PATCH
  /api/users/{user_id}/password`, `PATCH /api/users/{user_id}/active` to
  `backend/app/api/users.py` + `user_service.py`, per [users-api.md](./contracts/users-api.md),
  FR-004, FR-005, FR-006 (missing)
- [ ] T037 Implement Meeting-Owner transfer to `WorkspaceSettings.default_admin_user_id` when a
  Meeting Owner is deactivated, in `backend/app/services/user_service.py`, per FR-040 (missing)
- [ ] T038 Implement `frontend/src/pages/PeoplePage.tsx` (replacing its `PlaceholderPage`) with
  `MemberTable`/`AddMemberModal`/`RoleSelect` components, per US9 Acceptance Scenarios 1–6
  (missing)
- [ ] T039 Add `GET /api/activity-log` in a new `backend/app/api/activity_log.py`, Admin-only,
  per [activity-log-api.md](./contracts/activity-log-api.md), FR-041 (missing)
- [ ] T040 Implement `frontend/src/pages/ActivityLogPage.tsx` (replacing its `PlaceholderPage`)
  rendering actor/action/timestamp rows from `GET /api/activity-log`, per US10 Acceptance
  Scenarios 1–3 (missing)

---

## Phase 3: Convergence

Appended by `/speckit-converge`, assessing the 2026-09-15 BA amendment to `spec.md`/`plan.md`/
`data-model.md`/`contracts/` (database engine switched from SQLite to MongoDB; Login now requires
an "I agree to the Terms and Conditions" checkbox) against the codebase at the time. The
constitution was amended to v3.0.0 to authorize the MongoDB switch and T041–T048 were appended
below to track that migration.

**2026-09-15, later the same day — MongoDB reverted**: after T041–T048 were actually implemented
end-to-end (full MongoDB/pymongo migration, `mongomock`-based tests, frontend `string` ids, 97
backend + 18 frontend tests passing), a direct product decision was made to stay on SQLite instead.
The constitution was amended again to v4.0.0, reverting the v3.0.0 Database line back to "a local,
file-based database"; `spec.md`, `plan.md`, `data-model.md`, and `research.md` were updated to
match; and the codebase (backend and frontend) was migrated back to SQLAlchemy/SQLite with integer
ids throughout. **T041–T048 are cancelled** — do not implement them; SQLite/SQLAlchemy is the
target state going forward, not MongoDB. The FR-011/FR-026 "display name or email address" wording
change was confirmed wording-only (matches existing `employee_name`/`employee_id` search behavior)
and has no task.

### Database: SQLite → MongoDB — CANCELLED, do not implement

- [ ] ~~T041 Replace `backend/app/db/session.py`'s SQLAlchemy engine/`Session` with a MongoDB
  client~~ — cancelled 2026-09-15; SQLite/SQLAlchemy remains the storage engine
- [ ] ~~T042 Rewrite `backend/app/models/*.py` as MongoDB document schemas~~ — cancelled
  2026-09-15; models stay SQLAlchemy declarative models with integer ids
- [ ] ~~T043 Rewrite `backend/app/repositories/*.py` for MongoDB collections~~ — cancelled
  2026-09-15
- [ ] ~~T044 Update service/deps ID handling to MongoDB ObjectId/`str`~~ — cancelled 2026-09-15;
  ids stay `int`
- [ ] ~~T045 Update schema DTOs' id fields from `int` to `str`~~ — cancelled 2026-09-15
- [ ] ~~T046 Replace SQLite test fixtures with a MongoDB test double~~ — cancelled 2026-09-15; the
  in-memory SQLite `conftest.py` fixtures remain
- [ ] ~~T047 Add a MongoDB driver to requirements.txt, remove sqlalchemy~~ — cancelled 2026-09-15;
  `sqlalchemy` stays, no MongoDB driver was added
- [ ] ~~T048 Update frontend id types from `number` to `string`~~ — cancelled 2026-09-15; ids stay
  `number` throughout the frontend

### Login: "I agree to the Terms and Conditions"

- [X] T049 Add a `terms_accepted` column to the `User` model, per data-model.md and FR-046 —
  implemented on the SQLAlchemy `User` model (superseded by Phase 4's T053/T055)
- [X] T050 Update `POST /api/auth/login` to require `termsAccepted: true` in the request body
  (`422` otherwise) and set the account's `termsAccepted` flag on a successful sign-in, per
  FR-045, FR-046, [auth-api.md](./contracts/auth-api.md) — implemented (superseded by Phase 4's
  T055/T056)
- [X] T051 Add a required "I agree to the Terms and Conditions" checkbox to
  `frontend/src/pages/LoginPage.tsx` that disables sign-in on both options until checked, per
  FR-045 — implemented (superseded by Phase 4's T060)

---

## Phase 4: US1 - Sign In and Reach the Shared Workspace (Priority: P1)

Generated by `/speckit-tasks`, using BRD.docx, mockup.html, and the current `spec.md` as the
source of truth for User Story 1 only. `mockup.html`'s `#screen-login` already reflects the
current spec (a `login-terms` checkbox with `toggleSignInEnabled()` disabling `login-signin-btn`
until checked), confirming FR-045/FR-046 are current, not stale.

**Goal**: A person signs in with the Employee Mail ID/Password an Admin gave them (Team Member or
Admin option, same underlying check), only after agreeing to the Terms and Conditions, and lands
in the workspace matching their account's actual stored Role — against the SQLAlchemy/SQLite-backed
`User` table per data-model.md.

**Independent Test** (spec.md): An Admin creates one Team Member account and one Admin account
from the People screen, then signs in with each set of credentials — via either sign-in option —
confirming Admin-only screens/actions are unavailable for the Team Member and available for the
Admin.

**Already satisfied, no task needed**: AC3/AC4 (Role-gated navigation) — `RequireAdmin`/
`RequireAuth` in `frontend/src/routes/router.tsx` already gate People/Activity Log/Create Meeting
by `user.role`. AC5 (no sign-up form) — no registration route exists anywhere in the app.

**2026-09-15 update — MongoDB reverted**: T052, T054, and T057 originally called for migrating the
`User` model/repository/JWT-id-handling to MongoDB; that migration was implemented, then reverted
the same day when the product decision was made to stay on SQLite (see Phase 3's note and
constitution v4.0.0). They are now marked **cancelled**, not done and not blocked — the
SQLAlchemy `User` model, `UserRepository`, and integer-id JWT handling are the permanent target
state. T053/T058's "partial" caveats about `id: str`/`token_type` are likewise resolved: those
Mongo-only fields are correctly absent, not a gap.

### Backend

- [ ] ~~T052 [P] [US1] Rewrite the `User` model as a MongoDB document schema~~ — cancelled
  2026-09-15; delivered instead as a `terms_accepted` column on the SQLAlchemy `User` model
  (`backend/app/models/user.py`)
- [X] T053 [P] [US1] Update `backend/app/schemas/auth.py` (`LoginRequest.terms_accepted: bool`,
  required) and `backend/app/schemas/user.py` (`UserResponse.terms_accepted: bool`), per
  [auth-api.md](./contracts/auth-api.md) (FR-045, FR-046)
- [ ] ~~T054 [US1] Rewrite `user_repository.py` for MongoDB~~ — cancelled 2026-09-15; delivered
  instead as `UserRepository.mark_terms_accepted(user)` on the existing SQLAlchemy repository
- [X] T055 [US1] Update `backend/app/services/auth_service.login` to accept `terms_accepted`,
  raise `ValidationFailedError` (422) when it is not `True`, and persist acceptance on a
  successful sign-in, per FR-045, FR-046
- [X] T056 [US1] Update `backend/app/api/auth.py`'s `login` handler to pass `terms_accepted`
  through to `auth_service.login`
- [ ] ~~T057 [P] [US1] Update JWT `sub`/lookup to a MongoDB `str` id~~ — cancelled 2026-09-15;
  ids stay SQLAlchemy integers throughout `deps/auth.py` and `core/security.py`

### Frontend

- [X] T058 [P] [US1] Update `frontend/src/services/authApi.ts`
  (`AuthUser.termsAccepted: boolean`, `login(employeeMailId, password, termsAccepted)`) per
  [auth-api.md](./contracts/auth-api.md) — `AuthUser.id` correctly stays `number`
- [X] T059 [US1] Update `frontend/src/context/AuthContext.tsx`'s `login` to accept and forward
  `termsAccepted`
- [X] T060 [US1] Add the "I agree to the Terms and Conditions" checkbox to
  `frontend/src/pages/LoginPage.tsx` (mirroring `mockup.html`'s `#login-terms`), disabling the
  Sign In button on both sign-in options until checked, per FR-045

### Tests

- [X] T061 [P] [US1] Extend `backend/tests/contract/test_auth_login.py` for AC1, AC2, AC6, AC7:
  login succeeds only with `termsAccepted: true` (422 otherwise, including when the field is
  missing entirely), sets the account's `terms_accepted` flag on success (verified via `/me`),
  and still rejects wrong/deactivated credentials with 401
- [X] T062 [P] [US1] Extend `backend/tests/contract/test_auth_me.py` for the `termsAccepted`
  response field
- [X] T063 [P] [US1] Extend `frontend/tests/components/LoginPage.test.tsx`: Sign In stays
  disabled until the Terms and Conditions checkbox is checked, re-enables/disables as it's
  toggled, and the existing login/error tests now check the box first

**Checkpoint**: All seven of User Story 1's acceptance scenarios are satisfied on the
SQLAlchemy/SQLite stack — 97 backend + 18 frontend tests pass. Nothing in this phase remains open;
T052/T054/T057 are cancelled, not deferred.

## Dependencies & Execution Order (Phase 4)

- T053 has no dependencies and can start immediately.
- T055 depends on T053; T056 depends on T055.
- T058 has no backend dependency; T059 depends on T058; T060 depends on T059.
- T061 and T062 depend on T056; T063 depends on T060.

## Parallel Example: US1

```bash
# Backend model/schema, in parallel:
Task: "Add terms_accepted to the User model in backend/app/models/user.py"
Task: "Update LoginRequest/LoginResponse/UserResponse schemas for termsAccepted"

# Frontend and backend test extensions, in parallel once their dependencies land:
Task: "Extend backend/tests/contract/test_auth_login.py for the Terms-and-Conditions gate"
Task: "Extend frontend/tests/components/LoginPage.test.tsx for the Terms-and-Conditions gate"
```
