import { useState } from "react";
import { useParams } from "react-router-dom";

import { TaskBoard } from "../components/tasks/TaskBoard";
import { TaskEditModal } from "../components/tasks/TaskEditModal";
import { useAuth } from "../context/AuthContext";
import { useMeetingDetail } from "../hooks/useMeetings";
import { useTasks } from "../hooks/useTasks";
import type { Task } from "../services/tasksApi";

export function MeetingDetailsPage() {
  const { meetingId } = useParams<{ meetingId: string }>();
  const { user } = useAuth();
  const { meeting, isLoading, error, refresh } = useMeetingDetail(
    meetingId ? Number(meetingId) : null,
  );
  const { createTask, updateTask, deleteTask } = useTasks(Number(meetingId), refresh);
  const [editingTask, setEditingTask] = useState<Task | null | undefined>(undefined);

  if (isLoading) return <p className="muted">Loading meeting…</p>;
  if (error || !meeting || !user) return <p className="muted">{error ?? "Meeting not found."}</p>;

  const isOwner = user.id === meeting.ownerId;

  return (
    <div>
      <div className="card">
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
          <div>
            <h3 style={{ marginBottom: "6px" }}>{meeting.title}</h3>
            <div className="muted">
              {meeting.date} · {meeting.time}
            </div>
          </div>
          <span className="pill pill-owner">Meeting Owner: {meeting.ownerName}</span>
        </div>

        <div className="field-row" style={{ marginTop: "16px" }}>
          <span className="field-label">Attendees</span>
          <div>
            {meeting.attendees.map((attendee) => (
              <span className="chip" key={attendee.id}>
                {attendee.employeeName}
                {attendee.id === meeting.ownerId ? " (Owner)" : ""}
              </span>
            ))}
          </div>
        </div>

        <div className="field-row">
          <span className="field-label">Agenda / Notes</span>
          <div className="muted">{meeting.agendaNotes || "No agenda provided."}</div>
        </div>
      </div>

      <div className="card">
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            marginBottom: "10px",
          }}
        >
          <h3 style={{ margin: 0 }}>Task Board</h3>
          {isOwner && (
            <button className="btn btn-primary" onClick={() => setEditingTask(null)}>
              + Create Task
            </button>
          )}
        </div>
        <TaskBoard tasks={meeting.tasks} onOpenTask={(task) => setEditingTask(task)} />
      </div>

      {editingTask !== undefined && (
        <TaskEditModal
          meetingId={meeting.id}
          attendees={meeting.attendees}
          ownerId={meeting.ownerId}
          currentUserId={user.id}
          isAdmin={user.role === "ADMIN"}
          task={editingTask}
          onClose={() => setEditingTask(undefined)}
          onCreate={(input) => createTask(input)}
          onUpdate={(taskId, input) => updateTask(taskId, input)}
          onDelete={(taskId) => deleteTask(taskId)}
        />
      )}
    </div>
  );
}
