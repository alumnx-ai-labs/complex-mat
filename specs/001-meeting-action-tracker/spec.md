# Feature Specification: Meeting Action Tracker (MAT)

**Feature Branch**: `001-meeting-action-tracker`

**Created**: 2026-09-13

**Status**: Draft

**Amended**: 2026-09-14 — The database switched from a local file-based store to MongoDB (see
plan.md).

**Amended**: 2026-09-15 — Reverted the 2026-09-14 MongoDB switch. The database is a local,
file-based store (SQLite) again, as originally specified; MongoDB is no longer part of this
specification (see plan.md, data-model.md, and constitution v4.0.0).

**Amended**: 2026-09-15 — Reverted an interim change to Google Sign-In. Authentication is
Employee Mail ID/Password again, exactly as the BRD specifies: no self-registration, and only an
Admin creates member accounts (Employee Name, Employee Mail ID, Employee ID, Password, Role) from
the People screen's "Add Member" action. There is no Google/Firebase sign-in and no self-service
account auto-provisioning anywhere in this specification.

**Input**: User description: "Build the complete Meeting Action Tracker (MAT) application exactly as described in the Business Requirements Document (BRD.docx), which is the authoritative source of truth for this project. MAT is a single shared workspace for one internal organisation's meetings and the tasks that come out of them. Core requirements: (1) Authentication & Roles — Employee Mail ID/Password login, no self-registration, only an Admin creates member accounts (Employee Name, Employee Mail ID, Employee ID, Password, Role) from a People screen, exactly two roles (Admin, Team Member), Login shows Team Member/Admin sign-in as visually separate options but both check the same credentials and the account's actual Role determines access. (2) Meetings — only an Admin creates a Meeting, only from Calendar; selecting a date opens Create Meeting prefilled with it; fields are Title, Date, Time, Attendees (via internal member search), Agenda/Notes; the creating Admin becomes the Meeting Owner; any Admin may edit or delete any Meeting; deleting cascades to its Tasks; Team Members see only Meetings they're invited to, Admins see all. (3) Tasks — one Meeting, one Assignee; fields Task Title, Description/Notes, Assignee, Due Date, Status (To Do/In Progress/Completed); only the Meeting Owner assigns/reassigns the Assignee; Assignee must be a Meeting Attendee; Team Members drag their own cards between columns; an Assignee may edit only their own Task's Status and Description/Notes and cannot delete it; a deactivated/removed Assignee keeps the assignment but is flagged for reassignment. (4) My Tasks — every Task assigned to the authenticated user across all their Meetings, labelled with its parent Meeting, same columns/permissions. (5) Internal Member Search — Attendees searched across all members; Task Assignee searched only within that Meeting's Attendees. (6) Task Comments & @Mentions — Meeting Owner, Assignee, or any Admin can comment; \"@\" plus letters searches that Meeting's Attendees for a mention. (7) Azure DevOps Integration — no dedicated reference field; \"@<number>\" typed in Title/Description/Comments auto-links an existing Story/Feature, distinct from a mention by digits vs letters; suggestions are scoped to the current user's own Azure DevOps access; each Linked Item shows as \"ADO #<id> — <title>\" with an \"Open in Azure DevOps\" action; referencing never creates/modifies a work item; an unavailable/deleted item shows an unavailable indicator with the Open action disabled; MAT stays usable if Azure DevOps is down. (8) Notifications — email on Task assignment, on a new comment (unless the Assignee authored it), and on an @mention; delivery failure never blocks the underlying action. (9) People screen (Admin only) — add a member, and per-member edit Role, reset Password, or deactivate/reactivate; deactivation blocks sign-in and removes the member from search; if a Meeting Owner is deactivated, ownership of their Meetings transfers to the workspace's configured default Admin. (10) Activity Log (Admin only) — records actor, action, and timestamp for key actions across Meetings, Tasks, People, Notifications, Mentions, and Azure DevOps references. (11) Navigation covers Login, Calendar, Create/Edit Meeting, Meeting Details with its Task Board, My Tasks, Task Details, Previous Meetings, and the Admin-only People and Activity Log screens. (12) Responsive Design — fully usable on desktop and mobile, following the provided mockup's visual direction."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Sign In and Reach the Shared Workspace (Priority: P1)

A person opens the application and signs in with the Employee Mail ID and Password an Admin gave
them, entering their credentials on either the Team Member or the Admin sign-in option (visually
separate, but both check the same stored credentials). The workspace they land in — and
everything they can see and do there — matches their account's actual stored Role, regardless of
which sign-in option they used.

