import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { ApiError } from "../services/apiClient";

type SignInOption = "TEAM_MEMBER" | "ADMIN";

const ROLE_CARDS: { option: SignInOption; title: string; description: string }[] = [
  {
    option: "TEAM_MEMBER",
    title: "Team Member",
    description: "See your meetings, work your task board, comment on your tasks",
  },
  {
    option: "ADMIN",
    title: "Admin",
    description: "Schedule meetings, assign tasks, manage people, track everyone's progress",
  },
];

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [selectedOption, setSelectedOption] = useState<SignInOption>("ADMIN");
  const [employeeMailId, setEmployeeMailId] = useState("");
  const [password, setPassword] = useState("");
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await login(employeeMailId, password, termsAccepted);
      navigate("/", { replace: true });
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setError("Incorrect Employee Mail ID or Password.");
      } else {
        setError("Something went wrong. Please try again.");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="login-page">
      <form className="login-card" aria-label="Sign in" onSubmit={handleSubmit}>
        <div className="login-logo">M</div>
        <h1>Meeting Action Tracker</h1>
        <p>Sign in with the Employee Mail ID and Password an Admin gave you.</p>

        <div className="login-role-label">Continue as</div>
        <div className="login-role-cards" role="radiogroup" aria-label="Continue as">
          {ROLE_CARDS.map((card) => (
            <button
              type="button"
              key={card.option}
              role="radio"
              aria-checked={selectedOption === card.option}
              className={
                "login-role-card" + (selectedOption === card.option ? " selected" : "")
              }
              onClick={() => setSelectedOption(card.option)}
            >
              <div className="r-title">{card.title}</div>
              <div className="r-desc">{card.description}</div>
            </button>
          ))}
        </div>

        <div className="field-row">
          <label className="field-label" htmlFor="employeeMailId">
            Employee Mail ID
          </label>
          <input
            id="employeeMailId"
            className="text-input"
            type="email"
            placeholder="e.g. john@organisation.example"
            value={employeeMailId}
            onChange={(event) => setEmployeeMailId(event.target.value)}
            autoComplete="username"
            required
          />
        </div>

        <div className="field-row">
          <label className="field-label" htmlFor="password">
            Password
          </label>
          <input
            id="password"
            className="text-input"
            type="password"
            placeholder="Password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            autoComplete="current-password"
            required
          />
        </div>

        {error && (
          <p role="alert" className="login-error">
            {error}
          </p>
        )}

        <div className="field-row" style={{ display: "flex", alignItems: "flex-start", gap: "8px" }}>
          <input
            type="checkbox"
            id="termsAccepted"
            checked={termsAccepted}
            onChange={(event) => setTermsAccepted(event.target.checked)}
            style={{ marginTop: "3px" }}
          />
          <label htmlFor="termsAccepted" style={{ fontSize: "12px", cursor: "pointer" }}>
            I agree to the Terms and Conditions
          </label>
        </div>

        <button type="submit" className="login-btn" disabled={isSubmitting || !termsAccepted}>
          Sign In
        </button>

        <div className="login-note">
          Your account's actual Role always applies, whichever option is selected above.
        </div>
      </form>
    </div>
  );
}
