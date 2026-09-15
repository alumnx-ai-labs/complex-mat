import { useState, type FormEvent } from "react";

import { useComments } from "../../hooks/useComments";
import { useTaskAdoReferences } from "../../hooks/useAdoReferences";
import type { TaskWithMeeting } from "../../services/tasksApi";
import { AdoReferenceList } from "./AdoReferenceList";
import { CommentThread } from "./CommentThread";
import { MentionAdoInput } from "./MentionAdoInput";

export function MyTaskEditModal({
  task,
  onSave,
  onClose,
}: {
  task: TaskWithMeeting;
  onSave: (descriptionNotes: string) => Promise<void>;
  onClose: () => void;
}) {
  const [descriptionNotes, setDescriptionNotes] = useState(task.descriptionNotes ?? "");
  const [isSaving, setIsSaving] = useState(false);
  const { comments, isLoading: commentsLoading, postComment } = useComments(task.id);
  const { references } = useTaskAdoReferences(task.id);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setIsSaving(true);
    try {
      await onSave(descriptionNotes);
      onClose();
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label="Edit task">
      <div className="modal-panel card">
        <h3>{task.title}</h3>
        <div className="muted">{task.meetingTitle}</div>
        <div className="field-row" style={{ marginTop: "12px" }}>
          <span className="field-label">Due Date</span>
          <div className="muted">{task.dueDate ?? "No due date"}</div>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="field-row">
            <label className="field-label" htmlFor="my-task-description-notes">Description / Notes</label>
            <MentionAdoInput
              as="textarea"
              id="my-task-description-notes"
              className="textarea-input"
              meetingId={task.meetingId}
              value={descriptionNotes}
              onChange={setDescriptionNotes}
            />
            <div className="hint">Only Description/Notes can be edited here.</div>
          </div>
          <div className="modal-foot">
            <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={isSaving}>Save</button>
          </div>
        </form>

        <AdoReferenceList references={references} />
        <CommentThread
          meetingId={task.meetingId}
          comments={comments}
          canComment
          isLoading={commentsLoading}
          onPost={postComment}
        />
      </div>
    </div>
  );
}
