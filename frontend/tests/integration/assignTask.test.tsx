import { useEffect } from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AuthProvider, useAuth } from "../../src/context/AuthContext";
import { MeetingDetailsPage } from "../../src/pages/MeetingDetailsPage";
import * as authApi from "../../src/services/authApi";
import * as meetingsApi from "../../src/services/meetingsApi";
import * as tasksApi from "../../src/services/tasksApi";
import type { MeetingDetail } from "../../src/services/meetingsApi";

const OWNER = {
  id: 3,
  employeeName: "John Owner",
  employeeMailId: "john@example.com",
  employeeId: "E0001",
  role: "ADMIN" as const,
  isActive: true,
  termsAccepted: true,
};

const OTHER_ADMIN = {
  id: 9,
  employeeName: "Priya Admin",
  employeeMailId: "priya@example.com",
  employeeId: "E0009",
  role: "ADMIN" as const,
  isActive: true,
  termsAccepted: true,
};

const ATTENDEE = { id: 7, employeeName: "Sarah Iyer" };

function meetingDetail(): MeetingDetail {
  return {
    id: 42,
    title: "Q3 Roadmap Review",
    date: "2026-09-15",
    time: "10:00",
    agendaNotes: "Discuss roadmap.",
    ownerId: OWNER.id,
    ownerName: OWNER.employeeName,
    attendees: [{ id: OWNER.id, employeeName: OWNER.employeeName }, ATTENDEE],
    tasks: [],
  };
}

function SignInAs({ user, children }: { user: typeof OWNER; children: React.ReactNode }) {
  const { login } = useAuth();
  useEffect(() => {
    login(user.employeeMailId, "Password123!", true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return <>{children}</>;
}

function renderMeetingDetails(user: typeof OWNER) {
  return render(
    <MemoryRouter initialEntries={["/meetings/42"]}>
      <AuthProvider>
        <SignInAs user={user}>
          <Routes>
            <Route path="/meetings/:meetingId" element={<MeetingDetailsPage />} />
          </Routes>
        </SignInAs>
      </AuthProvider>
    </MemoryRouter>,
  );
}

describe("Assign task flow", () => {
  beforeEach(() => {
    sessionStorage.clear();
    vi.restoreAllMocks();
  });

  it("lets the Meeting Owner create a task and assign it to an attendee", async () => {
    const user = userEvent.setup();
    vi.spyOn(authApi, "login").mockResolvedValue({ accessToken: "token-owner", user: OWNER });
    vi.spyOn(meetingsApi, "getMeetingDetail").mockResolvedValue(meetingDetail());
    const createTaskSpy = vi.spyOn(tasksApi, "createTask").mockResolvedValue({
      id: 501,
      meetingId: 42,
      title: "Prepare notes",
      descriptionNotes: null,
      assigneeId: ATTENDEE.id,
      assigneeName: ATTENDEE.employeeName,
      dueDate: null,
      status: "TODO",
      needsReassignment: false,
    });

    renderMeetingDetails(OWNER);

    const addTaskButton = await screen.findByRole("button", { name: /create task/i });
    await user.click(addTaskButton);

    await user.type(screen.getByLabelText(/task title/i), "Prepare notes");
    await user.selectOptions(screen.getByLabelText(/assignee/i), String(ATTENDEE.id));
    await user.click(screen.getByRole("button", { name: /^save$/i }));

    await waitFor(() =>
      expect(createTaskSpy).toHaveBeenCalledWith(
        42,
        expect.objectContaining({ title: "Prepare notes", assigneeId: ATTENDEE.id }),
      ),
    );
  });

  it("does not let a non-Owner Admin change the task's assignee", async () => {
    const user = userEvent.setup();
    vi.spyOn(authApi, "login").mockResolvedValue({
      accessToken: "token-other-admin",
      user: OTHER_ADMIN,
    });
    const detail = meetingDetail();
    detail.tasks = [
      {
        id: 501,
        meetingId: 42,
        title: "Prepare notes",
        descriptionNotes: null,
        assigneeId: ATTENDEE.id,
        assigneeName: ATTENDEE.employeeName,
        dueDate: null,
        status: "TODO",
        needsReassignment: false,
      },
    ];
    vi.spyOn(meetingsApi, "getMeetingDetail").mockResolvedValue(detail);

    renderMeetingDetails(OTHER_ADMIN);

    expect(screen.queryByRole("button", { name: /create task/i })).not.toBeInTheDocument();

    await user.click(await screen.findByText("Prepare notes"));

    expect(await screen.findByText(/only the meeting owner can assign/i)).toBeInTheDocument();
    const assigneeField = screen.getByLabelText(/assignee/i);
    expect(assigneeField).toBeDisabled();
    expect(assigneeField).toHaveValue(ATTENDEE.employeeName);
  });
});
