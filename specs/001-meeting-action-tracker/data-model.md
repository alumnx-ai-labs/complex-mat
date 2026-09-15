# Phase 1 Data Model: Meeting Action Tracker (MAT)

This document describes the persisted entities, their fields, relationships, and validation rules,
reflecting the spec's Key Entities section refined into concrete database-level structures, as
amended 2026-09-15 for the reverted local, file-based (SQLite) storage approach and the reverted
Employee Mail ID/Password + Admin-creates-accounts authentication model (see
[research.md](./research.md) items 1, 3, 9, 10). Every entity is a SQLAlchemy declarative model
backed by a table of its plural snake_case form (e.g. `users`, `meetings`, `tasks`); every `id`/
foreign-key field is an auto-incrementing integer primary key.

## User

Represents one workspace member's account, created only by an Admin from the People screen's "Add
Member" action — the only identity concept in MAT; there is no separate "Person" concept and no
self-registration path.

| Field | Type | Notes |
|---|---|---|
| `id` | integer/UUID, primary key | Unique user identifier |
| `employee_name` | string, required | Display name shown throughout MAT; set by the Admin at account creation |
| `employee_mail_id` | string, required, unique | Sign-in identifier and notification address; set by the Admin at account creation (FR-001) |
| `employee_id` | string, required, unique | Internal employee identifier; set by the Admin at account creation |
| `password_hash` | string, required | Hashed Password (never stored or returned as plaintext); Admin-set at creation and Admin-resettable thereafter (FR-005) |
| `role` | enum: `ADMIN`, `TEAM_MEMBER` | Exactly one per user (FR-003); set at account creation and changeable only by an Admin afterward (FR-004, FR-005) |
| `is_active` | boolean, default `true` | `false` after deactivation (FR-006) |
| `terms_accepted` | boolean, default `false` | Set to `true` the first time this account signs in successfully after checking "I agree to the Terms and Conditions" (FR-046) |
| `created_at` | timestamp, server-set | Record creation time |

**Relationships**: a User may be the `owner` of many Meetings (1:N), an Attendee of many Meetings
(M:N via `MeetingAttendee`), the Assignee of many Tasks (1:N), the author of many
Comments (1:N), and the `actor` of many ActivityLogEntry rows (1:N).

