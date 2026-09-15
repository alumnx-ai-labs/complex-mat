import { apiRequest } from "./apiClient";

export type Role = "ADMIN" | "TEAM_MEMBER";

export interface AuthUser {
  id: number;
  employeeName: string;
  employeeMailId: string;
  employeeId: string;
  role: Role;
  isActive: boolean;
  termsAccepted: boolean;
}

export interface LoginResponse {
  accessToken: string;
  user: AuthUser;
}

export function login(
  employeeMailId: string,
  password: string,
  termsAccepted: boolean,
): Promise<LoginResponse> {
  return apiRequest<LoginResponse>("/api/auth/login", {
    method: "POST",
    body: { employeeMailId, password, termsAccepted },
  });
}

export function me(): Promise<AuthUser> {
  return apiRequest<AuthUser>("/api/auth/me");
}
