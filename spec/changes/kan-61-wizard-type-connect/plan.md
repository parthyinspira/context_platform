# KAN-61: Add-source wizard: type and connect steps (lite)

Jira: https://inspiradataintegration.atlassian.net/browse/KAN-61   Branch: m8-ui-wizard-and-runs

## Scope
In: new `AddSourceWizard` screen (reachable from an "Add source" button on the Sources screen) using the existing `Stepper` component for steps 1 (type) and 2 (connect); type tiles per `docs/UI_DESIGN.md` 4.3 (Git enabled, SQL/Upload/SharePoint/Snowflake/Tableau shown as "Coming soon" and disabled); a credential form for the Git type (uri, optional branch, credentials ref/token); a "Test connection" button calling `POST /sources/test-connection` (KAN-58) with clear success/error states; secrets entered are masked in the input and never re-displayed after submit.
Out: steps 3-5 (discover/plan/run — KAN-62/63); multiple source types' credential forms beyond Git (tiles exist but are disabled); persisting the source (`POST /sources`, already built in B2) is reused as-is, called once Connect succeeds, to carry the wizard into KAN-62.

## Acceptance criteria (from Jira)
1. Type tiles.
2. Credential form per type.
3. Test connection with clear success/error.
4. Secrets masked and never shown again.

## Requirements (at most 5)
- The wizard's step 1 SHALL render one tile per source type from `docs/UI_DESIGN.md` 4.3 (Git, SQL, Upload, SharePoint, Snowflake, Tableau); only the Git tile SHALL be selectable, the rest SHALL render disabled with a "Coming soon" label. (scenario: Given the wizard opens at step 1, When it renders, Then six tiles are shown and only Git is enabled; Given Git is selected, When the user advances, Then step 2 (connect) is shown)
- The wizard's step 2 SHALL render a credential form for the selected type (for Git: repository URL, optional branch, a credentials-ref/token input rendered as a masked `type="password"` field) and a "Test connection" button that calls `POST /sources/test-connection`. (scenario: Given the form is filled in, When "Test connection" is activated and the API returns `ok: true`, Then a success indicator is shown; Given the API returns `ok: false, error`, Then an error indicator with that message is shown instead)
- After a submitted secret value is accepted (test succeeds, or the source is created), the form SHALL never re-display that value in plain text; re-opening or re-rendering the field SHALL show it masked or blank, not the original value. (scenario: Given a successful test connection, When the step re-renders (e.g. navigating back from step 3 and returning), Then the secret field shows masked/blank content, not the original value)
- The connect step SHALL show loading, success and error states for the "Test connection" action using the shared state-rendering primitives (`Skeleton`/`ErrorBanner`), consistent with the rest of the app. (scenario: Given "Test connection" is in flight, When rendered, Then a loading indicator is shown instead of a stale result)

## Tasks
- [ ] 1. `ui/src/api.js`: add `testConnection(payload)` calling `POST /sources/test-connection` (test: resolves/rejects per mock fetch)
- [ ] 2. `ui/src/components/AddSourceWizard.jsx` step 1 (type tiles) using `Stepper` (test: six tiles render, only Git enabled/selectable)
- [ ] 3. `AddSourceWizard` step 2 (connect form + Test connection) (tests: success state, error state; masked field never shows prior value on re-render)
- [ ] 4. "Add source" entry point button on `SourcesScreen.jsx` opening the wizard

## Risks / not verifiable here
- Only the Git credential form is implemented; other types' forms are explicitly "Coming soon" per scope, matching the AC's "credential form per type" as "the types that exist get a form, the rest are visibly disabled" (no hidden/broken forms).

## Approval
Approved by: parthasarathy.venkatachalam (user approved spec-batch), 2026-10-31
