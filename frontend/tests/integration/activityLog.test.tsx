import { useEffect } from "react";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AuthProvider, useAuth } from "../../src/context/AuthContext";
import { ActivityLogPage } from "../../src/pages/ActivityLogPage";
import * as activityLogApi from "../../src/services/activityLogApi";
import * as authApi from "../../src/services/authApi";

const ADMIN = {
  id: 3,
  employeeName: "John Admin",
  employeeMailId: "john@example.com",
  employeeId: "E0001",
  role: "ADMIN" as const,
  isActive: true,
  termsAccepted: true,
};

function SignInAsAdmin({ children }: { children: React.ReactNode }) {
  const { login } = useAuth();
  useEffect(() => {
    login(ADMIN.employeeMailId, "Password123!", true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return <>{children}</>;
}

function renderPage() {
  return render(
    <MemoryRouter>
      <AuthProvider>
        <SignInAsAdmin>
          <ActivityLogPage />
        </SignInAsAdmin>
      </AuthProvider>
    </MemoryRouter>,
  );
}

describe("Activity Log page", () => {
  beforeEach(() => {
    sessionStorage.clear();
    vi.restoreAllMocks();
  });

  it("shows every logged action with its actor and timestamp", async () => {
    vi.spyOn(authApi, "login").mockResolvedValue({ accessToken: "token", user: ADMIN });
    vi.spyOn(activityLogApi, "getActivityLog").mockResolvedValue([
      {
        id: 901,
        actorId: 3,
        actorName: "John Admin",
        action: "MEETING_DELETED",
        entityType: "Meeting",
        entityId: 12,
        timestamp: "2026-09-14T11:05:00Z",
      },
      {
        id: 902,
        actorId: 3,
        actorName: "John Admin",
        action: "TASK_CREATED",
        entityType: "Task",
        entityId: 4,
        timestamp: "2026-09-14T10:00:00Z",
      },
    ]);

    renderPage();

    expect(await screen.findByText(/Meeting Deleted \(Meeting #12\)/)).toBeInTheDocument();
    expect(screen.getByText(/Task Created \(Task #4\)/)).toBeInTheDocument();
    expect(screen.getAllByText("John Admin")).toHaveLength(2);
  });

  it("shows an empty state when no activity has been recorded", async () => {
    vi.spyOn(authApi, "login").mockResolvedValue({ accessToken: "token", user: ADMIN });
    vi.spyOn(activityLogApi, "getActivityLog").mockResolvedValue([]);

    renderPage();

    expect(await screen.findByText(/no activity recorded yet/i)).toBeInTheDocument();
  });
});
