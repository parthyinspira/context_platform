import { useEffect, useState } from "react";
import { Stepper } from "./Stepper.jsx";
import { Skeleton } from "./Skeleton.jsx";
import { ErrorBanner } from "./ErrorBanner.jsx";
import { ScopeTree } from "./ScopeTree.jsx";
import { createSource, discoverSource, testConnection } from "../api.js";

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

const STEPS = [{ label: "Type" }, { label: "Connect" }, { label: "Discover" }];

function scopeNodeFromApi(node) {
  return {
    id: node.id,
    label: node.name,
    count: node.size_hint ?? undefined,
    checked: false,
    children: (node.children ?? []).map(scopeNodeFromApi),
  };
}

function setAllChecked(nodes, checked) {
  return nodes.map((n) => ({ ...n, checked, children: setAllChecked(n.children ?? [], checked) }));
}

function toggleTree(nodes, targetId) {
  return nodes.map((n) => {
    if (n.id === targetId) {
      const next = !n.checked;
      return { ...n, checked: next, children: setAllChecked(n.children ?? [], next) };
    }
    if (n.children?.length) {
      const children = toggleTree(n.children, targetId);
      return { ...n, checked: children.every((c) => c.checked), children };
    }
    return n;
  });
}

function matchesQuery(node, query) {
  if (node.label.toLowerCase().includes(query)) return true;
  return (node.children ?? []).some((c) => matchesQuery(c, query));
}

function filterTree(nodes, query) {
  if (!query) return nodes;
  return nodes
    .filter((n) => matchesQuery(n, query))
    .map((n) => ({ ...n, children: filterTree(n.children ?? [], query) }));
}

function selectAllLeaves(nodes) {
  return nodes.map((n) => {
    if (!n.children?.length) {
      return { ...n, checked: true };
    }
    const children = selectAllLeaves(n.children);
    return { ...n, children, checked: children.every((c) => c.checked) };
  });
}

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
  const [createdSource, setCreatedSource] = useState(null);
  const [scopeState, setScopeState] = useState("idle"); // idle | loading | success | error
  const [scopeNodes, setScopeNodes] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");

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
      setCreatedSource(source);
      setStep(2);
      onSourceCreated?.(source);
    } catch {
      setSubmitError("Could not create the source");
    } finally {
      setSubmitting(false);
    }
  }

  useEffect(() => {
    if (step !== 2 || !createdSource) return;
    let cancelled = false;
    setScopeState("loading");
    discoverSource(createdSource.id)
      .then((tree) => {
        if (cancelled) return;
        setScopeNodes((tree.roots ?? []).map(scopeNodeFromApi));
        setScopeState("success");
      })
      .catch(() => {
        if (cancelled) return;
        setScopeState("error");
      });
    return () => {
      cancelled = true;
    };
  }, [step, createdSource]);

  const visibleScopeNodes = filterTree(scopeNodes, searchQuery.trim().toLowerCase());
  const scopeTreeRenderState =
    scopeState === "success" && scopeNodes.length === 0 ? "empty" : scopeState;

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

      {step === 2 && (
        <div data-testid="wizard-step-discover">
          <label>
            Search
            <input
              data-testid="scope-search-input"
              type="search"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </label>
          <button
            type="button"
            data-testid="select-recommended-button"
            onClick={() => setScopeNodes((nodes) => selectAllLeaves(nodes))}
          >
            Select recommended
          </button>
          <ScopeTree
            state={scopeTreeRenderState}
            nodes={visibleScopeNodes}
            onToggle={(node) => setScopeNodes((nodes) => toggleTree(nodes, node.id))}
          />
          <button type="button" onClick={onCancel}>
            Cancel
          </button>
        </div>
      )}
    </div>
  );
}
