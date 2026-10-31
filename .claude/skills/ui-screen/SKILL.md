---
name: ui-screen
description: Build or change a UI screen per docs/UI_DESIGN.md with tokens, shared components, all states, accessibility checks and a screenshot.
---

Read `docs/UI_DESIGN.md` (the screen's section, tokens, component inventory, quality bar) and the change's spec delta.

1. Use tokens from `ui/src/tokens.json` and existing components; add a new component only when none fits, and add it to the component library.
2. Implement every state: empty, loading (skeleton), error, partial, success.
3. Wire to the UI API; use seeded demo data so the screen is reviewable without live sources.
4. Accessibility: keyboard navigation, visible focus, AA contrast, no colour-only meaning, labels; graph screens need a list-view alternative.
5. Performance for the graph: node cap with clustering and level-of-detail labels; first paint under 2 s at 2,000 nodes.
6. Verify in a browser (Playwright): screenshot each state at 1280 px and attach to `verification.md`; check the console for errors.
7. Note deviations from the design spec in the PR; do not silently change the design.
