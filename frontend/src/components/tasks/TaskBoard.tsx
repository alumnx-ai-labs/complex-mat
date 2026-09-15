import {
  DndContext,
  PointerSensor,
  type DragEndEvent,
  useSensor,
  useSensors,
} from "@dnd-kit/core";

import type { Task, TaskStatus, TaskWithMeeting } from "../../services/tasksApi";
import { TaskColumn } from "./TaskColumn";

const COLUMNS: { status: TaskStatus; label: string }[] = [
  { status: "TODO", label: "To Do" },
  { status: "IN_PROGRESS", label: "In Progress" },
  { status: "COMPLETED", label: "Completed" },
];

export function resolveStatusChangeFromDragEnd(
  tasks: TaskWithMeeting[],
  event: Pick<DragEndEvent, "active" | "over">,
): { taskId: number; status: TaskStatus } | null {
  const { active, over } = event;
  if (!over) return null;
  const taskId = Number(active.id);
  const nextStatus = over.id as TaskStatus;
  const task = tasks.find((candidate) => candidate.id === taskId);
  if (!task || task.status === nextStatus) return null;
  return { taskId, status: nextStatus };
}

export function TaskBoard({
  tasks,
  currentUserId,
  onStatusChange,
  onEdit,
  onOpenTask,
}: {
  tasks: TaskWithMeeting[] | Task[];
  currentUserId?: number;
  onStatusChange?: (taskId: number, status: TaskStatus) => void;
  onEdit?: (task: TaskWithMeeting) => void;
  onOpenTask?: (task: Task) => void;
}) {
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } }),
  );

  function handleDragEnd(event: DragEndEvent) {
    const change = resolveStatusChangeFromDragEnd(tasks, event);
    if (change && onStatusChange) {
      onStatusChange(change.taskId, change.status);
    }
  }

  return (
    <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
      <div className="board">
        {COLUMNS.map((column) => (
          <TaskColumn
            key={column.status}
            status={column.status}
            label={column.label}
            tasks={tasks.filter((task) => task.status === column.status)}
            currentUserId={currentUserId}
            onStatusChange={onStatusChange}
            onEdit={onEdit}
            onOpenTask={onOpenTask}
          />
        ))}
      </div>
    </DndContext>
  );
}
