import { apiRequest } from "./apiClient";

export interface AdoSuggestion {
  adoWorkItemId: number;
  title: string;
  type: string;
}

export interface AdoReference {
  adoWorkItemId: number;
  title: string | null;
  type: string | null;
  isAvailable: boolean;
  openUrl: string | null;
}

export function getAdoSuggestions(q: string): Promise<AdoSuggestion[]> {
  const params = new URLSearchParams({ q });
  return apiRequest<AdoSuggestion[]>(`/api/azure-devops/suggestions?${params.toString()}`);
}

export function getTaskAdoReferences(taskId: number): Promise<AdoReference[]> {
  return apiRequest<AdoReference[]>(`/api/tasks/${taskId}/ado-references`);
}
