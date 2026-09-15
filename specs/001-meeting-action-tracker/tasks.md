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
- [X] T032 Add `backend/app/integrations/email_sender.py` (`EmailSender` interface + SMTP
  implementation) and `backend/app/services/notification_service.py`, invoked via FastAPI
  `BackgroundTasks` on task-assignment, comment, and mention events, per FR-034, FR-035, FR-036,
  FR-037, FR-038 (partial: task-assignment notification (FR-034, FR-037, FR-038) implemented and
  wired into `POST /api/meetings/{meeting_id}/tasks` and `PATCH /api/tasks/{task_id}` reassignment
  in `backend/app/api/tasks.py`, with tests in
  `backend/tests/unit/test_notification_service.py` and
  `backend/tests/integration/test_task_assignment_notifications.py`. Comment-posted (FR-035) and
  mention-made (FR-036) notifications are still NOT implemented — T028/T029's Comment/mention
  feature now exists in the codebase (merged from upstream), but its comment-posted and
  mention-made events are not yet wired to `notification_service`.)
- [X] T033 Add `PATCH /api/meetings/{meeting_id}` and `DELETE /api/meetings/{meeting_id}` to
  `backend/app/api/meetings.py` + `meeting_service.py`, Admin-only (not Owner-restricted), with
  cascading Task deletion, per FR-012, FR-013. `PATCH` never accepts `ownerId` (AC4); removing an
  Attendee who is a Task's Assignee flags `needsReassignment` instead of reassigning (AC2). `DELETE`
  cascades through each Task's Comments/CommentMentions/TaskAdoReferences before deleting the Task
  (`task_service.delete_tasks_for_meeting`, new repository `delete`/`delete_by_task` helpers on
  `CommentRepository`/`AdoReferenceRepository`/`MeetingRepository`), then the Meeting, recorded as
  one `MEETING_DELETED` Activity Log entry (AC3). Tests:
  `backend/tests/contract/test_meetings_update.py`, `backend/tests/contract/test_meetings_delete.py`.
- [X] T034 Add `frontend/src/pages/EditMeetingPage.tsx` (new route
  `/meetings/:meetingId/edit`, `RequireAdmin`) and Edit/Delete Meeting controls on
  `MeetingDetailsPage.tsx`, both visible to any Admin (not Owner-restricted), per US7 Acceptance
  Scenarios 1–4. Reuses the existing `MeetingForm` (with `dateEditable`) from Create Meeting; Delete
  prompts a native confirm before calling `DELETE` and navigating back to Calendar. Test:
  `frontend/tests/integration/editDeleteMeeting.test.tsx`.
- [X] T035 Implement `frontend/src/pages/PreviousMeetingsPage.tsx` (replacing its
  `PlaceholderPage`), listing meetings via the existing `GET /api/meetings` with title/date/task
  count and a link into Meeting Details, per FR-039. Table layout (Title/Date/Meeting
  Owner/Tasks/Open) follows `mockup.html`'s Previous Meetings screen; matching `table`/`th`/`td`
  styles added to `frontend/src/styles/global.css`. Fixed a bug found along the way:
  `MeetingSummaryResponse.task_count` in `backend/app/api/meetings.py`'s `_to_summary` was
  hardcoded to `0` (affects `GET /api/meetings`, which this page and Calendar both consume) — now
  computed from `TaskRepository.list_by_meeting`, satisfying AC1/AC3's "current task count"
  requirement. Tests: `backend/tests/contract/test_meetings_list.py` (task-count case),
  `frontend/tests/integration/previousMeetings.test.tsx`.
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

---

## Phase 5: US9 - Admin Manages Member Accounts, Roles, and Access (Priority: P3)

Generated by `/speckit-tasks`, using BRD.docx, mockup.html, and the current `spec.md` as the
source of truth for User Story 9 only.

**Goal**: An Admin adds new member accounts, changes an existing member's Role, resets their
Password, and deactivates/reactivates them from the People screen — the only way any account
(beyond the seeded first Admin) comes into existence, since there is no self-registration.

