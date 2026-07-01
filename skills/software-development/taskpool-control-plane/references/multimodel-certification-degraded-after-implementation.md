# Multimodel certification degraded after implementation

Use when a taskpool implementation slice has deterministic proof (tests, commit, DB/API/UI readback) but the governed multimodel/certification hook returns `not_certified` or `degraded_not_certified`.

## Pattern

1. **Separate implementation proof from lifecycle certification.**
   - Deterministic evidence can prove the bounded code slice works.
   - It does **not** automatically authorize `done` when the task declares `requires_multimodel`, `truth_gate`, or expected participants.

2. **Do not fight hook-owned lifecycle state.**
   - A transition to `review` may trigger the multimodel event hook and reclaim the task into `running` under `claimed_by: hermes-multimodel`.
   - Treat that as governed ownership, not a failed code implementation.

3. **Record proof before certification retry.**
   - Add file paths, test commands, commit hashes, and readback artifacts to the task evidence / project ledger.
   - Keep the task in `review`/`running`/`blocked` as dictated by the gate; do not force `done` from chat.

4. **For consult_models evidence, prefer explicit evidence objects.**
   - Use `supports: ["C-001", "C-002"]` style claim links for evidence objects.
   - Avoid boolean `supports: true` because older/local evidence normalizers may treat `supports` as iterable and crash.
   - If a run still reports `unsupported factual claims`, inspect whether the evidence linker accepts the evidence `type`/shape before assuming the implementation proof is weak.

5. **If planner fanout/quorum is degraded, produce an intervention packet.**
   - Include deterministic proof, degraded certification reasons, exact tick dir/manifest, and the next safe slice.
   - Continue only local reversible work that does not require `done` lifecycle advancement.

## Safe closeout wording

Use wording like:

> Implementation slice landed and deterministic verification passed, but governed multimodel certification remains degraded/incomplete; task is not marked done. Next step is to repair/complete certification or proceed only with the next safe non-production slice.

## Anti-conditions

- Do not use this to bypass a genuine failed test, failed migration, failed DB readback, or unresolved severity>=3 model blocker.
- Do not record provider quota/auth/transient timeouts as durable facts; only record the certification handling pattern and evidence-shape pitfall.
