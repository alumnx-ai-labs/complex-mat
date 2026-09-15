import { useEffect } from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AuthProvider, useAuth } from "../../src/context/AuthContext";
import { NavSidebar } from "../../src/components/layout/NavSidebar";
import * as authApi from "../../src/services/authApi";

function SignInAs() {
  const { login } = useAuth();
  useEffect(() => {
    login("user@example.com", "Password123!", true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return <NavSidebar />;
}

describe("Role-gated navigation", () => {
  beforeEach(() => {
    sessionStorage.clear();
    vi.restoreAllMocks();
  });

  it("hides People and Activity Log for a Team Member", async () => {
    vi.spyOn(authApi, "login").mockResolvedValue({
      accessToken: "token-team-member",
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

    render(
      <MemoryRouter>
        <AuthProvider>
          <SignInAs />
        </AuthProvider>
      </MemoryRouter>,
    );

    await waitFor(() =>
      expect(screen.getByRole("link", { name: /calendar/i })).toBeInTheDocument(),
    );
    expect(screen.getByRole("link", { name: /my tasks/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /previous meetings/i })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /people/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /activity log/i })).not.toBeInTheDocument();
  });

  it("shows every destination for an Admin", async () => {
    vi.spyOn(authApi, "login").mockResolvedValue({
      accessToken: "token-admin",
      user: {
        id: 3,
        employeeName: "John Admin",
        employeeMailId: "john@example.com",
        employeeId: "E0001",
        role: "ADMIN",
        isActive: true,
        termsAccepted: true,
      },
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <SignInAs />
        </AuthProvider>
      </MemoryRouter>,
    );

    await waitFor(() =>
      expect(screen.getByRole("link", { name: /people/i })).toBeInTheDocument(),
    );
    expect(screen.getByRole("link", { name: /calendar/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /my tasks/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /previous meetings/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /activity log/i })).toBeInTheDocument();
  });
});
