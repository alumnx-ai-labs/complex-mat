import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { TaskCard } from "../../src/components/tasks/TaskCard";
import type { TaskWithMeeting } from "../../src/services/tasksApi";

const task: TaskWithMeeting = {
  id: 101,
  meetingId: 12,
  meetingTitle: "Q3 Roadmap Review",
  title: "Prepare onboarding API design doc",
  descriptionNotes: null,
  dueDate: "2026-09-20",
  status: "TODO",
  needsReassignment: false,
};

describe("TaskCard", () => {
  it("does not open the task on mouse-down alone (that would fire before a drag can start)", () => {
    const onOpen = vi.fn();
    render(
      <TaskCard task={task} onStatusChange={vi.fn()} onEdit={vi.fn()} onOpen={onOpen} />,
    );

    fireEvent.mouseDown(screen.getByText(task.title));

    expect(onOpen).not.toHaveBeenCalled();
  });

  it("opens the task on a plain click", () => {
    const onOpen = vi.fn();
    render(
      <TaskCard task={task} onStatusChange={vi.fn()} onEdit={vi.fn()} onOpen={onOpen} />,
    );

    fireEvent.click(screen.getByText(task.title));

    expect(onOpen).toHaveBeenCalledTimes(1);
  });
});