**Independent Test** (spec.md): An Admin adds a new member from the People screen, confirms that
member can sign in with the given credentials, changes their Role and resets their Password, then
deactivates them and confirms they can no longer sign in or appear in attendee/assignee search.

**Already satisfied, no task needed**: AC1 (People hidden from Team Members) —
`frontend/src/routes/router.tsx`'s `/people` route is already wrapped in `RequireAdmin`, and
`GET /api/users` already requires `require_role(ADMIN)`.

### Backend

- [X] T064 [P] [US9] Add `WorkspaceSettingsRepository.get_default_admin_id` in
  `backend/app/repositories/workspace_settings_repository.py` (new file), for the
  ownership-transfer lookup in T068
- [X] T065 [P] [US9] Add `create`, `update_role`, `update_password_hash`, `set_active`, and
  `get_by_employee_id` (for the uniqueness check in T068) to
  `backend/app/repositories/user_repository.py`
- [X] T066 [P] [US9] Add `list_owned_by` (all Meetings where `owner_id == user_id`) to
  `backend/app/repositories/meeting_repository.py`, for the ownership-transfer side effect in T068
- [X] T067 [US9] Add `CreateMemberRequest`, `RoleUpdateRequest`, `PasswordResetRequest`, and
  `ActiveUpdateRequest` to `backend/app/schemas/user.py`, per
  [users-api.md](./contracts/users-api.md)
- [X] T068 [US9] Add `create_member`, `update_role`, `reset_password`, `set_active` to
  `backend/app/services/user_service.py` (depends on T064, T065, T066, T067):
  - `create_member`: uniqueness check on `employee_mail_id`/`employee_id` (`ConflictError`, 409),
    hash the Password, create the User, log `MEMBER_ADDED` (FR-004)
  - `update_role`: log `MEMBER_ROLE_CHANGED` (FR-005)
  - `reset_password`: hash the new Password, log `MEMBER_PASSWORD_RESET` (FR-005) — never
    logs/returns the Password itself
  - `set_active`: on deactivation, reassign every Meeting this user owns to
    `WorkspaceSettings.default_admin_user_id` and flag `needs_reassignment` on every Task they're
    the Assignee of (reusing the existing `TaskRepository.list_by_assignee`/`update`), all as part
    of the same call; log `MEMBER_DEACTIVATED`/`MEMBER_REACTIVATED` (FR-006, FR-040)
- [X] T069 [US9] Add `POST /api/users`, `PATCH /api/users/{user_id}/role`,
  `PATCH /api/users/{user_id}/password`, `PATCH /api/users/{user_id}/active` to
  `backend/app/api/users.py`, all `require_role(ADMIN)`, per
  [users-api.md](./contracts/users-api.md) (depends on T067, T068)

### Frontend

- [X] T070 [P] [US9] Add `createMember`, `updateRole`, `resetPassword`, `setActive` to
  `frontend/src/services/usersApi.ts`, per [users-api.md](./contracts/users-api.md)
- [X] T071 [US9] Implement `frontend/src/pages/PeoplePage.tsx` (replacing its `PlaceholderPage` in
  `router.tsx`): a member table (Employee Name, Employee Mail ID, Employee ID, Role, Status,
  actions) plus a "+ Add Member" action, mirroring `mockup.html`'s `#screen-people` (depends on
  T070)
- [X] T072 [P] [US9] Add an `AddMemberModal` component
  (`frontend/src/components/people/AddMemberModal.tsx`) with Employee Name/Mail ID/Employee
  ID/Password/Role fields and inline validation, mirroring `mockup.html`'s `openAddMember()`/
  `saveMember()` flow (depends on T070)
- [X] T073 [P] [US9] Add a `RoleSelect` component
  (`frontend/src/components/people/RoleSelect.tsx`) — an inline Role dropdown per row that calls
  `updateRole` on change, mirroring `mockup.html`'s per-row Role `<select>` (depends on T070)
- [X] T074 [P] [US9] Add a `PasswordResetModal` component
  (`frontend/src/components/people/PasswordResetModal.tsx`) for the "Reset Password" action,
  mirroring `mockup.html`'s `resetPassword()` flow (depends on T070)
