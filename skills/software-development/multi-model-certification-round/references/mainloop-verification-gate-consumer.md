# Mainloop verification gate consumer pattern

Applicability: Hermes or similar agent main-loop work where a final response may claim `done`, `verified`, `certified`, production readiness, UI acceptance, or a high-risk T3 control-plane outcome.

Anti-conditions:
- Do not treat this as a mandate to run all user turns through synchronous multi-model fanout.
- Do not claim background certification workers, external side effects, or production acceptance are complete unless their own runtime/readback evidence exists.
- Do not count the producer/implementer model as an independent verifier.

## Pattern

1. Land a contract-level gate before opening broader runtime authority.
   - Add a gate that classifies completion-critical claims and verification surfaces.
   - T3 or completion claims should be evaluated before final turn finalization.
   - Low-risk ordinary chat should skip the gate or stay advisory so normal latency is preserved.

2. Separate these statuses in the implementation and report:
   - route/advisory classification;
   - objective evidence availability;
   - independent verifier vote;
   - final acceptance status;
   - background certification job status, if any.

3. Enforce independent verification for completion-critical claims.
   - Objective evidence alone may prove a tool action happened, but project-level certification needs an independent verifier vote when the configured policy requires it.
   - Implementer self-report can be retained as context, but must not count toward certification quorum.

4. Consume current-turn evidence, not model memory.
   - Extract evidence from tool messages, test output, config readback, git readback, screenshots, browser/console logs, API readback, or other non-model sources.
   - If a final response claims completion without enough evidence/votes, append a gate notice or downgrade the claim before finalization.

5. Keep the first consumer bounded.
   - The first runtime slice may only degrade/block final-response claims and store metadata (for example `_last_mainloop_verification_gate`).
   - Defer automatic background certification dispatch, MCP writes, external side effects, rollback/reopen, and production writes to later governed slices.

## Evidence bundle pitfall discovered

When using `consult_models.py state --evidence-json`, pass each evidence item as its own `--evidence-json` payload containing an `id` and explicit `supports`/`contradicts` links. Do not wrap the evidence list inside an ad-hoc nested object like `{claims: [...], evidence: [...]}` as a single evidence item: the truth builder may treat it as one unlinked evidence record, leaving `supporting_evidence_ids=[]`, `evidence_coverage=0.0`, and high-severity claims at `needs_link_review`.

Correct shape per evidence item:

```json
{
  "id": "E-pytest",
  "source": "terminal",
  "command": "./venv/bin/python -m pytest -q tests/agent/test_conductor_runtime.py",
  "exit_code": 0,
  "status": "pass",
  "content_excerpt": "15 passed",
  "supports": ["C-gate"]
}
```

Then rerun the certification state build with repeated `--evidence-json <item-json>` arguments. A healthy truth gate should show:

- `truth_assessment.can_certify_truth=true`
- `evidence_bundle.evidence_coverage=1.0`
- `grounding.<claim>.supporting_evidence_ids` populated
- `unsupported_high_severity_claim_ids=[]`

## Minimal verification bundle

For a main-loop gate consumer slice, use at least:

- commit/diff readback for the files touched;
- focused tests proving: model-only rejection, self-cert rejection, missing independent verifier rejection, certified path, low-risk skip, and final-response notice/blocking;
- syntax check/compile for modified runtime files;
- configuration readback proving the gate is enabled and policy flags match intent;
- post-update or project health check proving adjacent conductor/multi-brain regressions are still OK;
- final acceptance-gate packet with objective evidence refs plus an independent verifier approve vote.
