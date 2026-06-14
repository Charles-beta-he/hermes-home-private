# Intake-only execution-flow closeout evidence

Scope: taskpool `review` items whose objective/body contains implementation-like keywords (API, browser, UI, backend, adapter, verify, etc.) but whose actual authorized scope is **intake / source-review / safety-boundary / documentation-only**. The execution-flow closeout gate may request `api_or_backend_readback_proof` or `browser_or_ui_surface_proof`; do not satisfy that by performing forbidden runtime/API/browser actions.

## Pattern

1. Re-read the task contract before adding evidence.
   - Check `anti_drift_check`, `red_lines`, `non_goals`, `workflow_contract`, and acceptance criteria.
   - If the task explicitly forbids external runtime, API calls, browser bypass, credentials, API keys, Composio/auth, or third-party execution, treat API/browser runtime proof as **not applicable by safety boundary**, not as missing work to perform.

2. Produce/locate deterministic readback evidence that proves the scope boundary.
   - Existing report/artifact confirming the decision is acceptable.
   - Existing child-task backfill / ratification artifact is acceptable when it proves narrowed axes are done.
   - Do not invent browser/API results; do not run third-party tooling just to appease the closeout gate.

3. Add structured evidence with recognized prefixes only.
   - Good examples:
     - `proof:api_readback_not_applicable_intake_only_no_external_<source>_calls_allowed`
     - `proof:browser_surface_not_applicable_no_ui_or_browser_runtime_for_<axis>`
     - `command:readback artifact:/abs/path/to/report.md confirms documentation/proof-link-only boundary`
     - `command:readback parent auto-subtask backfill shows <axes> children done and ratification artifact present`
   - Keep narrative in `## Proof Log`; keep YAML `evidence:` machine-readable.

4. Re-run gates in order.
   - `proof-check --json` must stay `PASS`.
   - `auto-close-review --max-tasks 50 --json` should close only through normal lifecycle gates.
   - `review-gap-scan --max-tasks 50 --json` should return `gap_count=0` if no other review gaps remain.

5. Reconcile and verify drain state.
   - If `next --json` reports reconcile required, run `reconcile --write --json` once.
   - Then verify `next --json`, `dashboard --json`, `selfcheck --json`, `proof-check --json`, and worker/job liveness as appropriate.

## Anti-patterns

- Do not run forbidden API/browser/third-party actions merely to satisfy keyword-triggered evidence requirements.
- Do not mark implementation tasks done with `not_applicable` evidence unless the task contract really is intake-only / documentation-only / safety-boundary-only.
- Do not weaken `execution_flow_closeout_failures`; prefer structured evidence that explains why the proof type is not applicable for this task class.

## Example outcomes

- UUMit patch-normalization narrowed child: API/browser runtime proof was not applicable because the axis only normalized documentation/proof links and forbade external A2A/MCP calls.
- CloakBrowser risk-boundary intake: browser/API runtime proof was not applicable because the task explicitly forbade third-party browser-bypass execution; closeout relied on child-axis backfill and ratification artifact readback instead.
