import type { Role } from "../../services/authApi";

export function RoleSelect({
  value,
  onChange,
  disabled,
}: {
  value: Role;
  onChange: (role: Role) => void;
  disabled?: boolean;
}) {
  return (
    <select
      className="select-input"
      aria-label="Role"
      style={{ padding: "5px 8px", fontSize: "12.5px" }}
      value={value}
      disabled={disabled}
      onChange={(event) => onChange(event.target.value as Role)}
    >
      <option value="TEAM_MEMBER">Team Member</option>
      <option value="ADMIN">Admin</option>
    </select>
  );
}
