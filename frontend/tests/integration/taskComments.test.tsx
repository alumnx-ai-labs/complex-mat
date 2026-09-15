import { useEffect } from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AuthProvider, useAuth } from "../../src/context/AuthContext";
import { MeetingDetailsPage } from "../../src/pages/MeetingDetailsPage";
import * as authApi from "../../src/services/authApi";
import * as azureDevOpsApi from "../../src/services/azureDevOpsApi";
import * as commentsApi from "../../src/services/commentsApi";
import * as meetingsApi from "../../src/services/meetingsApi";
import type { MeetingDetail } from "../../src/services/meetingsApi";

const OWNER = {
  id: 3,
  employeeName: "John Owner",
  employeeMailId: "john@example.com",
  employeeId: "E0001",
  role: "ADMIN" as const,
  isActive: true,
};

const ASSIGNEE = { id: 7, employeeName: "Sarah Iyer" };

function meetingDetail(): MeetingDetail {
  return {
    id: 42,
    title: "Q3 Roadmap Review",
    date: "2026-09-15",
    time: "10:00",
    agendaNotes: "Discuss roadmap.",
    ownerId: OWNER.id,
    ownerName: OWNER.employeeName,
    attendees: [{ id: OWNER.id, employeeName: OWNER.employeeName }, ASSIGNEE],
    tasks: [
      {
        id: 501,
        meetingId: 42,
        title: "Prepare notes",
        descriptionNotes: "See @1234 for context",
        assigneeId: ASSIGNEE.id,
        assigneeName: ASSIGNEE.employeeName,
        dueDate: null,
        status: "TODO",
        needsReassignment: false,
      },
    ],
  };
}

function SignInAs({ user, children }: { user: typeof OWNER; children: React.ReactNode }) {
  const { login } = useAuth();
  useEffect(() => {
    login(user.employeeMailId, "Password123!");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return <>{children}</>;
}

function renderMeetingDetails() {
  return render(
    <MemoryRouter initialEntries={["/meetings/42"]}>
      <AuthProvider>
        <SignInAs user={OWNER}>
          <Routes>
            <Route path="/meetings/:meetingId" element={<MeetingDetailsPage />} />
          </Routes>
        </SignInAs>
      </AuthProvider>
    </MemoryRouter>,
  );
}

describe("Task comments, mentions, and Azure DevOps references", () => {
  beforeEach(() => {
    sessionStorage.clear();
    vi.restoreAllMocks();
  });

  it("shows the comment thread and linked Azure DevOps items, and lets the Owner post a comment", async () => {
    const user = userEvent.setup();
    vi.spyOn(authApi, "login").mockResolvedValue({ accessToken: "token-owner", user: OWNER });
    vi.spyOn(meetingsApi, "getMeetingDetail").mockResolvedValue(meetingDetail());
    vi.spyOn(azureDevOpsApi, "getTaskAdoReferences").mockResolvedValue([
      {
        adoWorkItemId: 1234,
        title: "Implement onboarding API",
        type: "Story",
        isAvailable: true,
        openUrl: "https://dev.azure.com/org/project/_workitems/edit/1234",
      },
    ]);
    vi.spyOn(commentsApi, "listComments").mockResolvedValue([
      {
        id: 1,
        taskId: 501,
        authorId: ASSIGNEE.id,
        authorName: ASSIGNEE.employeeName,
        message: "Can @John confirm this?",
        mentions: [{ userId: OWNER.id, employeeName: OWNER.employeeName }],
        adoReferences: [],
        createdAt: "2026-09-14T10:00:00Z",
      },
    ]);
    const postCommentSpy = vi.spyOn(commentsApi, "postComment").mockResolvedValue({
      id: 2,
      taskId: 501,
      authorId: OWNER.id,
      authorName: OWNER.employeeName,
      message: "Looks good",
      mentions: [],
      adoReferences: [],
      createdAt: "2026-09-14T10:05:00Z",
    });

    renderMeetingDetails();

    await user.click(await screen.findByText("Prepare notes"));

    expect(await screen.findByText(/implement onboarding api/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /open in azure devops/i })).toHaveAttribute(
      "href",
      "https://dev.azure.com/org/project/_workitems/edit/1234",
    );

    expect(await screen.findByText(/can @john confirm this\?/i)).toBeInTheDocument();

    const composer = screen.getByPlaceholderText(/type @ to mention/i);
    await user.type(composer, "Looks good");
    await user.click(screen.getByRole("button", { name: /post comment/i }));

    await waitFor(() => expect(postCommentSpy).toHaveBeenCalledWith(501, "Looks good"));
  });
});
