import { useNavigate, useParams } from "react-router-dom";

import { MeetingForm, type MeetingFormValues } from "../components/meetings/MeetingForm";
import { useMeetingDetail } from "../hooks/useMeetings";
import type { UserSummary } from "../services/usersApi";

export function EditMeetingPage() {
  const { meetingId } = useParams<{ meetingId: string }>();
  const navigate = useNavigate();
  const { meeting, isLoading, error, updateMeeting } = useMeetingDetail(
    meetingId ? Number(meetingId) : null,
  );

  if (isLoading) return <p className="muted">Loading meeting…</p>;
  if (error || !meeting) return <p className="muted">{error ?? "Meeting not found."}</p>;

  const initialAttendees: UserSummary[] = meeting.attendees.map((attendee) => ({
    id: attendee.id,
    employeeName: attendee.employeeName,
    employeeMailId: "",
    employeeId: "",
    role: "TEAM_MEMBER",
    isActive: true,
  }));

  async function handleSubmit(values: MeetingFormValues) {
    await updateMeeting({
      title: values.title,
      date: values.date,
      time: values.time,
      agendaNotes: values.agendaNotes,
      attendeeIds: values.attendeeIds,
    });
    navigate(`/meetings/${meetingId}`, { replace: true });
  }

  return (
    <div className="card">
      <h3>Edit Meeting</h3>
      <MeetingForm
        initialTitle={meeting.title}
        initialDate={meeting.date}
        initialTime={meeting.time}
        initialAgendaNotes={meeting.agendaNotes ?? ""}
        initialAttendees={initialAttendees}
        ownerId={meeting.ownerId}
        dateEditable
        submitLabel="Save Changes"
        onSubmit={handleSubmit}
        onCancel={() => navigate(`/meetings/${meetingId}`)}
      />
    </div>
  );
}
