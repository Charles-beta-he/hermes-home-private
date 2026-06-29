# taskpool orchestrator test hermetic routing

Applicability: `test_brain_task_orchestrator.py` or other Hermes taskpool unit tests fail only on a developer machine with live local brain/model/router/health config. Symptoms include ratification gate expecting different required models, autorun handoff failing on `dispatch_hint_precondition` / `p10_health`, or fake Task objects missing production-only attributes.

Root cause pattern: tests import or subprocess-run `brain_task_orchestrator.py`, which reads live `~/.hermes/config/quorum.yaml`, `p10-health.sh`, project profiles, or real health/model-router state at import/runtime. This creates machine-dependent failures that are not product regressions.

Smart-route fix pattern:
1. Classify the failure domain first: ratification model policy, autonomy write guard, blocked-resolve flow semantics, or parallel boundary refinement.
2. Keep production routing strict; make tests hermetic by passing explicit env fixtures.
3. For quorum: set `HERMES_QUORUM_CONFIG` to a temp/missing file for default-policy tests, and only set a real custom file in tests that explicitly verify quorum config loading.
4. For autonomy precondition: prefer a narrow fixture env such as `HERMES_AUTONOMY_PRECONDITION_P10_FIXTURE` that supplies a local JSON health result; do not let unit tests depend on current machine p10 grade.
5. For fake task objects in parallel dispatch tests: production helpers should tolerate missing optional attributes via `getattr(task, "project", "")` / `getattr(task, "title", "")` when they may receive lightweight fakes.
6. For blocked-resolve tests: assert the current route semantics explicitly. If local failure taxonomy can be derived from frontmatter, the smart route may auto-split/reopen instead of freezing on a missing historical artifact.
7. Verify targeted tests first, then full `python3 -m pytest ~/.hermes/scripts/test_brain_task_orchestrator.py -q`, then live `proof-check`, `selfcheck`, and `taskpool_watch_report.py --json`.
