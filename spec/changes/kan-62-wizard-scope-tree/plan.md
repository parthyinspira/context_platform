# KAN-62: Add-source wizard: discover scope tree (lite)

Jira: https://inspiradataintegration.atlassian.net/browse/KAN-62   Branch: m8-ui-wizard-and-runs

## Scope
In: wizard step 3 ("Discover") composing the existing `ScopeTree` component: calls `POST /sources/{id}/discover` (KAN-58) after the source is created from step 2, renders the returned tree with per-node size/count, adds checkbox selection state, a search/filter input, and a "select recommended" action (recommended = every leaf node, i.e. select-all, since no per-node recommendation score exists in the `Profile`/`ScopeTree` types).
Out: persisting the selection anywhere other than wizard state (it is passed to step 4/KAN-63's plan call); server-side search or pagination of the tree (client-side filter over the already-fetched tree, sized for a hackathon demo repo).

## Acceptance criteria (from Jira)
1. After connecting, shows repos/databases/sites as a tree with sizes and counts.
2. Checkbox selection.
3. Search.
4. Select recommended.

## Requirements (at most 5)
- Step 3 SHALL call `POST /sources/{id}/discover` once the source exists and render the result with the existing `ScopeTree` component, showing each node's name, kind, size and count, nested under its parent. (scenario: Given discover returns a tree with children, When step 3 renders, Then nested nodes with their sizes are shown via `ScopeTree`)
- Each tree node SHALL have a checkbox whose checked state is tracked in wizard state; checking/unchecking a parent SHALL propagate to its children. (scenario: Given a parent with two children, When the parent checkbox is toggled on, Then both children become checked; When one child is then unchecked, Then the parent becomes indeterminate/unchecked)
- A search input SHALL filter the visible tree to nodes whose name matches the query (case-insensitive substring), keeping ancestors of a match visible. (scenario: Given a tree with a node named "billing-service", When the user types "billing", Then that node and its ancestors remain visible and non-matching siblings are hidden)
- A "select recommended" action SHALL check every leaf node in the tree in one action. (scenario: Given no nodes are checked, When "select recommended" is activated, Then every leaf node becomes checked)

## Tasks
- [ ] 1. `ui/src/api.js`: add `discoverSource(sourceId)` calling `POST /sources/{id}/discover` (test: resolves with tree shape)
- [ ] 2. Wizard step 3 component wiring `ScopeTree` to discover results with checkbox state + parent/child propagation (tests: render with sizes/counts, parent toggles children)
- [ ] 3. Search input filtering the tree (test: filters to matches + ancestors)
- [ ] 4. "Select recommended" button (test: selects all leaves)

## Risks / not verifiable here
- "Recommended" has no scoring signal in `Profile`/`ScopeTree` today (no per-node recommendation flag); minimal interpretation is "select all leaves", documented above rather than inventing a scoring heuristic out of scope for this story.

## Approval
Approved by: parthasarathy.venkatachalam (user approved spec-batch), 2026-10-31
