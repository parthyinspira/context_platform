import { useCallback, useEffect, useRef, useState } from "react";

// ── Entity type config ────────────────────────────────────────────────────────

const RELATION_COLOR = {
  CONTAINS: "#3B82F6", DEPENDS_ON: "#F59E0B", DOCUMENTS: "#10B981",
  READS_FROM: "#8B5CF6", WRITES_TO: "#EF4444", DERIVED_FROM: "#EC4899",
  OWNED_BY: "#6B7280",
};

const TYPE_CONFIG = {
  Repository: { color: "#38BDF8", glow: "#38BDF840", r: 14 },
  Service:    { color: "#A78BFA", glow: "#A78BFA40", r: 13 },
  Module:     { color: "#818CF8", glow: "#818CF840", r: 11 },
  Table:      { color: "#34D399", glow: "#34D39940", r: 12 },
  Column:     { color: "#6EE7B7", glow: "#6EE7B740", r: 9  },
  Dashboard:  { color: "#FB923C", glow: "#FB923C40", r: 12 },
  Job:        { color: "#FBBF24", glow: "#FBBF2440", r: 11 },
  Document:   { color: "#F472B6", glow: "#F472B640", r: 11 },
  Person:     { color: "#F87171", glow: "#F87171A0", r: 13 },
  Team:       { color: "#FF6B6B", glow: "#FF6B6B40", r: 14 },
  default:    { color: "#94A3B8", glow: "#94A3B840", r: 10 },
};

function cfg(type) { return TYPE_CONFIG[type] ?? TYPE_CONFIG.default; }

// ── Force simulation (spring + repulsion + center) ────────────────────────────

function initSimulation(nodes, edges) {
  const pos = {};
  // Cluster by source_id to give connected components head-starts near each other
  const sources = [...new Set(nodes.map((n) => n.source_id))];
  nodes.forEach((n, i) => {
    const si = sources.indexOf(n.source_id);
    const clusterAngle = (si / Math.max(sources.length, 1)) * Math.PI * 2;
    const clusterR = sources.length > 1 ? 180 : 0;
    const localAngle = (i / nodes.length) * Math.PI * 2;
    const localR = Math.min(80, 20 + nodes.length * 5);
    pos[n.id] = {
      x: Math.cos(clusterAngle) * clusterR + Math.cos(localAngle) * localR,
      y: Math.sin(clusterAngle) * clusterR + Math.sin(localAngle) * localR,
      vx: 0, vy: 0,
    };
  });

  const K_REPEL = 4000;
  const K_SPRING = 0.03;
  const REST_LEN = 120;
  const DAMP = 0.85;
  const CENTER = 0.004;

  function tick() {
    const ids = Object.keys(pos);
    // Repulsion
    for (let i = 0; i < ids.length; i++) {
      for (let j = i + 1; j < ids.length; j++) {
        const a = pos[ids[i]], b = pos[ids[j]];
        const dx = a.x - b.x, dy = a.y - b.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 0.1;
        const force = K_REPEL / (dist * dist);
        a.vx += (dx / dist) * force; a.vy += (dy / dist) * force;
        b.vx -= (dx / dist) * force; b.vy -= (dy / dist) * force;
      }
    }
    // Spring
    edges.forEach((e) => {
      const a = pos[e.source], b = pos[e.target];
      if (!a || !b) return;
      const dx = b.x - a.x, dy = b.y - a.y;
      const dist = Math.sqrt(dx * dx + dy * dy) || 0.1;
      const f = K_SPRING * (dist - REST_LEN);
      a.vx += (dx / dist) * f; a.vy += (dy / dist) * f;
      b.vx -= (dx / dist) * f; b.vy -= (dy / dist) * f;
    });
    // Center pull + dampen
    ids.forEach((id) => {
      const p = pos[id];
      p.vx = (p.vx - p.x * CENTER) * DAMP;
      p.vy = (p.vy - p.y * CENTER) * DAMP;
      p.x += p.vx; p.y += p.vy;
    });
  }

  return { pos, tick };
}

// ── Legend ────────────────────────────────────────────────────────────────────

