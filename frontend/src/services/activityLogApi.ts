import { apiRequest } from "./apiClient";

export interface ActivityLogEntry {
  id: number;
  actorId: number;
  actorName: string;
  action: string;
  entityType: string;
  entityId: number;
  timestamp: string;
}

export function getActivityLog(): Promise<ActivityLogEntry[]> {
  return apiRequest<ActivityLogEntry[]>("/api/activity-log");
}
