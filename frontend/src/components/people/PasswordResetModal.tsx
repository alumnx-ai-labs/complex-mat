import { useState } from "react";

import * as usersApi from "../../services/usersApi";

export function PasswordResetModal({
  userId,
  employeeName,
  onClose,
  onReset,
}: {
  userId: number;
  employeeName: string;
  onClose: () => void;
  onReset: () => void;
}) {
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  async function handleSave() {
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    setError(null);
    setIsSaving(true);
    try {
      await usersApi.resetPassword(userId, password);
      onReset();
      onClose();
    } catch {
      setError("Unable to reset this member's Password.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(event) => event.stopPropagation()}>
        <div className="modal-head">
          <h3>Reset Password</h3>
          <button className="modal-close" aria-label="Close" onClick={onClose}>
            ✕
          </button>
        </div>
        <div className="modal-body">
          <div className="field-row">
            <label className="field-label" htmlFor="rp-password">
              New Password for {employeeName}
            </label>
            <input
              id="rp-password"
              className="text-input"
              type="password"
              placeholder="Set a new password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
            <div className="hint">
              Share the new Password with {employeeName} directly — MAT does not email
              credentials.
            </div>
          </div>
          {error && (
            <p role="alert" className="login-error">
              {error}
            </p>
          )}
        </div>
        <div className="modal-foot">
          <button className="btn btn-secondary" onClick={onClose} disabled={isSaving}>
            Cancel
          </button>
          <button className="btn btn-primary" onClick={handleSave} disabled={isSaving}>
            Reset Password
          </button>
        </div>
      </div>
    </div>
  );
}
