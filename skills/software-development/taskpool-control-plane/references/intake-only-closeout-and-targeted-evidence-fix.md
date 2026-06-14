# Intake-only closeout and targeted evidence fix

Scope/applicability: taskpool evolution/advisory items whose acceptance boundary explicitly forbids runtime/API/browser side effects, plus blocked parents where the user authorizes automatic targeted-evidence repair.

## Problem signatures

1. `review-gap-scan` / `auto-close-review` blocks an intake-only task with execution-flow gaps such as:
   - `execution_flow_closeout_blocked:api_or_backend_readback_proof`
   - `execution_flow_closeout_blocked:browser_or_ui_surface_proof`

   The task is not supposed to call a live API, open a browser runtime, install a package, or exercise a third-party service; its red lines are the evidence boundary.

2. A blocked parent has finished children and concrete deterministic evidence available, but `blocked-resolve-step` still reports `keep_blocked` due to stale or incomplete parent evidence.

3. A social/video lead is being added to the pool and the canonical repo's GitHub API returns `license.spdx_id=NOASSERTION` / `Other`; the social post may imply reuse, but license must be treated as unresolved until the repository `LICENSE` is reviewed.

## Safe closeout pattern for intake-only tasks

Do **not** fake browser/API proof. Instead, make the non-applicability explicit and structured:

- `proof:api_readback_not_applicable_intake_only_no_<service>_api_or_daemon_install_allowed`
- `proof:browser_surface_not_applicable_<reason>`
- `command:readback <artifact> confirms <intake-only boundary / children done / no external runtime>`

Then rerun:

```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py proof-check --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py auto-close-review --max-tasks 50 --json
```

Interpretation:
- If `auto-close-review` closes the item, the closeout is valid only for the intake/evidence task, not for a later implementation task.
- If the task title/objective promises implementation, adapter landing, browser behavior, API integration, or dashboard mutation, non-applicability proof is **not** enough; reopen or keep it blocked until feature-specific evidence exists.

## Targeted evidence repair pattern

When the user says to automatically fix targeted evidence if it exists:

1. Inspect the remaining blocker with `blocked-resolve-step --json`.
2. Run the deterministic probe or readback already named in `acceptance_evidence` / task body; keep within red lines.
   - Example class: a read-only public probe with no credentials, no writes, no token/spend consumption.
3. Attach structured evidence to the blocked parent:
   - `artifact:<probe-output>`
   - `proof:sha256:<artifact-hash>`
   - `command:<probe-command> PASS <boundary summary>`
   - `proof:targeted_evidence_fix_<axis>_<summary>`
4. Verify:
   - `proof-check --json`
   - `blocked-resolve-step --max-tasks 50 --json`
5. If the resolver still reports `keep_blocked` because multimodel certification is still not PASS / `loop_non_convergence`, try the explicit multimodel path only when authorized:

```bash
HERMES_LOCAL_BRAIN_AUTORUN_MULTIMODEL=1 \
  python3 ~/.hermes/scripts/brain_task_orchestrator.py multimodel-intervention-step --task '<parent-id>' --json
```

6. If the multimodel step returns `no_intervention_needed` and the resolver still keeps the parent blocked, stop. Report that deterministic evidence was attached but no further automatic repair path remains; the remaining choices are human review, a new explicit framing task, or archive/keep-blocked.

## Social/video intake additions

For WeChat 视频号 / social leads:

- Use browser DOM text extraction (`document.body.innerText`) when snapshots are sparse, and visual OCR for cover text / modal overlays.
- Persist a durable evidence note under `~/.hermes/docs/private/` before task creation.
- Map the project name from OCR/text to canonical repo/docs using live APIs/search; label uncertain mappings explicitly.
- If GitHub reports `license.spdx_id=NOASSERTION` or `license.name=Other`, add a red line: no code reuse or embedding before LICENSE review.
- Keep visualization/UI projects as projections unless a controlled mutation API with proof gates exists; never let a visual layer become taskpool/control-plane SSOT.

## Pitfalls

- Do not add `proof:browser...` or `proof:api...` as if a browser/API test actually ran when the real evidence is non-applicability. Include `not_applicable` in the proof string.
- Do not close an implementation task with intake-only evidence. The pattern is only for tasks whose non-goal/red-line says runtime execution is forbidden.
- Do not run third-party installs, package managers, browser bypasses, Composio/API authorizations, or public publishing during intake.
- Do not repeat multimodel loops indefinitely after `no_intervention_needed`; that is a governed stop condition, not a prompt to force status changes.
