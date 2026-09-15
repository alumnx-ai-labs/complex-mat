import { useState } from "react";

import { TaskBoard } from "../components/tasks/TaskBoard";
import { MyTaskEditModal } from "../components/tasks/MyTaskEditModal";
import { useMyTasks } from "../hooks/useTasks";
import type { TaskWithMeeting } from "../services/tasksApi";

export function MyTasksPage() {
  const { tasks, isLoading, error, updateStatus, updateDescription } = useMyTasks();
  const [editingTask, setEditingTask] = useState<TaskWithMeeting | null>(null);

  return (
    <div className="card">
      <h3>My Tasks</h3>
      <div className="hint" style={{ marginTop: 0, marginBottom: "14px" }}>
        Every Task assigned to you, across all your Meetings. Drag a card to update its Status, or
        open a Task to edit its Description/Notes.
      </div>

      {isLoading ? (
        <p className="muted">Loading your tasks…</p>
      ) : error ? (
        <p className="muted">{error}</p>
      ) : tasks.length === 0 ? (
        <p className="muted">No tasks are assigned to you yet.</p>
      ) : (
        <TaskBoard
          tasks={tasks}
          onStatusChange={(taskId, status) => updateStatus(taskId, status)}
          onEdit={(task) => setEditingTask(task)}
        />
      )}

      {editingTask && (
        <MyTaskEditModal
          task={editingTask}
          onSave={(descriptionNotes) => updateDescription(editingTask.id, descriptionNotes)}
          onClose={() => setEditingTask(null)}
        />
      )}
    </div>
  );
}
