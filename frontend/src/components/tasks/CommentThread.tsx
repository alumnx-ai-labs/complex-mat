import { useState } from "react";

import type { Comment } from "../../services/commentsApi";
import { MentionAdoInput } from "./MentionAdoInput";

export function CommentThread({
  meetingId,
  comments,
  canComment,
  onPost,
  isLoading,
}: {
  meetingId: number;
  comments: Comment[];
  canComment: boolean;
  onPost: (message: string) => Promise<void>;
  isLoading?: boolean;
}) {
  const [message, setMessage] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handlePost() {
    if (!message.trim()) return;
    setIsSaving(true);
    setError(null);
    try {
      await onPost(message.trim());
      setMessage("");
    } catch {
      setError("Unable to post comment.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="field-row">
      <span className="field-label">Comments</span>
      {isLoading ? (
        <p className="muted">Loading comments…</p>
      ) : comments.length === 0 ? (
        <p className="muted">No comments yet.</p>
      ) : (
        <ul className="comment-list">
          {comments.map((comment) => (
            <li key={comment.id} className="comment-item">
              <div className="comment-meta">
                <strong>{comment.authorName}</strong>{" "}
                <span className="muted">{new Date(comment.createdAt).toLocaleString()}</span>
              </div>
              <div className="comment-message">{comment.message}</div>
              {comment.adoReferences.length > 0 && (
                <div style={{ marginTop: "6px" }}>
                  {comment.adoReferences.map((reference) => (
                    <span className="chip" key={reference.adoWorkItemId}>
                      ADO #{reference.adoWorkItemId} — {reference.title ?? "Unavailable"}
                      {!reference.isAvailable && <span className="muted">(unavailable)</span>}
                    </span>
                  ))}
                </div>
              )}
            </li>
          ))}
        </ul>
      )}

      {canComment && (
        <div style={{ marginTop: "10px" }}>
          {error && (
            <p role="alert" className="login-error">
              {error}
            </p>
          )}
          <MentionAdoInput
            as="textarea"
            meetingId={meetingId}
            value={message}
            onChange={setMessage}
            rows={2}
            className="textarea-input"
            placeholder="Type @ to mention an attendee or @<number> to link an Azure DevOps item…"
          />
          <button
            type="button"
            className="btn btn-secondary"
            style={{ marginTop: "8px" }}
            onClick={handlePost}
            disabled={isSaving || !message.trim()}
          >
            Post Comment
          </button>
        </div>
      )}
    </div>
  );
}
