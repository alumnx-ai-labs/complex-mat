import type { AdoReference } from "../../services/azureDevOpsApi";

export function AdoReferenceList({ references }: { references: AdoReference[] }) {
  if (references.length === 0) return null;

  return (
    <div className="field-row">
      <span className="field-label">Linked Azure DevOps Items</span>
      <div>
        {references.map((reference) => (
          <span className="chip" key={reference.adoWorkItemId}>
            ADO #{reference.adoWorkItemId} — {reference.title ?? "Unavailable"}
            {reference.isAvailable && reference.openUrl ? (
              <a href={reference.openUrl} target="_blank" rel="noreferrer">
                Open in Azure DevOps
              </a>
            ) : (
              <span className="muted">(unavailable)</span>
            )}
          </span>
        ))}
      </div>
    </div>
  );
}