**Why this priority**: Nothing else is reachable without this; it is the entry gate, and getting Role-based access wrong undermines every other guarantee in the system (who can create a meeting, assign a task, or see People/Activity Log).

**Independent Test**: Can be fully tested by an Admin creating one Team Member account and one Admin account from the People screen, then signing in with each set of credentials — via either sign-in option — and confirming Admin-only screens and actions are unavailable for the Team Member account and available for the Admin account.

**Acceptance Scenarios**:

1. **Given** an Admin has created a member account with an Employee Mail ID and Password, **When** that person enters those credentials on either the Team Member or the Admin sign-in option and submits, **Then** they are signed in with their account's actual stored Role, regardless of which option they used.
2. **Given** the Login screen, **When** a person submits an Employee Mail ID and Password that do not match any account, or that match a deactivated account, **Then** they are not signed in and are told their credentials are incorrect.
3. **Given** a signed-in Team Member, **When** they look for People or Activity Log navigation, **Then** those destinations are not available to them.
4. **Given** a signed-in Admin, **When** they view navigation, **Then** Calendar, My Tasks, Previous Meetings, People, and Activity Log are all available.
5. **Given** the Login screen, **When** it is viewed, **Then** there is no sign-up form — every account comes into existence only via an Admin's "Add Member" action on the People screen.
6. **Given** the Login screen, **When** the "I agree to the Terms and Conditions" checkbox is unchecked, **Then** sign-in is disabled and cannot proceed on either sign-in option.
7. **Given** the Login screen, **When** a person checks the "I agree to the Terms and Conditions" checkbox and then signs in successfully, **Then** their acceptance of the Terms and Conditions is recorded against their account.

---

### User Story 2 - Admin Creates a Meeting and Becomes Its Owner (Priority: P1)

An Admin opens Calendar, selects a date, and is taken to Create Meeting with that date already filled in. They complete Title, Time, Attendees (found via a search across all internal members), and Agenda/Notes, then save. The Admin who saved it becomes that meeting's Meeting Owner, shown clearly on Meeting Details.

**Why this priority**: Creating meetings is the reason the workspace exists; without it there is no calendar content and no downstream task tracking.

**Independent Test**: Can be fully tested by an Admin selecting a Calendar date, completing and saving Create Meeting, and confirming the meeting appears on the calendar, in Previous Meetings, and shows that Admin as Meeting Owner on its details — without any task existing yet.

**Acceptance Scenarios**:

