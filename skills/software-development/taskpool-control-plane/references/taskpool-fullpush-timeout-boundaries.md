# Taskpool full-push timeout and boundary handling

Use this when the user asks to “并行全盘推进”, “全盘推进”, or otherwise wants the local taskpool advanced through the governed runner rather than only inspected.

## Reusable lesson

A full-push session can safely mutate task state through governed commands such as blocked-resolution and parallel claim/handoff, but worker execution may exceed a foreground tool timeout. Do not let a long-running foreground `agent_team_controller.py cycle` become the point where the whole workflow loses control.

## Recommended sequence

1. Establish the objective/authority boundary first: full landing means real task lifecycle movement and evidence, but still no bypass of proof, certification, project-profile, credential, destructive, or external-side-effect gates.
2. Re-read dispatch state before mutation:
   - `brain_task_dispatch_tick.py --summary --print-always --no-state`
   - `brain_task_orchestrator.py parallel-dispatch-dry-run --max-agents N --json`
3. If blocked tasks are retryable, use the governed resolver and then immediately re-run dispatch dry-run to confirm what became dispatchable.
4. Use `parallel-claim-and-handoff --write` only after the dry-run shows selected tasks and boundary PASS.
5. For actual worker execution, prefer a tracked background process with completion notification, or a narrower bounded subcommand, instead of a long foreground `agent_team_controller.py cycle` with a hard timeout. If a foreground cycle times out and the tool layer raises a consent/blocking warning, stop at that exact boundary and ask for resume authority; do not retry an equivalent command or route around it.
6. After execution or timeout, read back lifecycle state, runner state, proof log, and dispatch summary before claiming progress.

## Pitfalls

- `selected_count < max_agents` can be a policy result, not a resource bug. Retry lane caps such as `escape_quarantine: 1` and `retry_general: 0` intentionally throttle repeated failures.
- `review-gap-scan --write` can be blocked by project-profile policy requirements (for example missing source weighting or evidence policy). Treat that as a profile/authority gate; do not fabricate repair tasks or bypass the profile.
- Handoff creation is not execution. Report the handoff path and proof hash, but continue to worker execution or explicitly label the worker boundary.
- Generic `agent_team_controller.py consume-claimed --max-agents N` may return `SKIP no claimed tasks` even after a fresh `parallel-claim-and-handoff --write` if the event-driven handoff expects the explicit claimed JSON payload. If a claimed task remains in canonical `list --json`, reconstruct the minimal `--claimed-json` from the claim readback/handoff (`task_id`, `run_id`, `claim_expires_at`, `handoff`, `proof_hash`, `boundary_key`) and start a tracked background `consume-claimed --claimed-json ...`; then verify the task transitions from `claimed` to `running`.
- A worker process can run silently for minutes before emitting output. Do not assume failure from empty stdout; poll process state and canonical task state. If the task is `running` and `stale_claim=false`, let it continue unless a real timeout/expiry gate fires.
- `auto-close-review` closing zero tasks is not a failure when it reports missing API/UI/command proof or certification `allowlist_miss`; it is the correct fail-closed outcome. Use `review-gap-scan --write` to create bounded repair tasks, then rerun auto-close only after evidence is attached.
- A tool-timeout safety block is a real interaction boundary. The next safe output is an intervention packet: what ran, what is claimed/running, blast radius, and the smallest requested authority to read/recover state.

## Governed advancement sequence

When the user grants authority to advance the pool, prefer this bounded progression before attempting broad worker cycles:

1. Re-read state with `list --json`, `selfcheck --json`, and `brain_task_dispatch_tick.py --summary --print-always --no-state`.
2. Run `blocked-resolve-step --authority dry-run --json`; if it only resolves transient blocked tasks and does not cross external/destructive gates, rerun with the granted authority.
3. Run `review-gap-scan --authority dry-run --json`; if gaps are repairable, use `--write` to create bounded repair children instead of forcing parent `done`.
4. Run `auto-close-review --authority dry-run --json`; only run with write authority when it reports closeable items. Treat skipped items as evidence gaps, not as closeout failures.
5. Run `parallel-dispatch-dry-run --max-agents N --json`; only then use `parallel-claim-and-handoff --write` for selected tasks.
6. Start worker consumption as a tracked background process. If generic consume skips while claimed tasks remain, use explicit `--claimed-json` from the handoff readback.
7. Read back counts, running/review/blocked IDs, stale-claim status, and dispatch summary before reporting progress.

## Verification checklist

- [ ] Boundary PASS and kill-switch/human_escape state checked.
- [ ] Dispatch dry-run evidence recorded before write.
- [ ] Claim/handoff write returns `claimed_count`, handoff path, and proof hash.
- [ ] Worker consumption was started and read back from canonical task state (`claimed` -> `running`, or explicit skip reason).
- [ ] Review-gap repair tasks created only through `review-gap-scan --write`, not by hand-written fake closure.
- [ ] Auto-close skipped/closed outcomes were reported separately from worker execution progress.
- [ ] Execution was tracked without losing control to a foreground timeout, or timeout boundary was explicitly reported.
- [ ] Final state was read back from canonical taskpool commands.
