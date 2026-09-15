import { useEffect } from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AuthProvider, useAuth } from "../../src/context/AuthContext";
import { PeoplePage } from "../../src/pages/PeoplePage";
import * as authApi from "../../src/services/authApi";
import * as usersApi from "../../src/services/usersApi";
import type { UserSummary } from "../../src/services/usersApi";

const ADMIN = {
  id: 3,
  employeeName: "John Admin",
  employeeMailId: "john@example.com",
  employeeId: "E0001",
  role: "ADMIN" as const,
  isActive: true,
  termsAccepted: true,
};

const MEMBER: UserSummary = {
  id: 7,
  employeeName: "Sarah Iyer",
  employeeMailId: "sarah@example.com",
  employeeId: "E1042",
  role: "TEAM_MEMBER",
  isActive: true,
};

function SignInAsAdmin({ children }: { children: React.ReactNode }) {
  const { login } = useAuth();
  useEffect(() => {
    login(ADMIN.employeeMailId, "Password123!", true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return <>{children}</>;
}

function renderPeoplePage() {
  return render(
    <MemoryRouter>
      <AuthProvider>
        <SignInAsAdmin>
          <PeoplePage />
        </SignInAsAdmin>
      </AuthProvider>
    </MemoryRouter>,
  );
}

describe("People management", () => {
  beforeEach(() => {
    sessionStorage.clear();
    vi.restoreAllMocks();
  });

  it("lists members and lets an Admin add a new member", async () => {
    const user = userEvent.setup();
    vi.spyOn(authApi, "login").mockResolvedValue({ accessToken: "token-admin", user: ADMIN });
    vi.spyOn(usersApi, "searchUsers").mockResolvedValue([MEMBER]);
    const createMemberSpy = vi.spyOn(usersApi, "createMember").mockResolvedValue({
      ...MEMBER,
      id: 8,
      employeeName: "Priya Nair",
      employeeMailId: "priya@example.com",
      employeeId: "EMP-1077",
    });

    renderPeoplePage();

    expect(await screen.findByText("Sarah Iyer")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /add member/i }));
    await user.type(screen.getByLabelText(/employee name/i), "Priya Nair");
    await user.type(screen.getByLabelText(/employee mail id/i), "priya@example.com");
    await user.type(screen.getByLabelText(/employee id/i), "EMP-1077");
    await user.type(screen.getByLabelText(/^password$/i), "TempPass123!");
    await user.click(screen.getByRole("button", { name: /save member/i }));

    await waitFor(() =>
      expect(createMemberSpy).toHaveBeenCalledWith({
        employeeName: "Priya Nair",
        employeeMailId: "priya@example.com",
        employeeId: "EMP-1077",
        password: "TempPass123!",
        role: "TEAM_MEMBER",
      }),
    );
  });

  it("changes a member's Role, resets their Password, and deactivates them", async () => {
    const user = userEvent.setup();
    vi.spyOn(authApi, "login").mockResolvedValue({ accessToken: "token-admin", user: ADMIN });
    vi.spyOn(usersApi, "searchUsers").mockResolvedValue([MEMBER]);
    const updateRoleSpy = vi.spyOn(usersApi, "updateRole").mockResolvedValue({
      ...MEMBER,
      role: "ADMIN",
    });
    const resetPasswordSpy = vi.spyOn(usersApi, "resetPassword").mockResolvedValue(MEMBER);
    const setActiveSpy = vi.spyOn(usersApi, "setActive").mockResolvedValue({
      ...MEMBER,
      isActive: false,
    });

    renderPeoplePage();
    await screen.findByText("Sarah Iyer");

    await user.selectOptions(screen.getByLabelText(/role/i), "ADMIN");
    await waitFor(() => expect(updateRoleSpy).toHaveBeenCalledWith(MEMBER.id, "ADMIN"));

    await user.click(screen.getByRole("button", { name: /reset password/i }));
    await user.type(screen.getByLabelText(/new password for sarah iyer/i), "NewTempPass456!");
    const resetPasswordButtons = screen.getAllByRole("button", { name: /^reset password$/i });
    await user.click(resetPasswordButtons[resetPasswordButtons.length - 1]);
    await waitFor(() =>
      expect(resetPasswordSpy).toHaveBeenCalledWith(MEMBER.id, "NewTempPass456!"),
    );

    await user.click(screen.getByRole("button", { name: /deactivate/i }));
    await waitFor(() => expect(setActiveSpy).toHaveBeenCalledWith(MEMBER.id, false));
  });
});