- [X] T075 [US9] Wire "Deactivate"/"Reactivate" as a row action in `PeoplePage.tsx` calling
  `setActive`, mirroring `mockup.html`'s `toggleActive()` (depends on T070, T071)

### Tests

- [X] T076 [P] [US9] Contract tests for `POST /api/users` in
  `backend/tests/contract/test_users_create.py`: `201` and the new member can sign in with the
  given credentials (AC2), `403` for a non-Admin, `409` for a duplicate `employeeMailId`/
  `employeeId`, `422` for a missing field or an invalid `role`
- [X] T077 [P] [US9] Contract tests for `PATCH /api/users/{user_id}/role` in
  `backend/tests/contract/test_users_role.py`: `200` and the new Role applies on the member's next
  sign-in (AC3), `403` for a non-Admin, `404` for an unknown user
- [X] T078 [P] [US9] Contract tests for `PATCH /api/users/{user_id}/password` in
  `backend/tests/contract/test_users_password.py`: `200`, the old Password is rejected and the new
  one is accepted (AC4), `403`, `404`, `422`
- [X] T079 [P] [US9] Contract tests for `PATCH /api/users/{user_id}/active` in
  `backend/tests/contract/test_users_active.py`: deactivation blocks sign-in and excludes the
  member from search (AC5), reactivation restores sign-in and search visibility (AC6), `403`,
  `404`
