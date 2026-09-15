import { useEffect } from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AuthProvider, useAuth } from "../../src/context/AuthContext";
import { PreviousMeetingsPage } from "../../src/pages/PreviousMeetingsPage";
import * as authApi from "../../src/services/authApi";
import * as meetingsApi from "../../src/services/meetingsApi";

const ADMIN = {
  id: 3,
  employeeName: "John Admin",
  employeeMailId: "john@example.com",
  employeeId: "E0001",
  role: "ADMIN" as const,
  isActive: true,
};

function SignInAsAdmin({ children }: { children: React.ReactNode }) {
  const { login } = useAuth();
  useEffect(() => {
    login(ADMIN.employeeMailId, "Password123!");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return <>{children}</>;
}

function renderPage() {
  return render(
    <MemoryRouter initialEntries={["/previous-meetings"]}>
      <AuthProvider>
        <SignInAsAdmin>
          <Routes>
            <Route path="/previous-meetings" element={<PreviousMeetingsPage />} />
            <Route path="/meetings/:meetingId" element={<div>Meeting Details Page</div>} />
          </Routes>
        </SignInAsAdmin>
      </AuthProvider>
    </MemoryRouter>,
  );
}

describe("Previous Meetings page", () => {
  beforeEach(() => {
    sessionStorage.clear();
    vi.restoreAllMocks();
  });

  it("lists every visible meeting with its title, date, owner, and task count", async () => {
    vi.spyOn(authApi, "login").mockResolvedValue({ accessToken: "token", user: ADMIN });
    vi.spyOn(meetingsApi, "listMeetings").mockResolvedValue([
      {
        id: 12,
        title: "Q3 Roadmap Review",
        date: "2026-09-15",
        time: "14:00",
        ownerId: ADMIN.id,
        ownerName: ADMIN.employeeName,
        taskCount: 4,
      },
      {
        id: 13,
        title: "Sprint Planning",
        date: "2026-09-10",
        time: "10:00",
        ownerId: ADMIN.id,
        ownerName: ADMIN.employeeName,
        taskCount: 0,
      },
    ]);

    renderPage();

    expect(await screen.findByText("Q3 Roadmap Review")).toBeInTheDocument();
    expect(screen.getByText("Sprint Planning")).toBeInTheDocument();
    expect(screen.getByText("4 tasks")).toBeInTheDocument();
    expect(screen.getByText("0 tasks")).toBeInTheDocument();
    expect(screen.getAllByText(ADMIN.employeeName)).toHaveLength(2);
  });

  it("shows an empty state when no meetings are visible", async () => {
    vi.spyOn(authApi, "login").mockResolvedValue({ accessToken: "token", user: ADMIN });
    vi.spyOn(meetingsApi, "listMeetings").mockResolvedValue([]);

    renderPage();

    expect(await screen.findByText(/no meetings available to you yet/i)).toBeInTheDocument();
  });

  it("opens a meeting's full details when selected", async () => {
    const user = userEvent.setup();
    vi.spyOn(authApi, "login").mockResolvedValue({ accessToken: "token", user: ADMIN });
    vi.spyOn(meetingsApi, "listMeetings").mockResolvedValue([
      {
        id: 12,
        title: "Q3 Roadmap Review",
        date: "2026-09-15",
        time: "14:00",
        ownerId: ADMIN.id,
        ownerName: ADMIN.employeeName,
        taskCount: 1,
      },
    ]);

    renderPage();

    await user.click(await screen.findByRole("button", { name: /open meeting details/i }));

    expect(await screen.findByText("Meeting Details Page")).toBeInTheDocument();
  });
});
