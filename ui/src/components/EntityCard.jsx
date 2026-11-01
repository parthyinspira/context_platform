import { Skeleton } from "./Skeleton.jsx";
import { ErrorBanner } from "./ErrorBanner.jsx";
import { EmptyState } from "./EmptyState.jsx";

// Graph inspector entity card (KAN-68), per UI_DESIGN.md 4.1: properties, edges
// grouped by relation, citations (source link, harvested_at, run id), owner,
// open in source.
export function EntityCard({ state = "empty", entity }) {
  if (state === "loading") {
    return (
      <div data-testid="entity-card" data-state="loading">
        <Skeleton shape="block" count={3} />
      </div>
    );
  }
  if (state === "error") {
    return (
      <div data-testid="entity-card" data-state="error">
        <ErrorBanner message="Failed to load entity" />
      </div>
    );
  }
  if (state === "empty" || !entity) {
    return (
      <div data-testid="entity-card" data-state="empty">
        <EmptyState message="Select a node to see its details" />
      </div>
    );
  }

  return (
    <div data-testid="entity-card" data-state="success">
      <h3 data-testid="entity-name">{entity.name}</h3>
      <p data-testid="entity-type">{entity.type}</p>

      <section>
        <h4>Properties</h4>
        <dl data-testid="entity-props">
          {Object.entries(entity.props ?? {}).map(([key, value]) => (
            <div key={key}>
              <dt>{key}</dt>
              <dd data-testid={`entity-prop-${key}`}>{String(value)}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section>
        <h4>Edges</h4>
        {Object.entries(entity.edges_by_relation ?? {}).map(([relation, edges]) => (
          <div key={relation}>
            <h5>{relation}</h5>
            <ul data-testid={`entity-relation-${relation}`}>
              {edges.map((edge) => (
                <li key={edge.id}>
                  {edge.direction === "out" ? "→" : "←"} {edge.entity_name} ({edge.entity_type})
                </li>
              ))}
            </ul>
          </div>
        ))}
      </section>

      <section>
        <h4>Citations</h4>
        <ul data-testid="citations">
          {(entity.citations ?? []).map((citation, i) => (
            <li key={i} data-testid="citation-chip">
              <a href={citation.source_link} target="_blank" rel="noreferrer">
                {citation.source_link}
              </a>
              {" · "}
              {citation.harvested_at}
              {" · "}
              {citation.run_id ? `run ${citation.run_id}` : "unknown run"}
            </li>
          ))}
        </ul>
      </section>

      <p data-testid="entity-owner">Owner: {entity.owner}</p>

      <a data-testid="open-in-source" href={entity.source_uri} target="_blank" rel="noreferrer">
        Open in source
      </a>
    </div>
  );
}
