import type { ReactNode } from "react";
import { Navigate, createBrowserRouter } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { PlaceholderPage } from "../components/layout/PlaceholderPage";
import { ResponsiveShell } from "../components/layout/ResponsiveShell";
import { CalendarPage } from "../pages/CalendarPage";
import { CreateMeetingPage } from "../pages/CreateMeetingPage";
import { EditMeetingPage } from "../pages/EditMeetingPage";
import { LoginPage } from "../pages/LoginPage";
import { MeetingDetailsPage } from "../pages/MeetingDetailsPage";
import { MyTasksPage } from "../pages/MyTasksPage";
import { PeoplePage } from "../pages/PeoplePage";
import { PreviousMeetingsPage } from "../pages/PreviousMeetingsPage";

function RequireAuth({ title, children }: { title: string; children: ReactNode }) {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return <ResponsiveShell title={title}>{children}</ResponsiveShell>;
}

function RequireAdmin({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  if (user?.role !== "ADMIN") {
    return <Navigate to="/calendar" replace />;
  }
  return <>{children}</>;
}

function RedirectIfAuthenticated({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth();
  if (isAuthenticated) {
    return <Navigate to="/calendar" replace />;
  }
  return <>{children}</>;
}

export const router = createBrowserRouter([
  {
    path: "/login",
    element: (
      <RedirectIfAuthenticated>
        <LoginPage />
      </RedirectIfAuthenticated>
    ),
  },
  {
    path: "/",
    element: <Navigate to="/calendar" replace />,
  },
  {
    path: "/calendar",
    element: (
      <RequireAuth title="Calendar">
        <CalendarPage />
      </RequireAuth>
    ),
  },
  {
    path: "/meetings/new",
    element: (
      <RequireAuth title="Create Meeting">
        <RequireAdmin>
          <CreateMeetingPage />
        </RequireAdmin>
      </RequireAuth>
    ),
  },
  {
    path: "/meetings/:meetingId",
    element: (
      <RequireAuth title="Meeting Details">
        <MeetingDetailsPage />
      </RequireAuth>
    ),
  },
  {
    path: "/meetings/:meetingId/edit",
    element: (
      <RequireAuth title="Edit Meeting">
        <RequireAdmin>
          <EditMeetingPage />
        </RequireAdmin>
      </RequireAuth>
    ),
  },
  {
    path: "/my-tasks",
    element: (
      <RequireAuth title="My Tasks">
        <MyTasksPage />
      </RequireAuth>
    ),
  },
  {
    path: "/previous-meetings",
    element: (
      <RequireAuth title="Previous Meetings">
        <PreviousMeetingsPage />
      </RequireAuth>
    ),
  },
  {
    path: "/people",
    element: (
      <RequireAuth title="People">
        <RequireAdmin>
          <PeoplePage />
        </RequireAdmin>
      </RequireAuth>
    ),
  },
  {
    path: "/activity-log",
    element: (
      <RequireAuth title="Activity Log">
        <RequireAdmin>
          <PlaceholderPage title="Activity Log" />
        </RequireAdmin>
      </RequireAuth>
    ),
  },
  {
    path: "*",
    element: <Navigate to="/" replace />,
  },
]);
