import { useEffect } from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AuthProvider, useAuth } from "../../src/context/AuthContext";
import { MyTasksPage } from "../../src/pages/MyTasksPage";
import * as authApi from "../../src/services/authApi";
import * as tasksApi from "../../src/services/tasksApi";

function SignInAsSarah({ children }: { children: React.ReactNode }) {
  const { login } = useAuth();
  useEffect(() => {
    login("sarah@example.com", "Password123!", true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return <>{children}</>;
}

describe("My Tasks page", () => {
  beforeEach(() => {
    sessionStorage.clear();
    vi.restoreAllMocks();
  });

  function mockSignIn() {
    vi.spyOn(authApi, "login").mockResolvedValue({
      accessToken: "token-sarah",
      user: {
        id: 7,
        employeeName: "Sarah Iyer",
        employeeMailId: "sarah@example.com",
        employeeId: "E1042",
        role: "TEAM_MEMBER",
        isActive: true,
        termsAccepted: true,
      },
    });
  }

  function renderPage() {
    render(
      <MemoryRouter initialEntries={["/my-tasks"]}>
        <AuthProvider>
          <SignInAsSarah>
            <Routes>
              <Route path="/my-tasks" element={<MyTasksPage />} />
            </Routes>
          </SignInAsSarah>
        </AuthProvider>
      </MemoryRouter>,
    );
  }

  it("shows only the signed-in user's own tasks, labelled by meeting, with no delete control", async () => {
    mockSignIn();
    vi.spyOn(tasksApi, "listMyTasks").mockResolvedValue([
      {
        id: 101,
        meetingId: 12,
        meetingTitle: "Q3 Roadmap Review",
        title: "Prepare onboarding API design doc",
        descriptionNotes: "See related work.",
        dueDate: "2026-09-20",
        status: "TODO",
        needsReassignment: false,
      },
    ]);

    renderPage();

    expect(await screen.findByText(/prepare onboarding api design doc/i)).toBeInTheDocument();
    expect(screen.getByText(/q3 roadmap review/i)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /delete/i })).not.toBeInTheDocument();
  });

  it("lets the assignee edit Description/Notes without changing Title/Due Date", async () => {
    const user = userEvent.setup();
    mockSignIn();
    vi.spyOn(tasksApi, "listMyTasks").mockResolvedValue([
      {
        id: 101,
        meetingId: 12,
        meetingTitle: "Q3 Roadmap Review",
        title: "Prepare onboarding API design doc",
        descriptionNotes: "Original notes",
        dueDate: "2026-09-20",
        status: "TODO",
        needsReassignment: false,
      },
    ]);
    const updateDescriptionSpy = vi
      .spyOn(tasksApi, "updateTaskDescription")
      .mockResolvedValue({
        id: 101,
        meetingId: 12,
        meetingTitle: "Q3 Roadmap Review",
        title: "Prepare onboarding API design doc",
        descriptionNotes: "Updated notes",
        dueDate: "2026-09-20",
        status: "TODO",
        needsReassignment: false,
      });

    renderPage();

    await user.click(await screen.findByRole("button", { name: /edit description\/notes/i }));
    const textarea = await screen.findByLabelText(/description \/ notes/i);
    await user.clear(textarea);
    await user.type(textarea, "Updated notes");
    await user.click(screen.getByRole("button", { name: /save/i }));

    await waitFor(() =>
      expect(updateDescriptionSpy).toHaveBeenCalledWith(101, "Updated notes"),
    );
    expect(screen.getByText(/prepare onboarding api design doc/i)).toBeInTheDocument();
  });
});
