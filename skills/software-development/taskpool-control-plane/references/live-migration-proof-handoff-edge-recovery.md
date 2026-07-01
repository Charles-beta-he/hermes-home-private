# Live taskpool migration: proof, handoff, and edge recovery

Use this reference when continuing taskpool governance cleanup after selfcheck/proof-check show historical debt but the active taskpool is otherwise healthy.

## Landing-zone classifier

- Reusable procedure / pitfall: keep here in `taskpool-control-plane`.
- Project-specific run state, IDs, task names, backup paths: keep in evidence/project notes, not global memory.
- Concrete remaining work: create/keep taskpool candidates, not fake skills.

## Safe sequence for live migration

1. Capture baseline before mutation:
   - `python3 ~/.hermes/scripts/v_state.py --json`
   - `python3 ~/.hermes/scripts/brain_task_orchestrator.py selfcheck --json`
   - `python3 ~/.hermes/scripts/brain_task_orchestrator.py proof-check --json`
2. Make a reversible backup of affected runtime surfaces before applying cleanup:
   - continuation state
   - handoff dirs
   - kanban DB/workspaces
   - brain task notes
   - proof/selfcheck/v_state snapshots
3. Prefer read-only/dry-run tooling first, then apply only bounded actions.
4. After each apply, re-run selfcheck/proof-check/v_state and record an evidence report.

## Handoff backlog cleanup pattern

When selfcheck warns `autorun handoff directory has N handoffs`, the threshold is based on `~/.hermes/state/auto_run_handoffs/*.md`, not parallel handoffs.

Safe cleanup:

- Archive oldest `*.md` files under `auto_run_handoffs/archived/<timestamp>/`.
- Keep newest handoffs in the source dir; do not delete.
- Write a manifest with sha256/path/mtime/size for moved files.
- Verify selfcheck warning clears.

Anti-condition: do not archive `parallel_handoffs` just because it appears in a general report unless a gate explicitly complains about it.

## Proof debt migration pitfalls

`brain_task_orchestrator.py` uses a lightweight task frontmatter parser. Full PyYAML dump can convert inline lists to block lists and make fields like `evidence` invisible to proof-check. Avoid full frontmatter rewrites during historical debt migration.

Safe migration:

- Use line-preserving replacement for existing refs only.
- Convert bare paths/URLs already present in `evidence_refs`, `handoff_artifacts`, `proof_artifacts`, or `ratification_artifact` into structured refs.
- Do not fabricate missing ratification artifacts.
- Do not delete invalid proof hashes just to silence warnings.

## Autorun proof hash recovery

`proof:sha256:<hash>` for autorun closure is valid only if `<hash>` is an `event_hash` present in the append-only `~/.hermes/state/auto_run_proof.jsonl` and the proof chain verifies.

Safe recovery:

1. Run `proof-check --json` and parse invalid hash warnings.
2. Load `auto_run_proof.jsonl` and verify the chain.
3. For each invalid hash, search for exact same-task events in the proof log.
4. Replace only with an exact same-task valid `event_hash`.
5. If no exact same-task event exists, stop and emit a DecisionPacket; do not use arbitrary artifact sha or model agreement as proof.

## Edge node warnings

For a local read-only smoke edge node, clear warnings by making policy explicit rather than hiding the warning:

- `worker.standalone_mode: true` if no `brain_url` is expected.
- `security.lease_policy: <named policy>` when dangerous capabilities like `run_command` are present.
- A successful live `/health` probe can supersede a stale registry heartbeat timestamp; selfcheck should not warn stale heartbeat when the node probes healthy.

Anti-condition: do not enable broad remote dispatch just to clear warnings. Keep dispatch eligibility gated by token, allowlist, policy, health, and explicit dispatch config.

## Verification checklist

- Focused tests for changed scripts pass.
- `brain_task_orchestrator.py selfcheck --json`: PASS; warnings are understood or empty.
- `brain_task_orchestrator.py proof-check --json`: PASS; no failures.
- `v_state.py --json`: components/bottleneck reflect real remaining debt.
- Evidence report records backup path, exact apply counts, remaining DecisionPacket items, and rollback path.
