import { apiRequest } from "./apiClient";
import type { Task } from "./tasksApi";

export interface MeetingSummary {
  id: number;
  title: string;
  date: string;
  time: string;
  ownerId: number;
  ownerName: string;
  taskCount: number;
}

export interface MeetingAttendee {
  id: number;
  employeeName: string;
}

export interface MeetingDetail {
  id: number;
  title: string;
  date: string;
  time: string;
  agendaNotes: string | null;
  ownerId: number;
  ownerName: string;
  attendees: MeetingAttendee[];
  tasks: Task[];
}

export interface MeetingCreateInput {
  title: string;
  date: string;
  time: string;
  agendaNotes?: string;
  attendeeIds: number[];
}

export interface MeetingUpdateInput {
  title?: string;
  date?: string;
  time?: string;
  agendaNotes?: string;
  attendeeIds?: number[];
}

export function listMeetings(params?: { month?: number; year?: number }): Promise<MeetingSummary[]> {
  const query = new URLSearchParams();
  if (params?.month) query.set("month", String(params.month));
  if (params?.year) query.set("year", String(params.year));
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return apiRequest<MeetingSummary[]>(`/api/meetings${suffix}`);
}

export function getMeetingDetail(meetingId: number): Promise<MeetingDetail> {
  return apiRequest<MeetingDetail>(`/api/meetings/${meetingId}`);
}

export function createMeeting(input: MeetingCreateInput): Promise<MeetingSummary> {
  return apiRequest<MeetingSummary>("/api/meetings", { method: "POST", body: input });
}

export function updateMeeting(
  meetingId: number,
  input: MeetingUpdateInput,
): Promise<MeetingDetail> {
  return apiRequest<MeetingDetail>(`/api/meetings/${meetingId}`, { method: "PATCH", body: input });
}

export function deleteMeeting(meetingId: number): Promise<void> {
  return apiRequest<void>(`/api/meetings/${meetingId}`, { method: "DELETE" });
}
