import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AuthProvider } from "../../src/context/AuthContext";
import { LoginPage } from "../../src/pages/LoginPage";
import * as authApi from "../../src/services/authApi";

describe("LoginPage", () => {
  beforeEach(() => {
    sessionStorage.clear();
    vi.restoreAllMocks();
  });

  function renderLoginPage() {
    render(
      <MemoryRouter>
        <AuthProvider>
          <LoginPage />
        </AuthProvider>
      </MemoryRouter>,
    );
  }

  it("renders both the Team Member and Admin sign-in options plus a single Sign In action", () => {
    renderLoginPage();

    expect(screen.getByRole("radio", { name: /team member/i })).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: /admin/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /sign in/i })).toBeInTheDocument();
  });

  it("keeps Sign In disabled until the Terms and Conditions checkbox is checked, on either sign-in option", async () => {
    const user = userEvent.setup();
    renderLoginPage();

    const signInButton = screen.getByRole("button", { name: /sign in/i });
    const termsCheckbox = screen.getByRole("checkbox", { name: /terms and conditions/i });

    expect(termsCheckbox).not.toBeChecked();
    expect(signInButton).toBeDisabled();

    await user.click(screen.getByRole("radio", { name: /team member/i }));
    expect(signInButton).toBeDisabled();

    await user.click(termsCheckbox);
    expect(signInButton).toBeEnabled();

    await user.click(termsCheckbox);
    expect(signInButton).toBeDisabled();
  });

  it("logs in with the same credentials regardless of which option was clicked", async () => {
    const user = userEvent.setup();
    vi.spyOn(authApi, "login").mockResolvedValue({
      accessToken: "token-123",
      user: {
        id: 1,
        employeeName: "Sarah Iyer",
        employeeMailId: "sarah@example.com",
        employeeId: "E1042",
        role: "TEAM_MEMBER",
        isActive: true,
        termsAccepted: true,
      },
    });

    renderLoginPage();

    await user.click(screen.getByRole("radio", { name: /team member/i }));
    await user.type(screen.getByLabelText(/employee mail id/i), "sarah@example.com");
    await user.type(screen.getByLabelText(/password/i), "Password123!");
    await user.click(screen.getByRole("checkbox", { name: /terms and conditions/i }));
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() =>
      expect(authApi.login).toHaveBeenCalledWith("sarah@example.com", "Password123!", true),
    );
  });

  it("shows an error message when credentials are invalid", async () => {
    const user = userEvent.setup();
    const { ApiError } = await import("../../src/services/apiClient");
    vi.spyOn(authApi, "login").mockRejectedValue(new ApiError(401, "Invalid credentials"));

    renderLoginPage();

    await user.type(screen.getByLabelText(/employee mail id/i), "sarah@example.com");
    await user.type(screen.getByLabelText(/password/i), "wrong-password");
    await user.click(screen.getByRole("checkbox", { name: /terms and conditions/i }));
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      /incorrect employee mail id or password/i,
    );
  });
});
