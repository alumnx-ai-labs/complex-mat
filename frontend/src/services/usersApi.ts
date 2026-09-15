import { apiRequest } from "./apiClient";
import type { Role } from "./authApi";

export interface UserSummary {
  id: number;
  employeeName: string;
  employeeMailId: string;
  employeeId: string;
  role: Role;
  isActive: boolean;
}

export interface CreateMemberInput {
  employeeName: string;
  employeeMailId: string;
  employeeId: string;
  password: string;
  role: Role;
}

export function searchUsers(q: string, activeOnly = true): Promise<UserSummary[]> {
  const params = new URLSearchParams();
  if (q) params.set("q", q);
  params.set("activeOnly", String(activeOnly));
  return apiRequest<UserSummary[]>(`/api/users?${params.toString()}`);
}

export function createMember(input: CreateMemberInput): Promise<UserSummary> {
  return apiRequest<UserSummary>("/api/users", { method: "POST", body: input });
}

export function updateRole(userId: number, role: Role): Promise<UserSummary> {
  return apiRequest<UserSummary>(`/api/users/${userId}/role`, {
    method: "PATCH",
    body: { role },
  });
}

export function resetPassword(userId: number, password: string): Promise<UserSummary> {
  return apiRequest<UserSummary>(`/api/users/${userId}/password`, {
    method: "PATCH",
    body: { password },
  });
}

export function setActive(userId: number, isActive: boolean): Promise<UserSummary> {
  return apiRequest<UserSummary>(`/api/users/${userId}/active`, {
    method: "PATCH",
    body: { isActive },
  });
}
