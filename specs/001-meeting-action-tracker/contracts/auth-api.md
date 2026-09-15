# API Contract: Authentication

Base path: `/api/auth`. All request/response bodies are JSON, Pydantic models per constitution
Principle VI. Every other contract in this directory requires a valid `Authorization: Bearer
<token>` header — a JWT issued by `POST /api/auth/login` below, reused as-is on every subsequent
request until it expires.

*(2026-09-15 revert: replaces the interim 2026-09-14 Firebase-ID-token-based
`POST /api/auth/session` contract — see [research.md](../research.md) item 3. Authentication is
Employee Mail ID/Password again, exactly as the BRD specifies; there is no Google/Firebase sign-in.)*

## `POST /api/auth/login` — Sign In (User Story 1)

The Login screen offers visually separate "Team Member" and "Admin" sign-in options; both submit to
this same endpoint and both validate the submitted credentials against the same stored
Employee Mail ID/Password — the account's actual stored Role, not the option clicked, determines
access (FR-002). Sign-in is disabled client-side until the "I agree to the Terms and Conditions"
checkbox is checked (FR-045); `termsAccepted` below carries that confirmation to the backend.

**Request body** (`LoginRequest`):

```json
{ "employeeMailId": "sarah@example.com", "password": "hunter2", "termsAccepted": true }
```

**Responses**:
- `200 OK` → `LoginResponse`:
  ```json
  {
    "accessToken": "<JWT>",
    "user": {
      "id": 7,
      "employeeName": "Sarah Iyer",
      "employeeMailId": "sarah@example.com",
      "employeeId": "EMP-1042",
      "role": "TEAM_MEMBER",
      "isActive": true,
      "termsAccepted": true
    }
  }
  ```
  - The submitted Employee Mail ID/Password is validated against the stored `password_hash`
    (FR-001). `role` in the response is always the account's actual stored Role, regardless of
    which sign-in option (Team Member/Admin) the request came from (FR-002).
  - On a successful sign-in, the account's `termsAccepted` flag is set to `true` (FR-046); the
    request MUST fail validation (`422`) if `termsAccepted` is not `true`, since the Login screen
    MUST NOT allow submission with the checkbox unchecked (FR-045).
- `401 Unauthorized` — the Employee Mail ID/Password does not match any account, or matches a
  deactivated account (FR-001, FR-006). The response body does not reveal which of the two
  conditions applies.
- `422 Unprocessable Entity` — `termsAccepted` was not `true`, or a required field was missing.

## `GET /api/auth/me` — Current Session (used by route guards)

**Responses**:
- `200 OK` → the same `user` shape as `LoginResponse.user` above, for the account matching the
  bearer token's subject.
- `401 Unauthorized` — missing/expired/invalid token, or the account no longer exists or has been
  deactivated since the token was issued.

## Out of scope for this contract

There is no sign-up/self-registration endpoint and no Google/Firebase sign-in of any kind — every
account is created only by an Admin, via [users-api.md](./users-api.md)'s `POST /api/users` (the
People screen's "Add Member" action). This contract also does not include Password reset for an
existing member — that is an Admin action documented in [users-api.md](./users-api.md).
