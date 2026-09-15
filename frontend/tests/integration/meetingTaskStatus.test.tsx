import { useEffect } from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AuthProvider, useAuth } from "../../src/context/AuthContext";
import { MeetingDetailsPage } from "../../src/pages/MeetingDetailsPage";
import type { AuthUser } from "../../src/services/authApi";
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

const ASSIGNEE = {
  id: 7,
  employeeName: "Sarah Iyer",
  employeeMailId: "sarah@example.com",
  employeeId: "E1042",
  role: "TEAM_MEMBER" as const,
  isActive: true,
  termsAccepted: true,
};

function meetingDetail(): MeetingDetail {
  return {
    id: 42,
    title: "Q3 Roadmap Review",
    date: "2026-09-15",
    time: "10:00",
    agendaNotes: "Discuss roadmap.",
    ownerId: OWNER.id,
    ownerName: OWNER.employeeName,
    attendees: [
      { id: OWNER.id, employeeName: OWNER.employeeName },
      { id: ASSIGNEE.id, employeeName: ASSIGNEE.employeeName },
    ],
    tasks: [
      {
        id: 501,
        meetingId: 42,
        title: "Prepare notes",
        descriptionNotes: null,
        assigneeId: ASSIGNEE.id,
        assigneeName: ASSIGNEE.employeeName,
        dueDate: null,
        status: "TODO",
        needsReassignment: false,
      },
    ],
  };
}

function SignInAs({ user, children }: { user: AuthUser; children: React.ReactNode }) {
  const { login } = useAuth();
  useEffect(() => {
    login(user.employeeMailId, "Password123!", true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return <>{children}</>;
}

function renderMeetingDetails(user: AuthUser) {
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

describe("Meeting Details Task Board status changes", () => {
  beforeEach(() => {
    sessionStorage.clear();
    vi.restoreAllMocks();
  });

  it("lets the task's own Assignee change its status from the board", async () => {
    const user = userEvent.setup();
    vi.spyOn(authApi, "login").mockResolvedValue({ accessToken: "token", user: ASSIGNEE });
    vi.spyOn(meetingsApi, "getMeetingDetail").mockResolvedValue(meetingDetail());
    const updateStatusSpy = vi.spyOn(tasksApi, "updateTaskStatus").mockResolvedValue({
      ...meetingDetail().tasks[0],
      status: "IN_PROGRESS",
    });

    renderMeetingDetails(ASSIGNEE);

    const statusSelect = await screen.findByLabelText(/status/i);
    expect(statusSelect).not.toBeDisabled();
    await user.selectOptions(statusSelect, "IN_PROGRESS");

    await waitFor(() => expect(updateStatusSpy).toHaveBeenCalledWith(501, "IN_PROGRESS"));
  });

  it("disables status control for a non-Assignee (e.g. the Meeting Owner)", async () => {
    vi.spyOn(authApi, "login").mockResolvedValue({ accessToken: "token", user: OWNER });
    vi.spyOn(meetingsApi, "getMeetingDetail").mockResolvedValue(meetingDetail());
    const updateStatusSpy = vi.spyOn(tasksApi, "updateTaskStatus");

    renderMeetingDetails(OWNER);

    const statusSelect = await screen.findByLabelText(/status/i);
    expect(statusSelect).toBeDisabled();
    expect(screen.getByText(/only the assignee can drag or change/i)).toBeInTheDocument();
    expect(updateStatusSpy).not.toHaveBeenCalled();
  });
});
