import { useActivityLog } from "../hooks/useActivityLog";
import type { ActivityLogEntry } from "../services/activityLogApi";

function describeAction(entry: ActivityLogEntry): string {
  const label = entry.action
    .toLowerCase()
    .split("_")
    .map((word) => word[0].toUpperCase() + word.slice(1))
    .join(" ");
  return `${label} (${entry.entityType} #${entry.entityId})`;
}

function formatTimestamp(timestamp: string): string {
  return new Date(timestamp).toLocaleString();
}

export function ActivityLogPage() {
  const { entries, isLoading, error } = useActivityLog();

  return (
    <div className="card">
      <h3>Activity Log</h3>
      {isLoading ? (
        <p className="muted">Loading activity…</p>
      ) : error ? (
        <p className="muted">{error}</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Actor</th>
              <th>Action</th>
              <th>Timestamp</th>
            </tr>
          </thead>
          <tbody>
            {entries.length === 0 ? (
              <tr>
                <td colSpan={3} className="muted">
                  No activity recorded yet.
                </td>
              </tr>
            ) : (
              entries.map((entry) => (
                <tr key={entry.id}>
                  <td>{entry.actorName}</td>
                  <td>{describeAction(entry)}</td>
                  <td>{formatTimestamp(entry.timestamp)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      )}
    </div>
  );
}
