import { useNavigate } from "react-router-dom";

import { useMeetings } from "../hooks/useMeetings";

export function PreviousMeetingsPage() {
  const navigate = useNavigate();
  const { meetings, isLoading, error } = useMeetings();
  const sorted = [...meetings].sort((a, b) => a.date.localeCompare(b.date));

  return (
    <div className="card">
      <h3>Previous Meetings</h3>
      {isLoading ? (
        <p className="muted">Loading meetings…</p>
      ) : error ? (
        <p className="muted">{error}</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Title</th>
              <th>Date</th>
              <th>Meeting Owner</th>
              <th>Tasks</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {sorted.length === 0 ? (
              <tr>
                <td colSpan={5} className="muted">
                  No meetings available to you yet.
                </td>
              </tr>
            ) : (
              sorted.map((meeting) => (
                <tr key={meeting.id}>
                  <td>{meeting.title}</td>
                  <td>{meeting.date}</td>
                  <td>
                    <span className="pill pill-owner">{meeting.ownerName}</span>
                  </td>
                  <td>{meeting.taskCount} tasks</td>
                  <td>
                    <button
                      className="btn btn-secondary"
                      onClick={() => navigate(`/meetings/${meeting.id}`)}
                    >
                      Open Meeting Details
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      )}
      <div className="hint">
        Team Members only see meetings they are invited to as Attendees; Admins see all meetings.
      </div>
    </div>
  );
}
