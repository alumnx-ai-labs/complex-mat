import { useDraggable } from "@dnd-kit/core";

import type { TaskStatus, TaskWithMeeting } from "../../services/tasksApi";

const STATUS_OPTIONS: { value: TaskStatus; label: string }[] = [
  { value: "TODO", label: "To Do" },
  { value: "IN_PROGRESS", label: "In Progress" },
  { value: "COMPLETED", label: "Completed" },
];

function initials(name: string): string {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");
}

export function TaskCard({
  task,
  onStatusChange,
  onEdit,
  onOpen,
}: {
  task: TaskWithMeeting;
  onStatusChange: (status: TaskStatus) => void;
  onEdit: () => void;
  onOpen?: () => void;
}) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: task.id,
  });

  const style = transform
    ? { transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`, zIndex: 10 }
    : undefined;

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="task-card"
      data-dragging={isDragging || undefined}
      onClick={onOpen}
    >
      <div {...listeners} {...attributes} className="task-card-drag" onMouseDown={onOpen}>
        {task.meetingTitle && <div className="t-meeting">{task.meetingTitle}</div>}
        <div className="t-title">{task.title}</div>
        <div className="t-meta">
          <span>Due {task.dueDate ?? "—"}</span>
          {task.assigneeName && (
            <span className="avatar" title={task.assigneeName}>
              {initials(task.assigneeName)}
            </span>
          )}
        </div>
      </div>

      {task.needsReassignment && (
        <div className="flag">⚠ Assignee needs reassignment (inactive or no longer an attendee)</div>
      )}

      <div className="field-row">
        <label className="field-label" htmlFor={`task-status-${task.id}`}>
          Status
        </label>
        <select
          id={`task-status-${task.id}`}
          className="select-input"
          value={task.status}
          onChange={(event) => onStatusChange(event.target.value as TaskStatus)}
        >
          {STATUS_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      <button type="button" className="btn btn-secondary task-card-edit" onClick={onEdit}>
        Edit Description/Notes
      </button>
    </div>
  );
}
