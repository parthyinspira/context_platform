import { useEffect, useState } from "react";
import { getGraph } from "../api.js";
import { GraphCanvas } from "./GraphCanvas.jsx";
import { EmptyState } from "./EmptyState.jsx";
import { ErrorBanner } from "./ErrorBanner.jsx";

export function GraphScreen() {
  const [state, setState] = useState("loading");
  const [graph, setGraph] = useState({ nodes: [], edges: [] });

  useEffect(() => {
    let cancelled = false;
    setState("loading");
    getGraph()
      .then((data) => {
        if (cancelled) return;
        setGraph(data);
        setState(data.nodes.length === 0 ? "empty" : "success");
      })
      .catch(() => {
        if (cancelled) return;
        setState("error");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (state === "loading") {
    return <p data-testid="graph-loading">Loading graph…</p>;
  }

  if (state === "error") {
    return <ErrorBanner message="Could not load the knowledge graph." />;
  }

  if (state === "empty") {
    return <EmptyState message="No knowledge graph yet." actionLabel="Add a source" />;
  }

  return <GraphCanvas nodes={graph.nodes} edges={graph.edges} />;
}
