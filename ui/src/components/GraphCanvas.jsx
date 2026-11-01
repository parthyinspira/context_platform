import { useEffect, useRef } from "react";
import cytoscape from "cytoscape";
import tokens from "../tokens.json";

const { families, typeFamily, typeShape } = tokens.graph;

function familyForType(type) {
  return typeFamily[type] ?? "Code";
}

function shapeForType(type) {
  return typeShape[type] ?? "ellipse";
}

function toElements(nodes, edges) {
  const nodeElements = nodes.map((node) => ({
    data: {
      id: node.id,
      label: node.label,
      type: node.type,
      family: familyForType(node.type),
    },
  }));
  const edgeElements = edges.map((edge) => ({
    data: {
      id: edge.id,
      source: edge.source,
      target: edge.target,
      relation: edge.relation,
    },
  }));
  return [...nodeElements, ...edgeElements];
}

function buildStyle() {
  const familyRules = Object.entries(families).map(([family, color]) => ({
    selector: `node[family = "${family}"]`,
    style: { "background-color": color },
  }));
  const shapeRules = Object.entries(typeShape).map(([type, shape]) => ({
    selector: `node[type = "${type}"]`,
    style: { shape },
  }));
  return [
    { selector: "node", style: { label: "data(label)" } },
    ...familyRules,
    ...shapeRules,
    { selector: "edge", style: { "curve-style": "bezier", "target-arrow-shape": "triangle" } },
    { selector: ".highlighted", style: { "border-width": 3, "border-color": tokens.light.accent } },
    { selector: ".dimmed", style: { opacity: 0.2 } },
  ];
}

export function GraphCanvas({ nodes, edges }) {
  const containerRef = useRef(null);
  const cyRef = useRef(null);

  useEffect(() => {
    const cy = cytoscape({
      container: containerRef.current,
      elements: toElements(nodes, edges),
      style: buildStyle(),
      layout: { name: "cose" },
    });
    cyRef.current = cy;

    cy.on("tap", "node", (event) => {
      const node = event.target;
      const neighbourhood = node.closedNeighborhood();
      cy.elements().removeClass("highlighted").removeClass("dimmed");
      cy.elements().addClass("dimmed");
      neighbourhood.removeClass("dimmed").addClass("highlighted");
    });

    cy.on("tap", (event) => {
      if (event.target === cy) {
        cy.elements().removeClass("highlighted").removeClass("dimmed");
      }
    });

    return () => {
      cy.destroy();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodes, edges]);

  function handleFit() {
    cyRef.current?.fit();
  }

  function handleReset() {
    const cy = cyRef.current;
    if (!cy) return;
    cy.elements().removeClass("highlighted").removeClass("dimmed");
    cy.layout({ name: "cose" }).run();
    cy.fit();
  }

  return (
    <div>
      <div className="mb-2 flex gap-2">
        <button type="button" onClick={handleFit}>
          Fit
        </button>
        <button type="button" onClick={handleReset}>
          Reset
        </button>
      </div>
      <div data-testid="graph-cytoscape" ref={containerRef} style={{ width: "100%", height: "600px" }} />
    </div>
  );
}
