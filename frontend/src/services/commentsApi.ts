import { apiRequest } from "./apiClient";

export interface CommentMention {
  userId: number;
  employeeName: string;
}

export interface CommentAdoReference {
  adoWorkItemId: number;
  title: string | null;
  type: string | null;
  isAvailable: boolean;
}

export interface Comment {
  id: number;
  taskId: number;
  authorId: number;
  authorName: string;
  message: string;
  mentions: CommentMention[];
  adoReferences: CommentAdoReference[];
  createdAt: string;
}

export interface MentionCandidate {
  id: number;
  employeeName: string;
}

export function listComments(taskId: number): Promise<Comment[]> {
  return apiRequest<Comment[]>(`/api/tasks/${taskId}/comments`);
}

export function postComment(taskId: number, message: string): Promise<Comment> {
  return apiRequest<Comment>(`/api/tasks/${taskId}/comments`, {
    method: "POST",
    body: { message },
  });
}

export function searchMentionCandidates(
  meetingId: number,
  q: string,
): Promise<MentionCandidate[]> {
  const params = new URLSearchParams();
  if (q) params.set("q", q);
  return apiRequest<MentionCandidate[]>(
    `/api/meetings/${meetingId}/attendees/mention-search?${params.toString()}`,
  );
}
