import { useEffect, useState } from "react";
import { Stepper } from "./Stepper.jsx";
import { Skeleton } from "./Skeleton.jsx";
import { ErrorBanner } from "./ErrorBanner.jsx";
import { ScopeTree } from "./ScopeTree.jsx";
import { PlanSummaryCard } from "./PlanSummaryCard.jsx";
import { createRun, createSource, discoverSource, planSource, testConnection } from "../api.js";

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

const STEPS = [{ label: "Type" }, { label: "Connect" }, { label: "Discover" }, { label: "Plan & run" }];

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

function collectCheckedLeafIds(nodes) {
  return nodes.flatMap((n) =>
    n.children?.length ? collectCheckedLeafIds(n.children) : n.checked ? [n.id] : []
  );
}

function parsePatternList(text) {
  return text
    .split(",")
    .map((p) => p.trim())
    .filter(Boolean);
}

export function AddSourceWizard({ onSourceCreated, onRunStarted, onCancel }) {
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
  const [selectedRefs, setSelectedRefs] = useState(null);
  const [planState, setPlanState] = useState("idle"); // idle | loading | success | error
  const [planData, setPlanData] = useState(null);
  const [includeText, setIncludeText] = useState("");
  const [excludeText, setExcludeText] = useState("");
  const [runSubmitting, setRunSubmitting] = useState(false);
  const [runError, setRunError] = useState(null);

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

  function handleGoToPlan() {
    const refs = collectCheckedLeafIds(scopeNodes);
    setSelectedRefs(refs);
    setStep(3);
  }

  useEffect(() => {
    if (step !== 3 || !createdSource || selectedRefs === null) return;
    let cancelled = false;
    setPlanState("loading");
    setRunError(null);
    planSource(createdSource.id, { selected_refs: selectedRefs })
      .then((data) => {
        if (cancelled) return;
        setPlanData(data);
        setIncludeText((data.plan.include ?? []).join(", "));
        setExcludeText((data.plan.exclude ?? []).join(", "));
        setPlanState("success");
      })
      .catch(() => {
        if (cancelled) return;
        setPlanState("error");
      });
    return () => {
      cancelled = true;
    };
  }, [step, createdSource, selectedRefs]);

  async function handleRunNow() {
    setRunSubmitting(true);
    setRunError(null);
    try {
      const run = await createRun(createdSource.id, {
        include: parsePatternList(includeText),
        exclude: parsePatternList(excludeText),
        size_cap_bytes: planData.plan.size_cap_bytes,
        budgets: planData.plan.budgets,
      });
      onRunStarted?.(run);
    } catch {
      setRunError("Could not start the run");
    } finally {
      setRunSubmitting(false);
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
          <button
            type="button"
            data-testid="discover-next-button"
            disabled={scopeState !== "success"}
            onClick={handleGoToPlan}
          >
            Next: plan
          </button>
          <button type="button" onClick={onCancel}>
            Cancel
          </button>
        </div>
      )}

      {step === 3 && (
        <div data-testid="wizard-step-plan">
          <PlanSummaryCard
            state={planState === "idle" ? "loading" : planState}
            profile={planData?.profile}
            plan={{ include: parsePatternList(includeText), exclude: parsePatternList(excludeText) }}
            estimatedBytes={planData?.estimated_bytes}
            estimatedFiles={planData?.estimated_files}
            estimatedSeconds={planData?.estimated_seconds}
            estimatedTokens={planData?.estimated_tokens}
            budgetWarnings={planData?.budget_warnings}
          />

          {planState === "success" && (
            <>
              <label>
                Include patterns (comma-separated)
                <input
                  data-testid="plan-include-input"
                  type="text"
                  value={includeText}
                  onChange={(e) => setIncludeText(e.target.value)}
                />
              </label>
              <label>
                Exclude patterns (comma-separated)
                <input
                  data-testid="plan-exclude-input"
                  type="text"
                  value={excludeText}
                  onChange={(e) => setExcludeText(e.target.value)}
                />
              </label>

              {runError && <ErrorBanner message={runError} />}

              <button
                type="button"
                data-testid="run-now-button"
                disabled={runSubmitting}
                onClick={handleRunNow}
              >
                Run now
              </button>
            </>
          )}

          <button type="button" onClick={onCancel}>
            Cancel
          </button>
        </div>
      )}
    </div>
  );
}