function Legend({ types }) {
  return (
    <div style={{ position: "absolute", top: 12, right: 12, background: "#0F172ACC", backdropFilter: "blur(6px)", borderRadius: 10, padding: "10px 14px", maxHeight: 220, overflowY: "auto" }}>
      <div style={{ fontSize: 10, fontWeight: 700, color: "#64748B", textTransform: "uppercase", letterSpacing: ".08em", marginBottom: 8 }}>Entity types</div>
      {types.map((t) => {
        const c = cfg(t);
        return (
          <div key={t} style={{ display: "flex", alignItems: "center", gap: 7, marginBottom: 5 }}>
            <div style={{ width: 10, height: 10, borderRadius: "50%", background: c.color, boxShadow: `0 0 6px ${c.color}` }} />
            <span style={{ fontSize: 11, color: "#CBD5E1" }}>{t}</span>
          </div>
        );
      })}
    </div>
  );
}

// ── Main canvas component ─────────────────────────────────────────────────────

export function GraphCanvas({ nodes = [], edges = [], agentTrace = [] }) {
  const canvasRef = useRef(null);
  const stateRef = useRef(null);   // { pos, nodes, edges, agentTrace, zoom, tx, ty, dragging, hovered, pinned }
  const rafRef = useRef(null);
  const simRef = useRef(null);
  const [hoveredNode, setHoveredNode] = useState(null);

  const uniqueTypes = [...new Set(nodes.map((n) => n.type))];

  // ── Init / reset simulation when nodes/edges change ──────────────────────────
  useEffect(() => {
    if (nodes.length === 0) return;
    const { pos, tick } = initSimulation(nodes, edges);
    simRef.current = { tick, warming: 120 };
    if (!stateRef.current) {
      stateRef.current = { pos, zoom: 1, tx: 0, ty: 0, dragging: null, hovered: null, pinned: new Set() };
    } else {
      stateRef.current.pos = pos;
    }
    stateRef.current.nodes = nodes;
    stateRef.current.edges = edges;
    stateRef.current.agentTrace = agentTrace;
  }, [nodes, edges]);

  // Keep agentTrace in sync without resetting sim
  useEffect(() => {
    if (stateRef.current) stateRef.current.agentTrace = agentTrace;
  }, [agentTrace]);

  // ── Draw loop ─────────────────────────────────────────────────────────────────
  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    const s = stateRef.current;
    if (!canvas || !s || !s.nodes) { rafRef.current = requestAnimationFrame(draw); return; }
    const { nodes: ns, edges: es, pos, zoom, tx, ty, hovered, agentTrace: trace } = s;
    const traceSet = new Set(trace ?? []);

    // Warm up simulation
    if (simRef.current?.warming > 0) {
      for (let i = 0; i < 8; i++) simRef.current.tick();
      simRef.current.warming--;
    } else if (simRef.current && !s.dragging) {
      simRef.current.tick();
    }

    const W = canvas.width, H = canvas.height;
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, W, H);

    const cx = W / 2 + tx, cy = H / 2 + ty;

    // Draw edges
    es.forEach((e) => {
      const a = pos[e.source], b = pos[e.target];
      if (!a || !b) return;
      const ax = cx + a.x * zoom, ay = cy + a.y * zoom;
      const bx = cx + b.x * zoom, by = cy + b.y * zoom;

      // Edge highlight if both endpoints in trace
      const hot = traceSet.has(e.source) && traceSet.has(e.target);
      const relColor = RELATION_COLOR[e.relation] ?? "#334155";
      ctx.beginPath();
      ctx.moveTo(ax, ay);
      ctx.lineTo(bx, by);
      ctx.strokeStyle = hot ? "#F59E0B88" : relColor + "55";
      ctx.lineWidth = hot ? 2.5 : 1.5;
      ctx.stroke();

      // Arrow
      const angle = Math.atan2(by - ay, bx - ax);
      const ec = cfg(ns.find((n) => n.id === e.target)?.type);
      const len = 8 * zoom;
      const ex = bx - Math.cos(angle) * ec.r * zoom;
      const ey = by - Math.sin(angle) * ec.r * zoom;
      ctx.beginPath();
      ctx.moveTo(ex, ey);
      ctx.lineTo(ex - len * Math.cos(angle - 0.4), ey - len * Math.sin(angle - 0.4));
      ctx.lineTo(ex - len * Math.cos(angle + 0.4), ey - len * Math.sin(angle + 0.4));
      ctx.closePath();
      ctx.fillStyle = hot ? "#F59E0B" : relColor;
      ctx.fill();

      // Relation label on hover
      if (hovered && (e.source === hovered || e.target === hovered) && e.relation) {
        const mx = (ax + bx) / 2, my = (ay + by) / 2;
        ctx.font = "9px monospace";
        ctx.fillStyle = "#64748B";
        ctx.textAlign = "center";
        ctx.fillText(e.relation, mx, my - 4);
      }
    });

    // Draw nodes
    ns.forEach((node) => {
      const p = pos[node.id];
      if (!p) return;
      const x = cx + p.x * zoom, y = cy + p.y * zoom;
      const c = cfg(node.type);
      const r = c.r * zoom;
      const isHovered = hovered === node.id;
      const isTrace = traceSet.has(node.id);

      // Glow
      const glowR = isTrace ? r * 2.5 : isHovered ? r * 2 : r * 1.5;
      const grad = ctx.createRadialGradient(x, y, 0, x, y, glowR);
      grad.addColorStop(0, isTrace ? "#F59E0B60" : c.glow);
      grad.addColorStop(1, "transparent");
      ctx.beginPath();
      ctx.arc(x, y, glowR, 0, Math.PI * 2);
      ctx.fillStyle = grad;
      ctx.fill();

      // Node circle
      ctx.beginPath();
      ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.fillStyle = isTrace ? "#F59E0B" : c.color;
      ctx.fill();
      if (isHovered || isTrace) {
        ctx.strokeStyle = isTrace ? "#FDE68A" : "#fff";
        ctx.lineWidth = 2;
        ctx.stroke();
      }

      // Label
      const label = node.label ?? node.name ?? node.id;
      ctx.font = `${isHovered ? "bold " : ""}${Math.max(9, 11 * zoom)}px sans-serif`;
      ctx.fillStyle = isHovered ? "#F8FAFC" : "#CBD5E1";
      ctx.textAlign = "center";
      ctx.fillText(label, x, y + r + 12 * zoom);
    });

    rafRef.current = requestAnimationFrame(draw);
  }, []);

  useEffect(() => {
    rafRef.current = requestAnimationFrame(draw);
    return () => { if (rafRef.current) cancelAnimationFrame(rafRef.current); };
  }, [draw]);

  // ── Resize canvas ─────────────────────────────────────────────────────────────
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const obs = new ResizeObserver(() => {
      canvas.width = canvas.offsetWidth;
      canvas.height = canvas.offsetHeight;
    });
    obs.observe(canvas);
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;
    return () => obs.disconnect();
  }, []);

  // ── Mouse events ──────────────────────────────────────────────────────────────
  function worldCoords(e) {
    const rect = canvasRef.current.getBoundingClientRect();
    const s = stateRef.current;
    const mx = e.clientX - rect.left, my = e.clientY - rect.top;
    const cx = canvasRef.current.width / 2 + s.tx;
    const cy = canvasRef.current.height / 2 + s.ty;
    return { wx: (mx - cx) / s.zoom, wy: (my - cy) / s.zoom };
  }

  function findNode(wx, wy) {
    const s = stateRef.current;
    if (!s?.nodes) return null;
    return s.nodes.find((n) => {
      const p = s.pos[n.id];
      if (!p) return false;
      const dx = p.x - wx, dy = p.y - wy;
      return Math.sqrt(dx * dx + dy * dy) < cfg(n.type).r + 4;
    }) ?? null;
  }

  function onMouseMove(e) {
    const s = stateRef.current;
    if (!s) return;
    if (s.dragging) {
      if (s.dragging === "__pan__") {
        s.tx += e.movementX; s.ty += e.movementY;
      } else {
        const { wx, wy } = worldCoords(e);
        s.pos[s.dragging] = { ...s.pos[s.dragging], x: wx, y: wy, vx: 0, vy: 0 };
      }
      return;
    }
    const { wx, wy } = worldCoords(e);
    const hit = findNode(wx, wy);
    const id = hit?.id ?? null;
    if (id !== s.hovered) {
      s.hovered = id;
      setHoveredNode(hit);
      canvasRef.current.style.cursor = id ? "grab" : "default";
    }
  }

  function onMouseDown(e) {
    const s = stateRef.current;
    if (!s) return;
    const { wx, wy } = worldCoords(e);
    const hit = findNode(wx, wy);
    s.dragging = hit ? hit.id : "__pan__";
    if (hit) canvasRef.current.style.cursor = "grabbing";
  }

  function onMouseUp() {
    const s = stateRef.current;
    if (s) s.dragging = null;
    if (canvasRef.current) canvasRef.current.style.cursor = s?.hovered ? "grab" : "default";
  }

  function onWheel(e) {
    e.preventDefault();
    const s = stateRef.current;
    if (!s) return;
    s.zoom = Math.max(0.2, Math.min(3, s.zoom * (e.deltaY > 0 ? 0.9 : 1.1)));
  }

  function handleFit() {
    const s = stateRef.current;
    if (!s) return;
    s.tx = 0; s.ty = 0; s.zoom = 1;
  }

  function handleReset() {
    const s = stateRef.current;
    if (!s || !s.nodes) return;
    s.tx = 0; s.ty = 0; s.zoom = 1;
    const { pos, tick } = initSimulation(s.nodes, s.edges);
    s.pos = pos;
    simRef.current = { tick, warming: 120 };
  }

  if (nodes.length === 0) {
    return (
      <div style={{ height: 500, background: "#0D1117", borderRadius: 12, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 12, color: "#334155" }}>
        <div style={{ fontSize: 48 }}>🕸️</div>
        <div style={{ fontSize: 15, fontWeight: 600, color: "#64748B" }}>No knowledge graph yet</div>
        <div style={{ fontSize: 13, color: "#334155" }}>Register and harvest a source to populate the graph</div>
      </div>
    );
  }

  return (
    <div style={{ position: "relative", height: "100%", borderRadius: 12, overflow: "hidden", background: "#0D1117", border: "1px solid #1E293B" }}>
      {/* Toolbar */}
      <div style={{ position: "absolute", top: 12, left: 12, display: "flex", gap: 8, zIndex: 10 }}>
        <button type="button" onClick={handleFit}
          style={{ background: "#1E293B", color: "#94A3B8", border: "1px solid #334155", borderRadius: 7, padding: "5px 12px", fontSize: 12, cursor: "pointer", fontWeight: 600 }}>
          ⊡ Fit
        </button>
        <button type="button" onClick={handleReset}
          style={{ background: "#1E293B", color: "#94A3B8", border: "1px solid #334155", borderRadius: 7, padding: "5px 12px", fontSize: 12, cursor: "pointer", fontWeight: 600 }}>
          ↺ Reset
        </button>
        <div style={{ background: "#1E293B", color: "#64748B", border: "1px solid #1E293B", borderRadius: 7, padding: "5px 12px", fontSize: 11 }}>
          {nodes.length} nodes · {edges.length} edges · scroll to zoom · drag to pan/move
        </div>
      </div>

      {/* Hover tooltip */}
      {hoveredNode && (
        <div style={{ position: "absolute", bottom: 12, left: 12, background: "#1E293BEE", backdropFilter: "blur(6px)", borderRadius: 10, padding: "8px 14px", border: `1px solid ${cfg(hoveredNode.type).color}44`, zIndex: 10 }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: cfg(hoveredNode.type).color }}>{hoveredNode.label ?? hoveredNode.name}</div>
          <div style={{ fontSize: 11, color: "#64748B", marginTop: 2 }}>{hoveredNode.type}</div>
          {hoveredNode.id && <div style={{ fontSize: 10, color: "#334155", fontFamily: "monospace", marginTop: 2 }}>{hoveredNode.id}</div>}
        </div>
      )}

      <Legend types={uniqueTypes} />

      <canvas
        ref={canvasRef}
        style={{ width: "100%", height: "100%", display: "block" }}
        onMouseMove={onMouseMove}
        onMouseDown={onMouseDown}
        onMouseUp={onMouseUp}
        onMouseLeave={onMouseUp}
        onWheel={onWheel}
      />
    </div>
  );
}
