import { useEffect, useRef, useState, type ChangeEvent } from "react";

import { getAdoSuggestions } from "../../services/azureDevOpsApi";
import { searchMentionCandidates } from "../../services/commentsApi";

const DEBOUNCE_MS = 200;

type Suggestion =
  | { kind: "mention"; id: number; label: string }
  | { kind: "ado"; id: number; label: string; type: string };

/**
 * A text input/textarea that opens a "@" suggestion dropdown while typing —
 * letters search this Meeting's Attendees for a member mention, digits search
 * Azure DevOps Story/Feature suggestions, disambiguated by the first
 * character after "@" (FR-028, FR-029). Used for a Task's Title,
 * Description/Notes, and Comment composer alike (US5 Acceptance Scenario 2).
 */
export function MentionAdoInput({
  as = "textarea",
  meetingId,
  value,
  onChange,
  disabled,
  id,
  className,
  rows,
  placeholder,
}: {
  as?: "input" | "textarea";
  meetingId: number;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  id?: string;
  className?: string;
  rows?: number;
  placeholder?: string;
}) {
  const ref = useRef<HTMLInputElement | HTMLTextAreaElement | null>(null);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [triggerStart, setTriggerStart] = useState<number | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, []);

  function closeSuggestions() {
    setSuggestions([]);
    setTriggerStart(null);
  }

  function handleChange(event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) {
    const newValue = event.target.value;
    const caret = event.target.selectionStart ?? newValue.length;
    onChange(newValue);

    const upToCaret = newValue.slice(0, caret);
    const match = /@([A-Za-z0-9_]*)$/.exec(upToCaret);
    if (!match) {
      closeSuggestions();
      return;
    }
    const token = match[1];
    setTriggerStart(caret - token.length - 1);

    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (token.length === 0) {
      setSuggestions([]);
      return;
    }
    debounceRef.current = setTimeout(() => void loadSuggestions(token), DEBOUNCE_MS);
  }

  async function loadSuggestions(token: string) {
    if (/^\d+$/.test(token)) {
      const results = await getAdoSuggestions(token);
      setSuggestions(
        results.map((item) => ({
          kind: "ado" as const,
          id: item.adoWorkItemId,
          label: item.title,
          type: item.type,
        })),
      );
    } else {
      const results = await searchMentionCandidates(meetingId, token);
      setSuggestions(
        results.map((user) => ({ kind: "mention" as const, id: user.id, label: user.employeeName })),
      );
    }
  }

  function applySuggestion(suggestion: Suggestion) {
    if (triggerStart === null) return;
    const caret = ref.current?.selectionStart ?? value.length;
    const insertion =
      suggestion.kind === "mention" ? `@${suggestion.label.split(" ")[0]} ` : `@${suggestion.id} `;
    onChange(value.slice(0, triggerStart) + insertion + value.slice(caret));
    closeSuggestions();
    ref.current?.focus();
  }

  return (
    <div className="search-box">
      {as === "textarea" ? (
        <textarea
          id={id}
          ref={ref as React.Ref<HTMLTextAreaElement>}
          className={className}
          value={value}
          disabled={disabled}
          rows={rows}
          placeholder={placeholder}
          onChange={handleChange}
        />
      ) : (
        <input
          id={id}
          ref={ref as React.Ref<HTMLInputElement>}
          type="text"
          className={className}
          value={value}
          disabled={disabled}
          placeholder={placeholder}
          onChange={handleChange}
        />
      )}
      {suggestions.length > 0 && (
        <div className="search-results">
          {suggestions.map((suggestion) => (
            <div
              className="opt"
              key={`${suggestion.kind}-${suggestion.id}`}
              onClick={() => applySuggestion(suggestion)}
            >
              {suggestion.kind === "mention" ? (
                <>
                  <span className="avatar">{suggestion.label.slice(0, 1).toUpperCase()}</span>
                  {suggestion.label}
                </>
              ) : (
                <>
                  ADO #{suggestion.id} — {suggestion.label}
                  <span className="muted" style={{ marginLeft: "auto" }}>
                    {suggestion.type}
                  </span>
                </>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
