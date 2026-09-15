import { useState } from "react";

import { ApiError } from "../../services/apiClient";
import * as usersApi from "../../services/usersApi";
import type { Role } from "../../services/authApi";

export function AddMemberModal({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: () => void;
}) {
  const [employeeName, setEmployeeName] = useState("");
  const [employeeMailId, setEmployeeMailId] = useState("");
  const [employeeId, setEmployeeId] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<Role>("TEAM_MEMBER");
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  async function handleSave() {
    if (!employeeName.trim() || !employeeMailId.trim() || !employeeId.trim() || !password) {
      setError("Employee Name, Employee Mail ID, Employee ID, and Password are all required.");
      return;
    }
    setError(null);
    setIsSaving(true);
    try {
      await usersApi.createMember({
        employeeName: employeeName.trim(),
        employeeMailId: employeeMailId.trim(),
        employeeId: employeeId.trim(),
        password,
        role,
      });
      onCreated();
      onClose();
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setError("That Employee Mail ID or Employee ID is already registered to another member.");
      } else {
        setError("Unable to add this member.");
      }
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(event) => event.stopPropagation()}>
        <div className="modal-head">
          <h3>Add Member</h3>
          <button className="modal-close" aria-label="Close" onClick={onClose}>
            ✕
          </button>
        </div>
        <div className="modal-body">
          <div className="field-row">
            <label className="field-label" htmlFor="am-name">Employee Name</label>
            <input
              id="am-name"
              className="text-input"
              placeholder="e.g. Alex Rivera"
              value={employeeName}
              onChange={(event) => setEmployeeName(event.target.value)}
            />
          </div>
          <div style={{ display: "flex", gap: "12px" }}>
            <div className="field-row" style={{ flex: 1 }}>
              <label className="field-label" htmlFor="am-email">Employee Mail ID</label>
              <input
                id="am-email"
                className="text-input"
                placeholder="e.g. alex@organisation.example"
                value={employeeMailId}
                onChange={(event) => setEmployeeMailId(event.target.value)}
              />
            </div>
            <div className="field-row" style={{ flex: 1 }}>
              <label className="field-label" htmlFor="am-empid">Employee ID</label>
              <input
                id="am-empid"
                className="text-input"
                placeholder="e.g. EMP-1042"
                value={employeeId}
                onChange={(event) => setEmployeeId(event.target.value)}
              />
            </div>
          </div>
          <div className="field-row">
            <label className="field-label" htmlFor="am-password">Password</label>
            <input
              id="am-password"
              className="text-input"
              type="password"
              placeholder="Set an initial password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
            <div className="hint">
              Share this Employee Mail ID and Password with the member directly — MAT does not
              email credentials.
            </div>
          </div>
          <div className="field-row">
            <label className="field-label" htmlFor="am-role">Role</label>
            <select
              id="am-role"
              className="select-input"
              value={role}
              onChange={(event) => setRole(event.target.value as Role)}
            >
              <option value="TEAM_MEMBER">Team Member</option>
              <option value="ADMIN">Admin</option>
            </select>
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
            Save Member
          </button>
        </div>
      </div>
    </div>
  );
}
