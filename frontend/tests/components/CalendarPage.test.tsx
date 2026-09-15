import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AuthProvider, useAuth } from "../../src/context/AuthContext";
import { CalendarPage } from "../../src/pages/CalendarPage";
import * as authApi from "../../src/services/authApi";
import * as meetingsApi from "../../src/services/meetingsApi";
import { useEffect } from "react";

function SignInThenRender() {
  const { login } = useAuth();
  useEffect(() => {
    login("user@example.com", "Password123!", true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return <CalendarPage />;
}

describe("CalendarPage", () => {
  beforeEach(() => {
    sessionStorage.clear();
    vi.restoreAllMocks();
  });

  it("renders a month grid with the current month's day-of-week headers", async () => {
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
    vi.spyOn(meetingsApi, "listMeetings").mockResolvedValue([]);

    render(
      <MemoryRouter>
        <AuthProvider>
          <SignInThenRender />
        </AuthProvider>
      </MemoryRouter>,
    );

    await waitFor(() => expect(screen.getByText("Sun")).toBeInTheDocument());
    expect(screen.getByText("Mon")).toBeInTheDocument();
  });

  it("renders meeting pills for meetings returned from the API", async () => {
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
    const today = new Date();
    const isoDate = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-15`;
    vi.spyOn(meetingsApi, "listMeetings").mockResolvedValue([
      {
        id: 1,
        title: "Q3 Roadmap Review",
        date: isoDate,
        time: "10:00",
        ownerId: 3,
        ownerName: "John",
        taskCount: 0,
      },
    ]);

    render(
      <MemoryRouter>
        <AuthProvider>
          <SignInThenRender />
        </AuthProvider>
      </MemoryRouter>,
    );

    expect(await screen.findByText("Q3 Roadmap Review")).toBeInTheDocument();
  });
});