1. **Given** a Team Member is signed in, **When** they view Calendar, **Then** they have no way to create a Meeting.
2. **Given** an Admin selects a date on Calendar, **When** Create Meeting opens, **Then** its Date field is already filled with the selected date.
3. **Given** the Create Meeting form is open, **When** the Admin submits without a Title, **Then** the meeting is not saved and they are told a Title is required.
4. **Given** a valid Title, Date, Time, at least one Attendee, and optional Agenda/Notes, **When** the Admin saves, **Then** the meeting is created with a unique ID, those field values, and that Admin recorded as Meeting Owner.
5. **Given** the Admin is adding Attendees, **When** they search, **Then** results come from all internal workspace members (not only that meeting's current attendees), searchable by display name or email address.
6. **Given** a meeting was just created, **When** a different person's session views the calendar, **Then** the new meeting is visible to them if their Role/invitation allows it, without manual re-entry.

---

### User Story 3 - Meeting Owner Assigns and Manages Tasks (Priority: P2)

Opening a meeting shows its Title, Date, Time, Attendees, Agenda/Notes, Meeting Owner, and its Task Board. The Meeting Owner creates Tasks (Task Title, Description/Notes, Due Date) and assigns each to one Attendee found via a search scoped to that meeting's Attendees. Only the Meeting Owner — not any other Admin — can assign or reassign a Task's Assignee.

**Why this priority**: This is where action items are actually captured and made accountable; it depends on User Story 2 (a meeting must exist).

**Independent Test**: Can be fully tested by the Meeting Owner adding a task, assigning it to an attendee, confirming it defaults to "To Do," and confirming a different Admin (not the Owner) cannot change that task's assignee.

**Acceptance Scenarios**:

1. **Given** an open meeting's details, **When** the page loads, **Then** its Title, Date, Time, Attendees, Agenda/Notes, Meeting Owner, and current Tasks (in To Do / In Progress / Completed columns with live counts) are all displayed.
2. **Given** the current person is the meeting's Owner, **When** they add a Task with a Title and pick one Attendee as Assignee, **Then** the Task is created with status "To Do."
3. **Given** the current person is an Admin but not this meeting's Owner, **When** they try to assign or reassign a Task's Assignee, **Then** that control is unavailable to them, even though they may otherwise edit the meeting.
4. **Given** a Task's Assignee is being set, **When** someone who is not an Attendee of that meeting is selected, **Then** the assignment is rejected.
5. **Given** a Task's Assignee is later deactivated or removed as an Attendee, **When** the Task is viewed, **Then** it keeps its existing assignment but is flagged as needing reassignment, and nobody is automatically assigned in their place.
6. **Given** the meeting's Owner or an Admin deletes a Task, **When** the deletion completes, **Then** the task no longer appears anywhere, including in the assignee's My Tasks view.

---

### User Story 4 - Team Member Tracks and Updates Their Own Tasks (Priority: P2)

A Team Member opens My Tasks and sees every Task assigned to them across all Meetings they can access, each labelled with its parent meeting's name, grouped into To Do, In Progress, and Completed columns. They can drag a card between columns, or use a direct status control, to update its status, and can edit that Task's own Description/Notes — but nothing else about it, and nothing on a Task assigned to someone else.

**Why this priority**: This is the personal, day-to-day workflow that makes the tracker useful once tasks exist; it depends on User Story 3 having produced at least one assigned task.

**Independent Test**: Can be fully tested by assigning a task to a Team Member, signing in as that member, opening My Tasks, moving the task to another column, editing its Description/Notes, and confirming the Task's Title, Due Date, and Assignee remain unchanged and undeletable by that member.

**Acceptance Scenarios**:

1. **Given** tasks assigned to several different people exist, **When** a Team Member opens My Tasks, **Then** only tasks assigned to them are shown, each labelled with its meeting's name.
2. **Given** the My Tasks board or a meeting's Task Board, **When** a Team Member drags their own task card into a different column, **Then** its status updates immediately and the column counts update, visible from any other session viewing that data.
3. **Given** a Team Member views a Task assigned to someone else, **When** they attempt to drag it or change its status, **Then** the action is not available to them.
4. **Given** a Task assigned to the current Team Member, **When** they edit its Description/Notes, **Then** the change is saved, but its Title, Due Date, and Assignee remain unchanged and uneditable by them.
5. **Given** a Task assigned to the current Team Member, **When** they look for a delete action, **Then** none is available to them.
6. **Given** a Task moves to "Completed," **When** the board is viewed again later, **Then** the Task remains visible in the Completed column rather than disappearing.

---

### User Story 5 - Collaborate via Comments, Mentions, and Azure DevOps References (Priority: P2)

From a Task's details, the Meeting Owner, the Task's Assignee, or any Admin can post comments. Typing "@" followed by letters in a Task's Title, Description/Notes, or a comment opens a search of that meeting's Attendees to pick a member mention. Typing "@" followed by digits instead auto-detects an Azure DevOps Story or Feature reference, shown as a distinct, clearly labelled Linked Azure DevOps Item with its own "Open in Azure DevOps" action.

**Why this priority**: This is how task-level discussion, accountability, and traceability to engineering work happen; it depends on tasks already existing (User Story 3).

**Independent Test**: Can be fully tested by posting a comment that both mentions an attendee ("@Name") and references a work item ("@1234"), and confirming the mention renders as a member reference while the numeric token renders as a distinct Linked Azure DevOps Item with an Open action.

**Acceptance Scenarios**:

1. **Given** a Task's details, **When** someone who is neither the Meeting Owner, the Assignee, nor an Admin tries to post a comment, **Then** they cannot.
2. **Given** a person is typing in a Task's Title, Description/Notes, or a comment, **When** they type "@" followed by letters, **Then** a search of that meeting's Attendees appears and a selection renders as "@Name."
3. **Given** the same fields, **When** they type "@" followed by digits instead, **Then** Azure DevOps Story/Feature suggestions appear (each showing at least ID, Title, and Type), scoped to the current user's own Azure DevOps access.
4. **Given** a Task's Description/Notes contains "@1234," **When** the Task is viewed, **Then** it displays a Linked Azure DevOps Item "ADO #1234 — <title>" with its own "Open in Azure DevOps" action, and there is no separate Azure DevOps reference field to fill in.
5. **Given** a Linked Azure DevOps Item's underlying work item is later deleted or becomes inaccessible, **When** the Task is viewed, **Then** it still shows that reference with an "unavailable" indicator and the Open action disabled.
6. **Given** Azure DevOps is temporarily unavailable, **When** the rest of the Task is viewed or edited, **Then** everything except "@<number>" suggestion lookups continues to work normally.

---

### User Story 6 - Automatic Email Notifications (Priority: P3)

People are kept informed by email without having to poll the app: the Assignee is notified when a Task is assigned to them or commented on by someone else, and a mentioned member is notified when they are "@"-mentioned.

**Why this priority**: This is a convenience/awareness layer on top of assignment, comments, and mentions (User Stories 3 and 5); the workspace is fully usable without it, but it reduces missed updates.

**Independent Test**: Can be fully tested by assigning a task to a member and confirming they receive an assignment email, then posting a comment as someone else and confirming the Assignee receives a comment email containing task, meeting, sender, due date, and comment content — and confirming no email is sent when the Assignee comments on their own task.

**Acceptance Scenarios**:

1. **Given** a Task is assigned to a member, **When** the assignment is saved, **Then** that member receives an email notification.
2. **Given** a comment is posted on a Task by someone other than its Assignee, **When** the comment is saved, **Then** the Assignee receives an email containing the task, meeting, sender, due date, and comment content.
3. **Given** the Assignee posts a comment on their own Task, **When** it is saved, **Then** no comment-notification email is sent to them for that comment.
4. **Given** a member is "@"-mentioned in a Task comment, **When** the comment is saved, **Then** the mentioned member receives an email notification, independent of any assignee notification.
5. **Given** the email service is temporarily unavailable, **When** a Task is assigned, commented on, or a mention is made, **Then** that underlying action still completes successfully and is not lost or blocked.

---

### User Story 7 - Admin Edits or Deletes a Meeting (Priority: P3)

Any Admin — not only the Meeting Owner — can edit a meeting's details or delete it entirely. Deleting a meeting removes all of its tasks along with it.

**Why this priority**: Corrections and cleanup are needed after meetings exist (User Story 2), but this is not required for the core create → assign → work loop to function.

**Independent Test**: Can be fully tested by having an Admin who is not the Meeting Owner edit a meeting's Agenda/Notes, then delete that meeting, and confirming its tasks no longer appear anywhere, including in any assignee's My Tasks.

**Acceptance Scenarios**:

1. **Given** any Admin views a meeting they did not create, **When** they open Edit Meeting, **Then** they can change its Title, Date, Time, Attendees, and Agenda/Notes.
2. **Given** an Admin edits a meeting's Attendees, **When** the change is saved, **Then** any Task already assigned to someone removed from the Attendee list is flagged as needing reassignment rather than silently reassigned.
3. **Given** an Admin deletes a meeting, **When** the deletion completes, **Then** all of that meeting's Tasks are deleted along with it, and this is recorded as a single cascading action.
4. **Given** an Admin edits or deletes a meeting, **When** the change is saved, **Then** the Meeting Owner field itself cannot be changed by that edit — only Task-Assignee reassignment is Owner-exclusive.

---

### User Story 8 - Browse Previous Meetings (Priority: P3)

A person opens Previous Meetings and sees a list of meetings already created — restricted to the ones their Role/invitation allows them to see — each showing its title, date, and how many tasks it has, with the option to open its full details.

**Why this priority**: This is a convenience/history view; it depends on meetings already existing (User Story 2) and adds no new data-entry capability.

**Independent Test**: Can be fully tested by creating two or more meetings, opening Previous Meetings as different Roles, and confirming each visible meeting lists correct title, date, and task count, and that opening one navigates to its details.

**Acceptance Scenarios**:

1. **Given** two or more meetings have been created, **When** an Admin opens Previous Meetings, **Then** every meeting is listed with its title, date, and task count.
2. **Given** a Team Member was not invited to a given meeting, **When** they open Previous Meetings, **Then** that meeting does not appear in their list.
3. **Given** a meeting has 3 tasks, **When** it is listed in Previous Meetings, **Then** its task count reads 3, and the count updates if a task is later added or deleted.
4. **Given** the Previous Meetings list, **When** a person selects a meeting they are permitted to view, **Then** that meeting's full details open.

---

### User Story 9 - Admin Manages Member Accounts, Roles, and Access (Priority: P3)

An Admin opens the People screen and can add a new member (Employee Name, Employee Mail ID,
Employee ID, Password, Role), and for any existing member can change their Role, reset their
Password, or deactivate/reactivate them.

**Why this priority**: Ongoing account and access management is an administrative back-office task, not part of the core meeting/task workflow being exercised day to day; it is, however, the only way a new person gains access at all (see User Story 1), since there is no self-registration.

**Independent Test**: Can be fully tested by having an Admin add a new member from the People screen, confirming that member can sign in with the credentials given to them, confirming an Admin can change their Role and reset their Password, then deactivating the member and confirming they can no longer sign in or appear in attendee/assignee search.

**Acceptance Scenarios**:

1. **Given** a Team Member is signed in, **When** they try to reach People, **Then** it is not available to them.
2. **Given** the People screen, **When** an Admin adds a member with Employee Name, Employee Mail ID, Employee ID, Password, and Role, **Then** a new account is created with those values and that member can sign in with that Employee Mail ID and Password.
3. **Given** an existing member, **When** an Admin changes their Role, **Then** the member has the new Role's permissions the next time they access the workspace.
4. **Given** an existing member, **When** an Admin resets their Password, **Then** they can no longer sign in with their old Password and can sign in with the new one.
5. **Given** an existing member, **When** an Admin deactivates them, **Then** they can no longer sign in — even with a correct Employee Mail ID and Password — and they no longer appear in attendee or assignee search.
6. **Given** a deactivated member, **When** an Admin reactivates them, **Then** they can sign in again with their Employee Mail ID and Password and regain their prior Role's access.
7. **Given** a deactivated member was the Meeting Owner of one or more meetings, **When** their deactivation is saved, **Then** ownership of all of those meetings transfers automatically to the workspace's configured default Admin.

---

### User Story 10 - Admin Reviews the Activity Log (Priority: P3)

An Admin opens Activity Log and sees a record of who did what and when across meetings, tasks, people, notifications, mentions, and Azure DevOps references.

**Why this priority**: This is an oversight/audit capability that depends on other actions already having happened; it does not gate any other functionality.

**Independent Test**: Can be fully tested by performing a handful of actions (creating a meeting, assigning a task, adding a member) and confirming each appears in the Activity Log with its actor and timestamp.

**Acceptance Scenarios**:

1. **Given** a Team Member is signed in, **When** they try to reach Activity Log, **Then** it is not available to them.
2. **Given** an Admin creates a meeting, assigns a task, mentions a member, or manages a person's account, **When** the Admin opens Activity Log, **Then** each of those actions appears with its actor and timestamp.
3. **Given** a meeting is deleted (cascading its tasks), **When** the Activity Log is viewed, **Then** the cascading deletion is recorded as an entry.

---

### Edge Cases

- What happens when someone selects the "Admin" sign-in option but their account's Role is Team Member (or vice versa)? The option clicked is cosmetic only; the account's actual stored Role determines their access either way.
- What happens when the same account signs in from multiple devices or browser sessions? It resolves to the same single account and the same Role in every session; no duplicate account is created.
- What happens when a Task's Assignee is deactivated or removed from the meeting's Attendee list? The Task keeps its existing assignment but is flagged as needing reassignment; the system does not auto-assign a replacement.
- What happens when a Meeting Owner is deactivated? Ownership of all of their meetings transfers automatically to the workspace's configured default Admin.
- What happens when typing "@" and nothing or letters follow? A member-mention search of that meeting's Attendees appears. When digits follow instead? Azure DevOps Story/Feature suggestions appear. The two are always disambiguated this way.
- What happens when a referenced Azure DevOps work item is later deleted, made inaccessible, or becomes invalid? The Task keeps showing the "@<number>" reference with an "unavailable" indicator, and "Open in Azure DevOps" is disabled.
- What happens when Azure DevOps itself is temporarily unreachable? Everything in MAT keeps working except "@<number>" suggestion lookups.
- What happens when a comment's author is also the Task's Assignee? No comment-notification email is sent to them for their own comment, though @mentions within it still notify the mentioned member.
- What happens when email delivery fails? The underlying task, comment, mention, or assignment operation still completes; the notification is not retried in a way that blocks the user.
- What happens when a Meeting is deleted? All of its Tasks are deleted with it, in a single cascading action recorded once in the Activity Log.
- What happens when the same attendee name is searched and added twice to one meeting? The system treats attendees as a de-duplicated set per meeting.
- What happens when a Team Member who is not an Attendee of a meeting tries to browse to it directly? It does not appear in their Calendar or Previous Meetings, and its details are not accessible to them.
- What happens when a person tries to sign in without checking the "I agree to the Terms and Conditions" checkbox? Sign-in remains disabled on both sign-in options and no sign-in attempt is possible until the checkbox is checked.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST require a successful Employee Mail ID/Password sign-in before granting any access to the workspace; there MUST be no manual sign-up form.
- **FR-002**: The system MUST let a person choose between visually separate Team Member and Admin sign-in options, both of which MUST validate the submitted Employee Mail ID and Password against the same stored credentials. The resulting access MUST be determined solely by the account's actual stored Role, never by which option is used.
- **FR-003**: The system MUST support exactly two roles — Admin and Team Member — with every account having exactly one Role at a time.
- **FR-004**: Only an Admin MUST be able to create a new member account, from the People screen's "Add Member" action, capturing Employee Name, Employee Mail ID, Employee ID, Password, and Role; no self-registration path MUST exist.
- **FR-005**: Only an Admin MUST be able to change an existing member's Role, reset their Password, or deactivate/reactivate them, from the People screen.
- **FR-006**: A deactivated member MUST be unable to sign in — even with a correct Employee Mail ID and Password — and MUST no longer appear in attendee or assignee search results.
- **FR-007**: The system MUST let only an Admin create a new Meeting, and only from the Calendar view.
- **FR-008**: Selecting a date on the Calendar MUST open Create Meeting with that date already filled in.
- **FR-009**: The system MUST reject saving a new Meeting that is missing a Title or a Date.
- **FR-010**: A Meeting MUST be stored with a unique ID, Title, Date, Time, Attendees, Agenda/Notes, and a Meeting Owner equal to the Admin who created it; the Meeting Owner field MUST be system-assigned and MUST NOT be directly editable by anyone.
- **FR-011**: Attendees MUST be added to a Meeting via a search across all internal workspace members by display name or email address.
- **FR-012**: Any Admin MUST be able to edit or delete any Meeting, regardless of who its Meeting Owner is; Team Members MUST NOT be able to create, edit, or delete Meetings.
- **FR-013**: Deleting a Meeting MUST delete all of its Tasks as part of that same action.
- **FR-014**: A Team Member MUST see only Meetings they are an Attendee of, in Calendar and Previous Meetings; an Admin MUST see all Meetings.
- **FR-015**: The system MUST let a person open an existing Meeting to view its Title, Date, Time, Attendees, Agenda/Notes, Meeting Owner, and the Tasks that belong to it.
- **FR-016**: Only the Meeting Owner of a given Meeting MUST be able to assign or reassign the Assignee of that Meeting's Tasks; this MUST NOT be available to any other Admin, regardless of their general edit rights on the Meeting.
- **FR-017**: Each Task MUST belong to exactly one Meeting and MUST be assigned to exactly one Attendee of that Meeting; assigning a Task to anyone who is not an Attendee of its Meeting MUST be rejected.
- **FR-018**: A Task MUST be stored with a unique ID, Task Title, Description/Notes, its parent Meeting ID, Assignee, Due Date, and Status.
- **FR-019**: A newly created Task MUST default to status "To Do."
- **FR-020**: Task Status MUST be exactly one of To Do, In Progress, or Completed, displayed as columns with live counts.
- **FR-021**: The system MUST let a Task's Assignee change that Task's Status via drag-and-drop between columns and via a direct status control, with both mechanisms producing the same result, and MUST allow this only for Tasks assigned to them.
- **FR-022**: A Task's Assignee MUST be able to edit that Task's Description/Notes; its Title, Due Date, and Assignee MUST remain controlled by the Meeting Owner/Admins and MUST NOT be editable by the Assignee.
- **FR-023**: A Task's Assignee MUST NOT be able to delete that Task.
- **FR-024**: When a Task's Assignee is deactivated or removed from the parent Meeting's Attendee list, the Task MUST keep its existing assignment and MUST be flagged as needing reassignment; the system MUST NOT automatically assign a replacement.
- **FR-025**: The system MUST provide a "My Tasks" view showing every Task assigned to the current authenticated person across all Meetings they can access, each labelled with its parent Meeting's name, using the same Status columns, drag-and-drop, and edit permissions as that Meeting's own Task Board.
- **FR-026**: Assigning a Task MUST search only within that Meeting's Attendees, by display name or email address.
- **FR-027**: The system MUST let the Meeting Owner, the Task's Assignee, or any Admin post comments on a Task; no one else MUST be able to.
- **FR-028**: Typing "@" followed by nothing or by letters, in a Task's Title, Description/Notes, or a comment, MUST open a search of that Meeting's Attendees for selecting a member mention (e.g., "@John").
- **FR-029**: Typing "@" followed by digits, in the same three places, MUST show Azure DevOps Story/Feature suggestions instead of a member-mention search, each showing at least ID, Title, and Type, scoped to the current authenticated user's own Azure DevOps access.
- **FR-030**: Every "@<number>" token found in a Task's Title, Description/Notes, or Comments MUST be treated as a Linked Azure DevOps Item and displayed as "ADO #<id> — <title>" with its own "Open in Azure DevOps" action; there MUST be no separate, dedicated Azure DevOps reference field.
- **FR-031**: Referencing an Azure DevOps Story or Feature from MAT MUST NOT create or modify any Azure DevOps work item.
- **FR-032**: If a Linked Azure DevOps Item's underlying work item becomes deleted, inaccessible, or invalid, the Task MUST keep displaying that reference with an "unavailable" indicator, and its "Open in Azure DevOps" action MUST be disabled.
- **FR-033**: MAT MUST remain fully usable if the Azure DevOps integration is temporarily unavailable; only "@<number>" suggestion lookups MUST be affected.
- **FR-034**: The system MUST send an email notification to a Task's Assignee when that Task is assigned to them.
- **FR-035**: The system MUST send an email notification to a Task's Assignee when a comment is posted on that Task by someone other than the Assignee themself.
- **FR-036**: The system MUST send an email notification to any member who is "@"-mentioned in a Task comment, independent of any assignee notification for that same comment.
- **FR-037**: Email notifications MUST include enough context (task, meeting, sender, assignee, due date, comment/message, and Azure DevOps reference information where applicable) for the recipient to understand why they were notified.
- **FR-038**: A failure to deliver an email notification MUST NOT lose or block the underlying task, comment, mention, or assignment operation.
- **FR-039**: The system MUST provide a "Previous Meetings" view listing the meetings the current person is permitted to see, with title, date, and current task count, and MUST let them open any listed meeting's full details from there.
- **FR-040**: If a Meeting Owner is deactivated, ownership of all of their Meetings MUST transfer automatically to the workspace's configured default Admin.
- **FR-041**: The system MUST provide an Activity Log, visible to Admins only, recording actor and timestamp for key business actions across Meetings, Tasks, People, Notifications, Mentions, and Azure DevOps references.
- **FR-042**: The system's navigation MUST expose exactly these destinations, gated by Role: Calendar, My Tasks, and Previous Meetings for every signed-in person, plus People and Activity Log for Admins only.
- **FR-043**: Any change made by one person (creating/editing/deleting a meeting or task, changing a task's status, posting a comment, managing a person) MUST become visible to other people permitted to see that data from a different session or device, without requiring anything beyond normal navigation/refresh.
- **FR-044**: The system MUST remain fully usable, with all actions reachable and no loss of functionality, on both desktop and mobile-sized screens.
- **FR-045**: The Login screen MUST present an "I agree to the Terms and Conditions" checkbox, and sign-in MUST remain disabled on both sign-in options until that checkbox is checked; sign-in MUST NOT be possible while it is unchecked.
- **FR-046**: On a successful sign-in, the system MUST record that the signed-in account has accepted the Terms and Conditions.

### Key Entities

- **User**: A workspace member's account, created only by an Admin from the People screen. Key attributes: unique ID, Employee Name, Employee Mail ID (sign-in identifier and notification address), Employee ID, Password (Admin-set and Admin-resettable), Role (Admin or Team Member; set at creation, changeable only by an Admin afterward), Active flag, Terms Accepted flag (set when the person checks "I agree to the Terms and Conditions" to sign in). Can be a Meeting Owner, an Attendee, a Task Assignee, or a comment author.
- **Meeting**: A scheduled meeting. Key attributes: unique ID, Title, Date, Time, Attendees (a set of Users), Agenda/Notes, Meeting Owner (the creating Admin, system-assigned and read-only). Owns a collection of Tasks.
- **Task**: A single action item belonging to exactly one Meeting. Key attributes: unique ID, Task Title, Description/Notes, `meetingId`, Assignee (one Attendee of the parent Meeting), Due Date, Status (`To Do`, `In Progress`, or `Completed`), and a needs-reassignment flag. Owns a collection of Comments and derives a collection of Linked Azure DevOps Items.
- **Comment**: A message posted against a Task. Key attributes: unique ID, author, message text, timestamp, the mentions and Azure DevOps reference tokens it contains.
- **Linked Azure DevOps Item** *(derived, read-only)*: A Story or Feature detected from an "@<number>" token in a Task's Title, Description/Notes, or Comments. Key attributes: ID, Title, Type, link, availability status. Not a separately editable field.
- **Activity Log Entry**: A record of one business action. Key attributes: actor, action description, timestamp, and the entity it relates to.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A person can sign in and reach the workspace appropriate to their Role in under 10 seconds.
- **SC-002**: An Admin can create a new meeting with a title, date, time, and at least one attendee in under 1 minute.
- **SC-003**: A meeting, task, comment, or account change made in one session becomes visible in a second, independent session permitted to see that data, without any action beyond opening or refreshing that view.
- **SC-004**: 100% of tasks in the system are associated with exactly one meeting and exactly one assignee at all times, and every task-assignee change is traceable to that meeting's Meeting Owner.
- **SC-005**: A Team Member can move one of their own tasks to a different status column, by drag-and-drop or by direct selection, in a single interaction, with the change reflected immediately in every view showing that task.
- **SC-006**: Every task assignment, non-self-authored comment, and @mention results in a notification reaching the intended recipient's inbox in the vast majority of cases, and never blocks or loses the underlying action even when notification delivery fails.
- **SC-007**: An "@<number>" token typed anywhere it is supported (Title, Description/Notes, Comments) resolves to a visibly distinct Linked Azure DevOps Item, correctly disambiguated from an "@Name" member mention, in 100% of sampled cases during testing.
- **SC-008**: The application's Login, Calendar, Meeting Details/Task Board, My Tasks, Previous Meetings, People, and Activity Log views are each fully operable — no missing controls, no horizontal scrolling required to reach content — on both a common desktop screen width and a common mobile screen width.
- **SC-009**: Previous Meetings always reports a task count for each meeting that matches the number of tasks actually open under that meeting's details, verified across at least 95% of sampled meetings in testing.
- **SC-010**: Deactivating a Meeting Owner results in ownership of all of their meetings appearing under the configured default Admin on the very next view of those meetings, with no manual intervention.

## Assumptions

- **BRD is authoritative and fully in scope.** This specification implements the complete BRD.docx feature set, including its original Employee Mail ID/Password authentication, Admin-only account-creation model (People "Add Member"), and local, file-based (SQLite) database. The 2026-09-14 switch to MongoDB was reverted on 2026-09-15 — no amendment to the original BRD-specified storage approach remains in effect. A brief, interim switch to Google Sign-In was likewise made and reverted on 2026-09-15; this specification reflects the reverted (original BRD) authentication model. The provided mockup (`mockup.html`) is used for visual/layout direction (screen names, field names, status values, and action names), consistent with the BRD's Employee Mail ID/Password login.
- **A single "default Admin" is configured for meeting-ownership continuity.** The BRD requires that a deactivated Meeting Owner's meetings transfer to "the workspace's configured default Admin"; this specification assumes exactly one such Admin is designated for the workspace at any time, without prescribing how that designation is made (an implementation-level configuration concern for planning).
- **Out of scope**: creating, editing, or syncing Azure DevOps work items from MAT; referencing Azure DevOps work item types other than Story and Feature; notification channels other than email; multiple assignees per task; external/guest meeting attendees; any general-purpose chat feature separate from task comments; and any external identity system or single sign-on (including Google Sign-In) — sign-in is Employee Mail ID/Password only.
- **No removal of the Meeting Owner role from a meeting.** A Meeting always has exactly one Meeting Owner (its creator, or the configured default Admin after an ownership transfer); this specification does not include manually reassigning ownership to an arbitrary different Admin outside of the deactivation-triggered transfer.
- **Mobile and desktop breakpoints** follow standard responsive web practice (a single-column, stacked layout on narrow/mobile widths; multi-column grid/board layouts on wider/desktop widths), consistent with the mockup's visual direction.
