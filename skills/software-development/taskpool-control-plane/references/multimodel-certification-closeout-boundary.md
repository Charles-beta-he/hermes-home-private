# Multimodel certification closeout boundary

Use when a taskpool task has `requires_multimodel: true`, `multimodel_certification_authority: true`, or a closeout gate such as `project-evidence-review-done` that requires certification.

## Procedure

1. Do not treat tests/selfcheck/commit evidence as sufficient for `done` until the certification gate is satisfied or an explicit policy override is granted.
2. Run the real certification path, enabling the runner's explicit env gate when required, for example:
   ```bash
   HERMES_LOCAL_BRAIN_AUTORUN_MULTIMODEL=1 \
   python3 ~/.hermes/scripts/brain_task_orchestrator.py multimodel-intervention-step \
     --task '<task-id>' --json
   ```
3. Inspect the gate artifact and classify failures:
   - implementation/evidence issue: missing final design, next slice, acceptance evidence, rollback boundary, requested read-only evidence;
   - consensus issue: agreement below threshold, unresolved severity blocker, missing best-within-constraints signature;
   - authority/setup issue: provider credential failure or external certification dependency unavailable.
4. Continue safe local work only for implementation/evidence issues. Add the requested evidence or final-design fields, rerun tests/selfcheck, and rerun certification.
5. If the remaining blocker is authority/setup outside the implementation scope, stop at a human intervention packet rather than forcing `done`.

## Human intervention packet

Include:

- task id and current lifecycle status;
- certification artifact path;
- exact gate failures;
- completed deterministic evidence (tests, selfcheck, commits, docs);
- requested smallest action: fix provider credentials / rerun certification / explicitly authorize deterministic-evidence closeout override;
- safety note: no taskpool lifecycle mutation or external side effect should be forced past the gate.

## Anti-conditions

- Do not save transient provider credential failures as a durable claim that a model/tool is broken.
- Do not use `--force done` to bypass `multimodel_certification_required_before_done` unless the user explicitly authorizes that policy override.
- Do not reframe sequential backlog items as human-choice implementation forks; only stop for same-implementation mutual exclusion, permission, safety, credential, or certification gates.
