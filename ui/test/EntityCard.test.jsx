import { describe, it, expect, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import { EntityCard } from "../src/components/EntityCard.jsx";

afterEach(cleanup);

function entity(overrides = {}) {
  return {
    id: "e1",
    type: "Repository",
    name: "repo-a",
    props: { language: "python", stars: 42 },
    owner: "alice@acme.com",
    source_uri: "https://github.com/acme/repo-a",
    edges_by_relation: {
      DEPENDS_ON: [{ id: "ed1", direction: "out", entity_id: "e2", entity_type: "Table", entity_name: "table-a" }],
      CONTAINS: [{ id: "ed2", direction: "in", entity_id: "e3", entity_type: "Service", entity_name: "svc-a" }],
    },
    citations: [{ source_link: "https://github.com/acme/repo-a", harvested_at: "2026-02-01T00:00:00Z", run_id: "run-early" }],
    ...overrides,
  };
}

describe("EntityCard", () => {
  it("renders properties, edges grouped by relation, citations, owner and open-in-source", () => {
    render(<EntityCard state="success" entity={entity()} />);

    expect(screen.getByTestId("entity-prop-language")).toHaveTextContent("python");
    expect(screen.getByTestId("entity-prop-stars")).toHaveTextContent("42");

    expect(screen.getByTestId("entity-relation-DEPENDS_ON")).toHaveTextContent("table-a");
    expect(screen.getByTestId("entity-relation-CONTAINS")).toHaveTextContent("svc-a");

    const citation = screen.getByTestId("citation-chip");
    expect(citation).toHaveTextContent("https://github.com/acme/repo-a");
    expect(citation).toHaveTextContent("2026-02-01T00:00:00Z");
    expect(citation).toHaveTextContent("run-early");

    expect(screen.getByTestId("entity-owner")).toHaveTextContent("alice@acme.com");

    const openInSource = screen.getByTestId("open-in-source");
    expect(openInSource).toHaveAttribute("href", "https://github.com/acme/repo-a");
  });

  it("shows a citation with no run id as such", () => {
    render(
      <EntityCard
        state="success"
        entity={entity({ citations: [{ source_link: "https://x", harvested_at: "2026-02-01T00:00:00Z", run_id: null }] })}
      />
    );

    expect(screen.getByTestId("citation-chip")).toHaveTextContent("unknown run");
  });

  it("shows a skeleton while loading", () => {
    render(<EntityCard state="loading" />);
    expect(screen.getByTestId("skeleton")).toBeInTheDocument();
  });

  it("shows an error banner on error", () => {
    render(<EntityCard state="error" />);
    expect(screen.getByTestId("error-banner")).toBeInTheDocument();
  });

  it("shows an empty state when nothing is selected", () => {
    render(<EntityCard state="empty" />);
    expect(screen.getByTestId("empty-state")).toBeInTheDocument();
  });
});
