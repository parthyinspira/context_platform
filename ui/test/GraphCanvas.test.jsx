import { describe, it, expect, vi, afterEach, beforeEach } from "vitest";
import { render, cleanup, fireEvent } from "@testing-library/react";
import tokens from "../src/tokens.json";

const handlers = {};
let lastStyle;
let lastElements;
let lastLayoutOptions;

function makeCollection(ids) {
  const collection = {
    ids: new Set(ids),
    addClass: vi.fn(function addClass() {
      return collection;
    }),
    removeClass: vi.fn(function removeClass() {
      return collection;
    }),
    union: vi.fn((other) => makeCollection([...collection.ids, ...(other?.ids ?? [])])),
  };
  return collection;
}

let allElementsCollection;

const cyMock = {
  on: vi.fn((event, selectorOrHandler, handler) => {
    if (typeof handler === "function") {
      handlers[`${event}:${selectorOrHandler}`] = handler;
    } else {
      handlers[`${event}:core`] = selectorOrHandler;
    }
  }),
  fit: vi.fn(),
  layout: vi.fn(() => ({ run: vi.fn() })),
  elements: vi.fn(() => allElementsCollection),
  getElementById: vi.fn((id) => ({
    id: () => id,
    closedNeighborhood: vi.fn(() => makeCollection([id, "neighbour-of-" + id])),
  })),
  destroy: vi.fn(),
};

vi.mock("cytoscape", () => ({
  default: vi.fn((opts) => {
    lastElements = opts.elements;
    lastStyle = opts.style;
    lastLayoutOptions = opts.layout;
    return cyMock;
  }),
}));

import cytoscape from "cytoscape";
import { GraphCanvas } from "../src/components/GraphCanvas.jsx";

const NODES = [
  { id: "repo-1", label: "billing-service", type: "Repository" },
  { id: "svc-1", label: "billing", type: "Service" },
  { id: "person-1", label: "Jane", type: "Person" },
];
const EDGES = [{ id: "e1", source: "repo-1", target: "svc-1", relation: "CONTAINS" }];

beforeEach(() => {
  allElementsCollection = makeCollection(["n1", "n2", "n3"]);
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  for (const key of Object.keys(handlers)) delete handlers[key];
});

describe("GraphCanvas", () => {
  it("initializes cytoscape with a force-directed (cose) layout", () => {
    render(<GraphCanvas nodes={NODES} edges={EDGES} />);
    expect(cytoscape).toHaveBeenCalledTimes(1);
    expect(lastLayoutOptions.name).toBe("cose");
  });

  it("maps nodes and edges into cytoscape elements with type/family data", () => {
    render(<GraphCanvas nodes={NODES} edges={EDGES} />);
    const nodeEls = lastElements.filter((el) => !el.data.source);
    const repoEl = nodeEls.find((el) => el.data.id === "repo-1");
    expect(repoEl.data.type).toBe("Repository");
    expect(repoEl.data.family).toBe("Code");

    const edgeEls = lastElements.filter((el) => el.data.source);
    expect(edgeEls).toHaveLength(1);
    expect(edgeEls[0].data).toMatchObject({ source: "repo-1", target: "svc-1" });
  });

  it("colours nodes by family and shapes them by type via the style rules", () => {
    render(<GraphCanvas nodes={NODES} edges={EDGES} />);
    const codeFamilyRule = lastStyle.find(
      (rule) => rule.selector === `node[family = "Code"]`
    );
    expect(codeFamilyRule.style["background-color"]).toBe(tokens.graph.families.Code);

    const repositoryShapeRule = lastStyle.find(
      (rule) => rule.selector === `node[type = "Repository"]`
    );
    expect(repositoryShapeRule.style.shape).toBe(tokens.graph.typeShape.Repository);
  });

  it("fit button calls cy.fit()", () => {
    const { getByText } = render(<GraphCanvas nodes={NODES} edges={EDGES} />);
    fireEvent.click(getByText("Fit"));
    expect(cyMock.fit).toHaveBeenCalled();
  });

  it("reset button re-runs the layout, fits, and clears selection highlighting", () => {
    const { getByText } = render(<GraphCanvas nodes={NODES} edges={EDGES} />);
    fireEvent.click(getByText("Reset"));
    expect(cyMock.layout).toHaveBeenCalled();
    expect(cyMock.fit).toHaveBeenCalled();
    expect(cyMock.elements().removeClass).toHaveBeenCalledWith("dimmed");
  });

  it("selecting a node highlights its neighbourhood and dims the rest", () => {
    render(<GraphCanvas nodes={NODES} edges={EDGES} />);
    const tapHandler = handlers["tap:node"];
    expect(tapHandler).toBeTypeOf("function");

    const node = { id: () => "repo-1", closedNeighborhood: vi.fn(() => makeCollection(["repo-1", "svc-1"])) };
    tapHandler({ target: node });

    const neighbourhood = node.closedNeighborhood.mock.results[0].value;
    expect(neighbourhood.addClass).toHaveBeenCalledWith("highlighted");
    expect(cyMock.elements).toHaveBeenCalled();
  });

  it("tapping the background clears highlighting", () => {
    render(<GraphCanvas nodes={NODES} edges={EDGES} />);
    const bgHandler = handlers["tap:core"];
    expect(bgHandler).toBeTypeOf("function");
    bgHandler({ target: cyMock });
    expect(cyMock.elements().removeClass).toHaveBeenCalledWith("highlighted");
    expect(cyMock.elements().removeClass).toHaveBeenCalledWith("dimmed");
  });

  it("destroys the cytoscape instance on unmount", () => {
    const { unmount } = render(<GraphCanvas nodes={NODES} edges={EDGES} />);
    unmount();
    expect(cyMock.destroy).toHaveBeenCalled();
  });
});
