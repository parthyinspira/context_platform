import { useState } from "react";
import { Stepper } from "./Stepper.jsx";
import { Skeleton } from "./Skeleton.jsx";
import { ErrorBanner } from "./ErrorBanner.jsx";
import { createSource, testConnection } from "../api.js";

// Hackathon-minimal defaults for fields the wizard doesn't collect yet
// (schedule/owner/sensitivity are required by POST /sources but out of
// scope for the type/connect steps per the KAN-61 plan).
const DEFAULT_SCHEDULE = "0 0 * * *";
const DEFAULT_OWNER = "unassigned";
const DEFAULT_SENSITIVITY = "internal";

const SOURCE_TYPES = [
  { id: "git", label: "Git repository", enabled: true },
  { id: "sql", label: "SQL database", enabled: false },
  { id: "upload", label: "Upload", enabled: false },
  { id: "sharepoint", label: "SharePoint", enabled: false },
  { id: "snowflake", label: "Snowflake", enabled: false },
  { id: "tableau", label: "Tableau", enabled: false },
];

const STEPS = [{ label: "Type" }, { label: "Connect" }];

export function AddSourceWizard({ onSourceCreated, onCancel }) {
  const [step, setStep] = useState(0);
  const [type, setType] = useState(null);
  const [uri, setUri] = useState("");
  const [credentialsInput, setCredentialsInput] = useState("");
  const [pendingCredentials, setPendingCredentials] = useState("");
  const [testState, setTestState] = useState("idle"); // idle | loading | success | error
  const [testError, setTestError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);

  function selectType(sourceType) {
    setType(sourceType);
    setStep(1);
  }

  function handleCredentialsChange(value) {
    setCredentialsInput(value);
    setTestState("idle");
  }

  async function handleTestConnection() {
    setTestState("loading");
    setTestError(null);
    try {
      const result = await testConnection({ type, uri, credentials_ref: credentialsInput });
      if (result.ok) {
        // Never keep an accepted secret in a rendered field: stash it for the
        // create-source submission only, and blank the visible input.
        setPendingCredentials(credentialsInput);
        setCredentialsInput("");
        setTestState("success");
      } else {
        setTestState("error");
        setTestError(result.error ?? "connection failed");
      }
    } catch {
      setTestState("error");
      setTestError("could not reach the server");
    }
  }

  async function handleAddSource() {
    setSubmitting(true);
    setSubmitError(null);
    try {
      const source = await createSource({
        type,
        uri,
        credentials_ref: pendingCredentials,
        schedule: DEFAULT_SCHEDULE,
        owner: DEFAULT_OWNER,
        sensitivity: DEFAULT_SENSITIVITY,
      });
      setPendingCredentials("");
      onSourceCreated?.(source);
    } catch {
      setSubmitError("Could not create the source");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div data-testid="add-source-wizard">
      <Stepper steps={STEPS} activeStep={step} />

      {step === 0 && (
        <div data-testid="wizard-step-type" role="radiogroup" aria-label="Source type">
          {SOURCE_TYPES.map((t) => (
            <button
              key={t.id}
              type="button"
              data-testid={`type-tile-${t.id}`}
              disabled={!t.enabled}
              onClick={() => t.enabled && selectType(t.id)}
            >
              {t.label}
              {!t.enabled && <span> (Coming soon)</span>}
            </button>
          ))}
        </div>
      )}

      {step === 1 && (
        <div data-testid="wizard-step-connect">
          <label>
            Repository URL
            <input
              data-testid="connect-uri-input"
              type="text"
              value={uri}
              onChange={(e) => setUri(e.target.value)}
            />
          </label>
          <label>
            Credentials (token)
            <input
              data-testid="connect-credentials-input"
              type="password"
              value={credentialsInput}
              onChange={(e) => handleCredentialsChange(e.target.value)}
            />
          </label>

          <button type="button" data-testid="test-connection-button" onClick={handleTestConnection}>
            Test connection
          </button>

          {testState === "loading" && <Skeleton shape="row" count={1} />}
          {testState === "success" && (
            <p data-testid="connect-success" role="status">
              Connection succeeded
            </p>
          )}
          {testState === "error" && <ErrorBanner message={testError} />}

          {submitError && <ErrorBanner message={submitError} />}

          <button
            type="button"
            data-testid="add-source-submit"
            disabled={testState !== "success" || submitting}
            onClick={handleAddSource}
          >
            Add source
          </button>
          <button type="button" onClick={() => setStep(0)}>
            Back
          </button>
          <button type="button" onClick={onCancel}>
            Cancel
          </button>
        </div>
      )}
    </div>
  );
}
