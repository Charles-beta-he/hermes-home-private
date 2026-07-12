# Profile-local quota-observability continuation

Scoped reference for taskpool / multi-model quota-observability closeout. Use this when a historical quota-observability child references provider quota evidence, a profile-specific runtime home, and stale/no-header model routes.

## Applicability

- A historical task or session says a quota-observability child is complete, but parent/T3 certification or budget handoff was blocked by stale, unknown, or unobservable model quota evidence.
- A model is reported as non-certifying because its route is no-header/unobservable, while a low-risk runtime smoke may still succeed.
- The original run used a profile-specific `HERMES_HOME`, so root quota state may disagree with the authoritative profile-local state.

## Anti-conditions

- Do not use root quota state as authority for a profile-scoped parent unless an explicit sync step was authorized and read back.
- Do not upgrade no-header runtime success into exact remaining-quota or budget-handoff precision.
- Do not pretend historical artifact hashes were re-read when files are missing; create a new continuation packet instead.
- Do not treat model agreement as evidence; keep claim/evidence links explicit.

## Procedure

1. Identify the authoritative runtime home from the historical task/session. Treat that profile-local state as authoritative for the parent unless a sync/readback step says otherwise.
2. Check whether the historical workspace artifacts still exist. If not, create a fresh continuation/readback packet in the same logical workspace and explicitly state that old artifacts were missing.
3. Run quota commands with enforced gate semantics. `confidence-gate --json` may print failures while exiting 0; use `--gate` when the exit code itself is evidence.
   ```bash
   HERMES_HOME=<profile-home> python3 ~/.hermes/scripts/model_quota.py status --json
   HERMES_HOME=<profile-home> python3 ~/.hermes/scripts/model_quota.py confidence-gate --json --gate
   ```
4. Refresh exact providers before judging staleness. For DeepSeek-style balance providers, run the balance probe first:
   ```bash
   HERMES_HOME=<profile-home> python3 ~/.hermes/scripts/model_quota.py probe --deepseek --json
   ```
5. For no-header providers, run real low-risk smokes to prove route availability while preserving the no-quota boundary:
   ```bash
   HERMES_HOME=<profile-home> python3 ~/.hermes/scripts/multi-model-smoke.py --model <model> --timeout 90 --repeat 1
   ```
6. Re-run the profile-local confidence gate after smokes/probes. A good profile-local closeout is `exit_code=0`, `failure_count=0`, with clear notes that no-header models remain unobservable/low-risk-routing-only rather than exact quota-certified.
7. Run deterministic regression tests under the Hermes repo venv if available; avoid using system Python when it lacks pytest:
   ```bash
   ~/.hermes/hermes-agent/venv/bin/python -m pytest \
     ~/.hermes/scripts/test_model_quota.py \
     ~/.hermes/scripts/test_model_router_quota.py \
     ~/.hermes/scripts/test_consult_models_integration.py -q
   ```
8. Write a compact continuation packet containing:
   - profile-local gate exit/pass/failure counts;
   - root comparison gate counts, explicitly marked comparison-only;
   - model snapshots for relevant models;
   - test command and output;
   - artifact paths and hashes;
   - boundary statement: runtime availability is not exact quota.
9. Patch the task note Proof Log / Final Handoff with the fresh packet path, commands, and residual boundary.

## Common pitfalls

- `confidence-gate --json` without `--gate` can be misleading as a shell-success signal.
- A no-header smoke response proves the route works for that prompt; it does not expose safe quota headers.
- Root and profile quota states can diverge. For a profile-scoped parent, the profile-local state is authoritative unless a sync step is explicitly authorized.
- Historical task notes may point to workspace artifacts that were cleaned up. Preserve the provenance but create fresh evidence instead of claiming old readback.