**Validation rules**:
- `employee_mail_id` and `employee_id` are each unique across all users (FR-001, FR-004).
- A User is created only by an Admin via `user_service.create_member` (the People screen's "Add
  Member" action), capturing Employee Name, Employee Mail ID, Employee ID, Password, and Role —
  there is no self-registration path (FR-004). Only an Admin may change an existing User's `role`,
  reset their `password_hash`, or change `is_active` afterward (FR-005); a user may not change
  their own `role` or reset their own Password.
- A deactivated (`is_active == false`) user MUST be rejected at sign-in — even with a correct
  Employee Mail ID and Password — and MUST be excluded from attendee/assignee search results
  (FR-006).
- Sign-in MUST be rejected unless the Login screen's "I agree to the Terms and Conditions" checkbox
  was checked (FR-045); on a successful sign-in, `terms_accepted` MUST be set to `true` for that
  account (FR-046).

## Meeting

Represents a single scheduled meeting.

| Field | Type | Notes |
|---|---|---|
| `id` | integer/UUID, primary key | Unique meeting identifier |
| `title` | string, required, non-empty | Meeting title (FR-009) |
| `date` | date, required | Meeting date (FR-009); prefilled from the selected Calendar date (FR-008) |
| `time` | time, required | Meeting time |
| `agenda_notes` | text, optional | Free-text agenda/notes |
| `owner_id` | FK → User.id, required | The creating Admin; system-assigned, immutable except via the deactivation-triggered transfer in [research.md](./research.md) item 10 (FR-010, FR-040) |
| `created_at` | timestamp, server-set | For ordering in Previous Meetings |

**Relationships**: one Meeting has many `MeetingAttendee` rows (1:N, cascade delete with the
meeting) and many `Task` rows (1:N, cascade delete with the meeting, per FR-013).

**Validation rules**:
- `title` and `date` are mandatory at creation (FR-009); a request missing either is rejected.
- Only a user with `role == ADMIN` may create a Meeting (FR-007); any Admin (not only the Owner)
  may edit or delete it (FR-012), except that `owner_id` itself is never directly editable through
  the edit endpoint.
- Deleting a Meeting deletes all of its Tasks (and their Comments/references) in the same
  transaction (FR-013).

## MeetingAttendee

Join table between Meeting and User — the "Attendee" relationship.

| Field | Type | Notes |
|---|---|---|
| `id` | integer/UUID, primary key | Unique row identifier |
| `meeting_id` | FK → Meeting.id, required | Owning meeting |
| `user_id` | FK → User.id, required | The invited member |

**Relationships**: many `MeetingAttendee` rows belong to one Meeting (N:1) and reference one User
(N:1). A Task's `assignee_id` is validated against the set of `MeetingAttendee` rows for its
Meeting.

**Validation rules**:
- `(meeting_id, user_id)` is unique — the same member cannot be added twice to one meeting.
- Attendees are added via a search across **all** active workspace members, by `employee_name` or
  `employee_id` (FR-011); a deactivated user cannot be added.
- If an Attendee is removed from this table while they are the Assignee of one of the meeting's
  Tasks, that Task is flagged `needs_reassignment` rather than automatically unassigned (FR-024).

## Task

Represents one action item belonging to exactly one meeting and assigned to exactly one attendee.

| Field | Type | Notes |
|---|---|---|
| `id` | integer/UUID, primary key | Unique task identifier |
| `meeting_id` | FK → Meeting.id, required | Parent meeting (FR-017); immutable after creation |
| `title` | string, required, non-empty | Task Title; may contain `@Name` mentions or `@<number>` Azure DevOps tokens |
| `description_notes` | text, optional | Description/Notes; may also contain `@Name`/`@<number>` tokens |
| `assignee_id` | FK → User.id, required | Must be an Attendee of `meeting_id` (FR-017) |
| `due_date` | date, optional | Due Date |
| `status` | enum: `TODO`, `IN_PROGRESS`, `COMPLETED` | Defaults to `TODO` on creation (FR-019) |
| `needs_reassignment` | boolean, default `false` | Set when the current Assignee is deactivated or removed as an Attendee (FR-024) |
| `created_at` | timestamp, server-set | For stable ordering on boards |

**Relationships**: many Task rows belong to one Meeting (N:1) and reference one User as Assignee
(N:1). One Task has many `Comment` rows (1:N) and many derived `TaskAdoReference` rows (1:N).

**Validation rules**:
- `assignee_id` MUST reference a `MeetingAttendee` of the same `meeting_id`; otherwise the write is
  rejected (FR-017).
- `status` MUST be one of the three defined values; on create it is always forced to `TODO`
  regardless of any client-sent value (FR-019).
- Only the parent Meeting's `owner_id` user may set or change `assignee_id` (FR-016); any Admin may
  otherwise edit `title`, `due_date`; the Assignee may edit only `description_notes` and `status`
  (FR-022); nobody but an Admin/Owner may delete a Task, and never the Assignee (FR-023).
- `title` is mandatory, non-empty.

**State transitions**: `status` may move freely between `TODO`, `IN_PROGRESS`, and `COMPLETED` in
any direction; only a request from the user matching `Task.assignee_id` may change it (FR-021). A
Task once `needs_reassignment == true` stays assigned to the same (now-invalid) Assignee until an
Admin/Owner explicitly reassigns it — this flag is never cleared automatically (FR-024).

## Comment

Represents one message posted against a Task.

| Field | Type | Notes |
|---|---|---|
| `id` | integer/UUID, primary key | Unique comment identifier |
| `task_id` | FK → Task.id, required | Parent task |
| `author_id` | FK → User.id, required | Must be the parent Task's Meeting Owner, the Task's Assignee, or any Admin at post time (FR-027) |
| `message` | text, required, non-empty | Comment text; may contain `@Name` mentions or `@<number>` Azure DevOps tokens |
| `created_at` | timestamp, server-set | Ordering within the thread |

**Relationships**: many Comments belong to one Task (N:1). A Comment's parsed content produces
zero or more `CommentMention` rows and zero or more `TaskAdoReference` rows (associated with the
parent Task, since Azure DevOps links are a Task-level, not Comment-level, concept per the BRD).

**Validation rules**:
- `author_id` must satisfy the posting-permission check above at write time (FR-027); this is
  re-checked on every post, not cached from Task/Meeting state.

## CommentMention *(derived at write time)*

Normalizes an `@Name` token found in a Task's `title`/`description_notes` or a `Comment.message`
into a notifiable relationship (FR-028, FR-036).

| Field | Type | Notes |
|---|---|---|
| `id` | integer/UUID, primary key | Unique row identifier |
| `source_type` | enum: `TASK`, `COMMENT` | Which field the mention was found in |
| `source_id` | FK → Task.id or Comment.id | Depends on `source_type` |
| `mentioned_user_id` | FK → User.id, required | Must be an Attendee of the mention's parent Meeting (FR-028) |
| `created_at` | timestamp, server-set | Used to avoid re-notifying on unchanged content |

## TaskAdoReference *(derived at write time, refreshed at read time)*

Normalizes an `@<number>` token into a Linked Azure DevOps Item (FR-030).

| Field | Type | Notes |
|---|---|---|
| `id` | integer/UUID, primary key | Unique row identifier |
| `task_id` | FK → Task.id, required | The Task the reference belongs to |
| `ado_work_item_id` | integer, required | The numeric ID parsed from `@<number>` |
| `cached_title` | string, nullable | Last-known title, shown even when currently unavailable |
| `cached_type` | string, nullable | Last-known type (Story/Feature) |
| `is_available` | boolean | Refreshed from Azure DevOps at read time; `false` disables "Open in Azure DevOps" (FR-032) |
| `last_checked_at` | timestamp | When availability/title/type were last refreshed |

**Validation rules**:
- `(task_id, ado_work_item_id)` is unique — a given work item is linked at most once per Task even
  if `@<number>` appears more than once across its fields/comments.
- MAT never calls a create/update endpoint against Azure DevOps for this row (FR-031) — it is
  strictly a read/reference cache.

## ActivityLogEntry

An append-only audit record (FR-041), visible to Admins only.

| Field | Type | Notes |
|---|---|---|
| `id` | integer/UUID, primary key | Unique entry identifier |
| `actor_id` | FK → User.id, required | Who performed the action |
| `action` | string, required | e.g., `MEETING_CREATED`, `TASK_ASSIGNED`, `MEMBER_DEACTIVATED` |
| `entity_type` | string, required | e.g., `Meeting`, `Task`, `User` |
| `entity_id` | integer/UUID, required | The affected entity's id |
| `timestamp` | timestamp, server-set | When the action occurred |

## WorkspaceSettings *(singleton configuration)*

| Field | Type | Notes |
|---|---|---|
| `default_admin_user_id` | FK → User.id | Target of automatic Meeting-Owner transfer on deactivation (FR-040, [research.md](./research.md) item 10) |

## Field-level authorization summary

Consolidates *who* may write *what*, as enforced by the service layer (constitution Principle VII):

| Field | Who may write it | Enforcement point |
|---|---|---|
| `User` creation | Only an Admin, via the People screen's "Add Member" action | `user_service.create_member` |
| `User.role`, `password_hash`, `is_active` (after creation) | Any Admin, for any user (never the user themself) | `user_service.update_role` / `reset_password` / `set_active` *(not yet implemented — User Story 9)* |
| `User.terms_accepted` | System only — set on the user's own successful sign-in | `auth_service.sign_in` |
| `Meeting.title`, `date`, `time`, `agenda_notes`, attendees | Any Admin | `meeting_service.create_meeting` / `update_meeting` |
| `Meeting.owner_id` | System only — set at creation; changed only by the deactivation-transfer routine | `meeting_service.create_meeting`, `user_service.set_active` |
| `Task.title`, `due_date` | Any Admin (the Meeting Owner is also an Admin) | `task_service.create_task` / `update_task` |
| `Task.assignee_id` | Only the parent Meeting's `owner_id` user | `task_service.assign_task`, checked against `Meeting.owner_id` |
| `Task.description_notes`, `status` | Only the user matching `Task.assignee_id` | `task_service.update_own_task` |
| `Task` deletion | Any Admin; never the Assignee acting alone | `task_service.delete_task` |
| `Comment` creation | Meeting Owner, Task Assignee, or any Admin | `comment_service.create_comment` |

## Entity-relationship summary

```text
User (1) ──< Meeting (N)              "owner_id: meetings this user created/owns"
User (M) ──< MeetingAttendee >── (N) Meeting   "attendees invited to a meeting"
Meeting (1) ──< Task (N)              "tasks raised for a meeting"
User (1) ──< Task (N)                 "assignee_id: tasks assigned to this user"
Task (1) ──< Comment (N)              "discussion thread on a task"
Task (1) ──< TaskAdoReference (N)     "linked Azure DevOps Stories/Features"
(Task | Comment) (1) ──< CommentMention (N) ──> User (1)   "who was @mentioned, and where"
User (1) ──< ActivityLogEntry (N)     "actor: actions this user performed"
```
