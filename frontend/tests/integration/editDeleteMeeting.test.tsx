import { useEffect } from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AuthProvider, useAuth } from "../../src/context/AuthContext";
import { EditMeetingPage } from "../../src/pages/EditMeetingPage";
import { MeetingDetailsPage } from "../../src/pages/MeetingDetailsPage";
import type { AuthUser } from "../../src/services/authApi";
import * as authApi from "../../src/services/authApi";
import * as meetingsApi from "../../src/services/meetingsApi";
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

const TEAM_MEMBER = {
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
      { id: TEAM_MEMBER.id, employeeName: TEAM_MEMBER.employeeName },
    ],
    tasks: [],
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

function renderApp(user: AuthUser, initialEntry = "/meetings/42") {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <AuthProvider>
        <SignInAs user={user}>
          <Routes>
            <Route path="/calendar" element={<div>Calendar Page</div>} />
            <Route path="/meetings/:meetingId" element={<MeetingDetailsPage />} />
            <Route path="/meetings/:meetingId/edit" element={<EditMeetingPage />} />
          </Routes>
        </SignInAs>
      </AuthProvider>
    </MemoryRouter>,
  );
}

describe("Edit and delete meeting flow", () => {
  beforeEach(() => {
    sessionStorage.clear();
    vi.restoreAllMocks();
  });

  it("shows Edit/Delete Meeting controls to any Admin, including a non-Owner", async () => {
    vi.spyOn(authApi, "login").mockResolvedValue({ accessToken: "token", user: OTHER_ADMIN });
    vi.spyOn(meetingsApi, "getMeetingDetail").mockResolvedValue(meetingDetail());

    renderApp(OTHER_ADMIN);

    expect(await screen.findByRole("button", { name: /edit meeting/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /delete meeting/i })).toBeInTheDocument();
  });

  it("hides Edit/Delete Meeting controls from a Team Member", async () => {
    vi.spyOn(authApi, "login").mockResolvedValue({ accessToken: "token", user: TEAM_MEMBER });
    vi.spyOn(meetingsApi, "getMeetingDetail").mockResolvedValue(meetingDetail());

    renderApp(TEAM_MEMBER);

    await screen.findByText("Q3 Roadmap Review");
    expect(screen.queryByRole("button", { name: /edit meeting/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /delete meeting/i })).not.toBeInTheDocument();
  });

  it("lets a non-Owner Admin edit Title/Date/Time/Attendees/Agenda without touching the Owner", async () => {
    const user = userEvent.setup();
    vi.spyOn(authApi, "login").mockResolvedValue({ accessToken: "token", user: OTHER_ADMIN });
    vi.spyOn(meetingsApi, "getMeetingDetail").mockResolvedValue(meetingDetail());
    const updateMeetingSpy = vi.spyOn(meetingsApi, "updateMeeting").mockResolvedValue({
      ...meetingDetail(),
      title: "Q3 Roadmap Review (rescheduled)",
    });

    renderApp(OTHER_ADMIN);

    await user.click(await screen.findByRole("button", { name: /edit meeting/i }));

    const titleInput = await screen.findByLabelText(/title/i);
    await user.clear(titleInput);
    await user.type(titleInput, "Q3 Roadmap Review (rescheduled)");
    await user.click(screen.getByRole("button", { name: /save changes/i }));

    await waitFor(() =>
      expect(updateMeetingSpy).toHaveBeenCalledWith(
        42,
        expect.objectContaining({ title: "Q3 Roadmap Review (rescheduled)" }),
      ),
    );
    const [, payload] = updateMeetingSpy.mock.calls[0];
    expect(payload).not.toHaveProperty("ownerId");
  });

  it("deletes the meeting after confirmation and returns to Calendar", async () => {
    const user = userEvent.setup();
    vi.spyOn(authApi, "login").mockResolvedValue({ accessToken: "token", user: OWNER });
    vi.spyOn(meetingsApi, "getMeetingDetail").mockResolvedValue(meetingDetail());
    const deleteMeetingSpy = vi.spyOn(meetingsApi, "deleteMeeting").mockResolvedValue(undefined);
    vi.spyOn(window, "confirm").mockReturnValue(true);

    renderApp(OWNER);

    await user.click(await screen.findByRole("button", { name: /delete meeting/i }));

    await waitFor(() => expect(deleteMeetingSpy).toHaveBeenCalledWith(42));
    expect(await screen.findByText("Calendar Page")).toBeInTheDocument();
  });

  it("does not delete the meeting when the confirmation is declined", async () => {
    const user = userEvent.setup();
    vi.spyOn(authApi, "login").mockResolvedValue({ accessToken: "token", user: OWNER });
    vi.spyOn(meetingsApi, "getMeetingDetail").mockResolvedValue(meetingDetail());
    const deleteMeetingSpy = vi.spyOn(meetingsApi, "deleteMeeting").mockResolvedValue(undefined);
    vi.spyOn(window, "confirm").mockReturnValue(false);

    renderApp(OWNER);

    await user.click(await screen.findByRole("button", { name: /delete meeting/i }));

    expect(deleteMeetingSpy).not.toHaveBeenCalled();
    expect(screen.getByText("Q3 Roadmap Review")).toBeInTheDocument();
  });
});