- [X] T080 [US9] Integration tests in
  `backend/tests/integration/test_people_management_workflow.py` — implemented as three cases
  rather than one combined case, since AC7's ownership-transfer and FR-024's task-flagging apply
  to different actors (a deactivated Meeting Owner vs. a deactivated Assignee) and conflating them
  in one Meeting/Task setup would have tested the wrong thing: (1) the story's own Independent
  Test end-to-end (add a member → sign in with those credentials → change Role → reset Password →
  deactivate → confirm sign-in/search are blocked), (2) AC7 (deactivating a Meeting Owner
  transfers ownership of all their Meetings to the default Admin), (3) FR-024 (deactivating a
  Task's Assignee flags that Task `needs_reassignment`)
- [X] T081 [P] [US9] Add a People flow test under `frontend/tests/integration/`: only an Admin
  sees the People nav item / can reach `/people`, "+ Add Member" creates a row, and Role
  change/Reset Password/Deactivate each call the right service function

**Checkpoint**: All seven of User Story 9's acceptance scenarios are satisfied; the new
`/api/users`-related backend tests plus the new frontend People flow test are green.

## Dependencies & Execution Order (Phase 5)

- T064, T065, T066 have no dependencies on each other or on other phases and can start
  immediately.
- T067 has no dependencies. T068 depends on T064, T065, T066, T067. T069 depends on T067, T068.
- T070 has no dependencies. T071 depends on T070. T072, T073, T074 depend on T070 and are
  independent of each other. T075 depends on T070, T071.
- T076-T079 depend on T069. T080 depends on T069 (it also exercises T068's ownership-transfer
  logic). T081 depends on T071-T075.

## Parallel Example: US9

```bash
# Backend repository layer, in parallel:
Task: "Add WorkspaceSettingsRepository.get_default_admin_id in backend/app/repositories/workspace_settings_repository.py"
Task: "Add create/update_role/update_password_hash/set_active to backend/app/repositories/user_repository.py"
Task: "Add list_owned_by to backend/app/repositories/meeting_repository.py"

# Backend contract tests, in parallel once the endpoints exist:
Task: "Contract tests for POST /api/users in backend/tests/contract/test_users_create.py"
Task: "Contract tests for PATCH /api/users/{user_id}/role in backend/tests/contract/test_users_role.py"
Task: "Contract tests for PATCH /api/users/{user_id}/password in backend/tests/contract/test_users_password.py"
Task: "Contract tests for PATCH /api/users/{user_id}/active in backend/tests/contract/test_users_active.py"
```

## Phase 6: US10 - Admin Reviews the Activity Log (Priority: P3)

Generated by `/speckit-tasks`, using spec.md, contracts/activity-log-api.md, research.md item 11,
and mockup.html as the source of truth for User Story 10 only.

**Goal**: An Admin opens Activity Log and sees a record of who did what and when across meetings,
tasks, people, notifications, mentions, and Azure DevOps references.

**Independent Test** (spec.md): Can be fully tested by performing a handful of actions (creating a
meeting, assigning a task, adding a member) and confirming each appears in the Activity Log with
its actor and timestamp.

**Already satisfied, no task needed**:
- The `ActivityLogEntry` model (`backend/app/models/activity_log.py`) and the `log_activity(db,
  actor_id, action, entity_type, entity_id)` helper (`backend/app/services/activity_log_service.py`)
  already exist and are already called for `MEETING_CREATED`/`MEETING_UPDATED`/`MEETING_DELETED`
  (`meeting_service.py`, prior story) and `MEMBER_ADDED`/`MEMBER_ROLE_CHANGED`/
  `MEMBER_PASSWORD_RESET`/`MEMBER_DEACTIVATED`/`MEMBER_REACTIVATED` (`user_service.py`, US9) — AC2's
  "creates a meeting... or manages a person's account" is already covered.
- AC1 (Activity Log hidden from Team Members) — `frontend/src/components/layout/NavSidebar.tsx`
  already gates the "Activity Log" nav item on `user?.role === "ADMIN"`, and `router.tsx`'s
  `/activity-log` route is already wrapped in `RequireAdmin`; only the read-side endpoint/page
  themselves are missing (T086-T090 below).

**Scope note** (flagging per "stop if a dependency on another user story is required"): AC2 also
requires "assigns a task" and "mentions a member" to appear in the log, and the story header/
research.md item 11 additionally call for tasks, notifications, and Azure DevOps references to be
covered. None of `task_service.py`, `comment_service.py`, `reference_service.py`, or
`backend/app/api/tasks.py` call `log_activity` today. T082-T085 add the minimal, additive
`log_activity` call needed at each existing action site in those files — no existing behavior
changes, only a new logging call is added at the end of an already-successful operation, matching
the pattern `meeting_service.py` and `user_service.py` already established themselves. This is
called out explicitly rather than silently skipped or silently done.

### Backend

- [X] T082 [US10] Add `log_activity` calls to `backend/app/services/task_service.py`: `TASK_CREATED`
  in `create_task` (actor: the Meeting Owner), `TASK_STATUS_CHANGED` in `update_task_status` (actor:
  the Assignee), `TASK_REASSIGNED` in `update_task` when `assignee_id` is among the changed fields
  (actor: `current_user`), `TASK_DELETED` in `delete_task` (actor: `current_user`) — entity type
  `"Task"`, entity id `task.id` in each case
- [X] T083 [US10] Add `log_activity` calls to `backend/app/services/comment_service.py`'s
  `create_comment`: `COMMENT_POSTED` (actor: `current_user`, entity `"Task"`/`task_id`) once the
  Comment is created, then one `MEMBER_MENTIONED` per resolved mention (actor: `current_user`,
  entity `"User"`/mentioned user's id) — satisfies AC2's "mentions a member" (depends on T082 for
  import placement only, no functional dependency)
- [X] T084 [US10] Thread an optional `actor_id: int | None` parameter through
  `sync_task_content_references`, `sync_comment_references`, and `_sync_ado_references` in
  `backend/app/services/reference_service.py`, and log one `ADO_REFERENCE_DETECTED` (entity
  `"Task"`/`task_id`) per newly-upserted `ado_id` when `actor_id` is given; pass `owner.id`/
  `current_user.id` from the two call sites already being touched in T082 (`task_service.py`) and
  T083 (`comment_service.py`) — when `actor_id` is omitted, behavior is unchanged (backward
  compatible with any other caller)
- [X] T085 [US10] Add one `log_activity(db, current_user.id, "NOTIFICATION_SENT", "Task", task.id)`
  call at each of the two `background_tasks.add_task(notification_service.notify_task_assigned,
  ...)` sites in `backend/app/api/tasks.py` (`create_task`, `update_task`), logged synchronously
  using the request's own `db` session at the point the notification is scheduled — not inside the
  background task itself, since FastAPI tears down a yield-dependency's `db` session before
  background tasks run, so `notification_service.py` deliberately has no `db` access to log from
- [X] T086 [P] [US10] Add `ActivityLogRepository.list(entity_type, since, page, page_size)` in
  `backend/app/repositories/activity_log_repository.py` (new file) — newest-first by `timestamp`,
  optionally filtered by `entity_type`/`since`, paginated
- [X] T087 [P] [US10] Add `ActivityLogEntryResponse` (`id`, `actorId`, `actorName`, `action`,
  `entityType`, `entityId`, `timestamp`) to `backend/app/schemas/activity_log.py` (new file), per
  [activity-log-api.md](./contracts/activity-log-api.md) — `actorName` is resolved via a join/lookup
  against `User` in the endpoint, not stored on `ActivityLogEntry` itself
- [X] T088 [US10] Add `GET /api/activity-log` to `backend/app/api/activity_log.py` (new file),
  `require_role(ADMIN)`, query params `entityType`/`since`/`page`/`pageSize` (all optional), per
  [activity-log-api.md](./contracts/activity-log-api.md) (depends on T086, T087); register
  `activity_log_router` in `backend/app/main.py` alongside the other routers

### Frontend

- [X] T089 [P] [US10] Add `getActivityLog(params)` to `frontend/src/services/activityLogApi.ts`
  (new file), calling `GET /api/activity-log`, per
  [activity-log-api.md](./contracts/activity-log-api.md)
- [X] T090 [US10] Implement `frontend/src/pages/ActivityLogPage.tsx` (replacing its
  `PlaceholderPage` in `router.tsx`): a card with an Actor/Action/Timestamp table, newest first,
  mirroring `mockup.html`'s `#screen-activity-log`/`renderActivityLog()` (depends on T089)

### Tests

- [X] T091 [P] [US10] Contract tests for `GET /api/activity-log` in
  `backend/tests/contract/test_activity_log.py`: `200` with entries shaped per
  `ActivityLogEntryResponse` newest-first, `403` for a non-Admin (AC1), `entityType`/`since`
  filters narrow the results
- [X] T092 [US10] Integration test in `backend/tests/integration/test_activity_log_workflow.py` —
  the story's own Independent Test end-to-end (create a meeting, assign a task, add a member, then
  confirm each appears in `GET /api/activity-log` with its actor and timestamp, AC2), plus AC3
  (deleting a meeting that has tasks records the cascading deletion as an entry) (depends on T082,
  T088)
- [X] T093 [P] [US10] Add an Activity Log flow test under `frontend/tests/integration/`: only an
  Admin can reach `/activity-log` and sees the logged entries; a Team Member navigating there is
  redirected away (AC1) (depends on T090)

**Checkpoint**: All three of User Story 10's acceptance scenarios are satisfied; `GET
/api/activity-log` reflects meeting, task, people, mention, notification, and Azure DevOps
reference actions; the new backend and frontend tests are green.

## Dependencies & Execution Order (Phase 6)

- T082, T083 have no dependencies on each other; both touch `reference_service.py`'s callers, which
  T084 then extends (T084 depends on T082, T083 for the call sites it wires into).
- T085 has no dependency on T082-T084 (it edits a different file, `api/tasks.py`) and can run in
  parallel with them.
- T086, T087 have no dependencies on each other or on T082-T085 and can start immediately. T088
  depends on T086, T087.
- T089 has no dependencies. T090 depends on T089.
- T091 depends on T088. T092 depends on T082, T088. T093 depends on T090.

## Parallel Example: US10

```bash
# Backend read-side, in parallel:
Task: "Add ActivityLogRepository.list in backend/app/repositories/activity_log_repository.py"
Task: "Add ActivityLogEntryResponse in backend/app/schemas/activity_log.py"

# Backend write-side instrumentation, in parallel (different files):
Task: "Add log_activity calls to backend/app/services/task_service.py"
Task: "Add NOTIFICATION_SENT log_activity calls in backend/app/api/tasks.py"
```
