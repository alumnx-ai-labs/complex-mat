import { useCallback, useEffect, useState } from "react";

import { AddMemberModal } from "../components/people/AddMemberModal";
import { PasswordResetModal } from "../components/people/PasswordResetModal";
import { RoleSelect } from "../components/people/RoleSelect";
import * as usersApi from "../services/usersApi";
import type { UserSummary } from "../services/usersApi";

export function PeoplePage() {
  const [members, setMembers] = useState<UserSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddMember, setShowAddMember] = useState(false);
  const [resettingPasswordFor, setResettingPasswordFor] = useState<UserSummary | null>(null);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      setMembers(await usersApi.searchUsers("", false));
    } catch {
      setError("Unable to load members.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function handleRoleChange(member: UserSummary, role: UserSummary["role"]) {
    await usersApi.updateRole(member.id, role);
    await refresh();
  }

  async function handleToggleActive(member: UserSummary) {
    await usersApi.setActive(member.id, !member.isActive);
    await refresh();
  }

  if (isLoading) return <p className="muted">Loading members…</p>;

  return (
    <div className="card">
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <h3 style={{ margin: 0 }}>People</h3>
        <button className="btn btn-primary" onClick={() => setShowAddMember(true)}>
          + Add Member
        </button>
      </div>
      <p className="muted" style={{ fontSize: "12.5px" }}>
        There is no self-registration. An Admin adds every member here and shares their Employee
        Mail ID and Password with them directly. An Admin can also change a member's Role or
        reset their Password at any time.
      </p>
      {error && <p className="muted">{error}</p>}

      <div style={{ overflowX: "auto" }}>
        <table>
          <thead>
            <tr>
              <th>Employee Name</th>
              <th>Employee Mail ID</th>
              <th>Employee ID</th>
              <th>Role</th>
              <th>Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {members.map((member) => (
              <tr key={member.id}>
                <td>{member.employeeName}</td>
                <td>{member.employeeMailId}</td>
                <td>{member.employeeId}</td>
                <td>
                  <RoleSelect
                    value={member.role}
                    onChange={(role) => handleRoleChange(member, role)}
                  />
                </td>
                <td>
                  <span className={"pill " + (member.isActive ? "pill-active" : "pill-inactive")}>
                    {member.isActive ? "Active" : "Inactive"}
                  </span>
                </td>
                <td>
                  <button
                    className="btn btn-secondary"
                    style={{ marginRight: "6px" }}
                    onClick={() => setResettingPasswordFor(member)}
                  >
                    Reset Password
                  </button>
                  <button
                    className="btn btn-secondary"
                    onClick={() => handleToggleActive(member)}
                  >
                    {member.isActive ? "Deactivate" : "Reactivate"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showAddMember && (
        <AddMemberModal onClose={() => setShowAddMember(false)} onCreated={refresh} />
      )}
      {resettingPasswordFor && (
        <PasswordResetModal
          userId={resettingPasswordFor.id}
          employeeName={resettingPasswordFor.employeeName}
          onClose={() => setResettingPasswordFor(null)}
          onReset={refresh}
        />
      )}
    </div>
  );
}
