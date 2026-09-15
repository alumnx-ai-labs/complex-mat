# API Contract: People (Users)

Base path: `/api/users`. Also used by Attendee/Assignee search from Meetings/Tasks.

*(2026-09-15 revert: restores `POST /api/users` (account creation) and
`PATCH /api/users/{user_id}/password` (Password reset), both Admin-only, in place of the interim
2026-09-14 "accounts are auto-provisioned via Google Sign-In" model — see
[auth-api.md](./auth-api.md) and [research.md](../research.md) item 3. `employeeId` is restored to
all request/response shapes and to search — see [research.md](../research.md) item 9.)*

## `POST /api/users` — Add Member (People "Add Member", User Story 9)

Requires an authenticated Admin (`require_role(ADMIN)`) — a Team Member gets `403 Forbidden`
(FR-042). This is the only way a new account comes into existence; there is no self-registration
path (FR-004).

**Request body** (`CreateMemberRequest`):

```json
{
  "employeeName": "Priya Nair",
  "employeeMailId": "priya@example.com",
  "employeeId": "EMP-1077",
  "password": "TempPass123!",
  "role": "TEAM_MEMBER"
}
```

**Responses**:
- `201 Created` → `UserResponse` (see shape below); the account can sign in immediately with the
  given Employee Mail ID and Password (FR-004).
- `403 Forbidden` — caller is not an Admin.
- `409 Conflict` — `employeeMailId` or `employeeId` is already in use by another account.
- `422 Unprocessable Entity` — a required field is missing or `role` is not one of `ADMIN` /
  `TEAM_MEMBER`.

## `GET /api/users` — Search Members (Attendee search, User Story 2; People list, User Story 9)

Requires an authenticated Admin (`require_role(ADMIN)`) — a Team Member gets `403 Forbidden`
(FR-042).

**Query parameters**:
- `q` (string, optional) — case-insensitive substring match against `employeeName` or
  `employeeId` (FR-011). Omitted → returns all active members (People screen listing).
- `activeOnly` (boolean, default `true`) — deactivated members are excluded from Attendee search
  by default (FR-006).

**Response** `200 OK` → `UserResponse[]`:

```json
[{
  "id": 7,
  "employeeName": "Sarah Iyer",
  "employeeMailId": "sarah@example.com",
  "employeeId": "EMP-1042",
  "role": "TEAM_MEMBER",
  "isActive": true,
  "termsAccepted": true
}]
```

Note: `UserResponse` never includes `password`/`passwordHash`.

## `PATCH /api/users/{user_id}/role` — Change Role (User Story 9)

Requires an authenticated Admin.

**Request body**: `{ "role": "ADMIN" }`

**Responses**:
- `200 OK` → updated `UserResponse`.
- `403 Forbidden` — caller is not an Admin.
- `404 Not Found` — no such user.

## `PATCH /api/users/{user_id}/password` — Reset Password (User Story 9)

Requires an authenticated Admin. Only an Admin may reset a member's Password; a member cannot reset
their own (FR-005).

**Request body**: `{ "password": "NewTempPass456!" }`

**Responses**:
- `200 OK` → updated `UserResponse` (Password itself is never returned).
  - The member can no longer sign in with the old Password and can sign in with the new one
    immediately.
- `403 Forbidden` — caller is not an Admin.
- `404 Not Found` — no such user.
- `422 Unprocessable Entity` — `password` missing or fails policy validation.

## `PATCH /api/users/{user_id}/active` — Deactivate / Reactivate (User Story 9)

Requires an authenticated Admin.

**Request body**: `{ "isActive": false }`

**Responses**:
- `200 OK` → updated `UserResponse`.
- `403 Forbidden` — caller is not an Admin.
- `404 Not Found` — no such user.

**Side effects** (FR-006, FR-040, [research.md](../research.md) item 10): setting `isActive: false`
— in the same transaction —
1. blocks that user from signing in (even with a correct Employee Mail ID/Password) and from
   appearing in future Attendee/Assignee search results;
2. transfers `owner_id` on every Meeting they own to the workspace's configured default Admin;
3. flags `needs_reassignment` on every Task where they are the Assignee, without changing
   `assignee_id`.

Setting `isActive: true` on a previously deactivated member lets them sign in again with their
Employee Mail ID/Password and regain their prior Role's access; it does not restore any Meeting
ownership already transferred away.
