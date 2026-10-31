# Tasks

- [x] `ui/src/api.js`: `listSources()`, `runSource(id)` against `VITE_API_BASE_URL`/`VITE_SCHEDULER_BASE_URL`
- [x] `ui/src/components/NavRail.jsx`: clickable items, `onNavigate` callback
- [x] `ui/src/components/SourcesScreen.jsx`: loading/empty/error/success states, Run action
- [x] `ui/src/components/RunView.jsx`: shows run id, source id, status
- [x] `ui/src/App.jsx`: view-state switch (sources / run), wires nav + screens together
- [x] Tests: `ui/test/SourcesScreen.test.jsx`, `ui/test/RunView.test.jsx`, `ui/test/App.navigation.test.jsx`
- [x] `api/app/main.py` + `scheduler/app/main.py`: permissive CORS so the UI origin can call both services locally
- [x] Spec delta `specs/ui.md`
- [x] `verification.md` with evidence per scenario and AC
- [x] Run `contract-check` and `secret-scan`
- [x] Run `scripts/spec_check.py` (plan and verify stages)
