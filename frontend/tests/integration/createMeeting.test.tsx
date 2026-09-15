import { useEffect } from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AuthProvider, useAuth } from "../../src/context/AuthContext";
import { CreateMeetingPage } from "../../src/pages/CreateMeetingPage";
import * as authApi from "../../src/services/authApi";
import * as meetingsApi from "../../src/services/meetingsApi";
import * as usersApi from "../../src/services/usersApi";

function SignInAsAdmin({ children }: { children: React.ReactNode }) {
  const { login } = useAuth();
  useEffect(() => {
    login("john@example.com", "Password123!", true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return <>{children}</>;
}

describe("Create meeting flow", () => {
  beforeEach(() => {
    sessionStorage.clear();
    vi.restoreAllMocks();
  });

  it("prefills the selected date, requires a Title, and searches attendees", async () => {
    const user = userEvent.setup();
    vi.spyOn(authApi, "login").mockResolvedValue({
      accessToken: "token-admin",
      user: {
        id: 3,
        employeeName: "John",
        employeeMailId: "john@example.com",
        employeeId: "E0001",
        role: "ADMIN",
        isActive: true,
        termsAccepted: true,
      },
    });
    vi.spyOn(usersApi, "searchUsers").mockResolvedValue([
      {
        id: 7,
        employeeName: "Sarah Iyer",
        employeeMailId: "sarah@example.com",
        employeeId: "E1042",
        role: "TEAM_MEMBER",
        isActive: true,
      },
    ]);
    const createMeetingSpy = vi.spyOn(meetingsApi, "createMeeting").mockResolvedValue({
      id: 99,
      title: "Weekly Sync",
      date: "2026-09-15",
      time: "14:00",
      ownerId: 3,
      ownerName: "John",
      taskCount: 0,
    });
    vi.spyOn(meetingsApi, "listMeetings").mockResolvedValue([]);

    render(
      <MemoryRouter initialEntries={["/meetings/new?date=2026-09-15"]}>
        <AuthProvider>
          <SignInAsAdmin>
            <Routes>
              <Route path="/meetings/new" element={<CreateMeetingPage />} />
            </Routes>
          </SignInAsAdmin>
        </AuthProvider>
      </MemoryRouter>,
    );

    await waitFor(() => expect(screen.getByLabelText(/date/i)).toHaveValue("2026-09-15"));

    await user.click(screen.getByRole("button", { name: /save meeting/i }));
    expect(screen.getByRole("alert")).toHaveTextContent(/title is required/i);
    expect(createMeetingSpy).not.toHaveBeenCalled();

    await user.type(screen.getByLabelText(/title/i), "Weekly Sync");
    await user.type(
      screen.getByPlaceholderText(/search internal members/i),
      "Sarah",
    );
    expect(await screen.findByText(/sarah iyer/i)).toBeInTheDocument();
    await user.click(screen.getByText(/sarah iyer/i));

    await user.click(screen.getByRole("button", { name: /save meeting/i }));

    await waitFor(() =>
      expect(createMeetingSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          title: "Weekly Sync",
          date: "2026-09-15",
          attendeeIds: expect.arrayContaining([3, 7]),
        }),
      ),
    );
  });
});
