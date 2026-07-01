# Core Gate

Extracted from `/Users/charles/.hermes/skills/software-development/objective-model-path-verification/SKILL.md` on 2026-07-01T08:55:33.664327+00:00 by generic core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

## Core Gate

### Full-landing semantics

Scope: complex implementation, workflow/control-plane, UI/API, or automation tasks where the user says “全盘推进”, “完整落地”, “推进至需人工介入”, or equivalent. Applicability: when the request is to build or repair the actual working system, not only advise. Anti-condition: do not use this wording to bypass permission, value-judgement, destructive, external-side-effect, credential, or evidence-insufficient gates.

For these requests, the default completion target is not a plan, draft, read-only projection, mock, visual-only button, copy-only change, local-only placeholder, or test stub. Start from the target model and carry the work through the real layers that define the intended effect: UI/interaction, API/contract, SSOT/ledger, adapter or executor boundary, persistence, read-back, tests, browser/runtime verification, and scoped commit. If a lower layer is intentionally the endpoint, label it explicitly (for example “record-only; adapter apply not opened”).

For “开箱即用 / 全自动化效果 / 企业生产级” specifically, do not stop at templates, reports, inventory, sanitizer, or an internal script when the user's target is a usable capability. The safe default is a productized path: install or doctor command, fail-closed validation, no-overwrite or explicit-merge policy, activation state/receipt, docs/help text, tests, and a real temp-environment smoke. Only stop before external side effects such as push/deploy/publish, credential entry, destructive cleanup, broad config mutation, or submodule-pointer publication whose target commit is not reachable.

If the work reaches a boundary requiring human choice or authority, do not silently downgrade to a weaker layer and call it done. Also do not stop with only “cannot continue.” For self-advancing/workflow-kernel work, the dry-run acceptance bundle is a real scheme boundary: it is safe to land contract/projection/acceptance artifacts, but local executor/runtime/taskpool write-through requires a fresh human gate.

Sequentially approved tracks are not a choice boundary. When the user says multiple tracks can proceed or explicitly approves “全盘推进直至需要人工介入”, continue the ordered backlog through each independently verifiable slice. Stop only for the smallest real gate: same-implementation mutual exclusion, permission/credential/safety/legal risk, destructive or external side effect, evidence insufficiency, or a governed certification gate that cannot currently pass. A stage report is not a gate: report progress only when useful, then keep advancing the next safe slice instead of pausing for acknowledgment. Do not convert “current status / next suggested slice” into an implicit human confirmation point; only stop when the next action would cross one of the real boundary classes above. If the user says the方案 should be treated as the final方案 and that landing should be performed step by step by the agent, stop presenting implementation options as if asking for product direction; choose the safest reversible default path, land contracts/tests/config/docs first, and reserve only true authority gates for the user. For taskpool tasks that require multimodel certification, deterministic implementation evidence is not enough to force `done`; run the certification path, inspect the gate artifact, and if the remaining blocker is provider credentials/authority or unresolved certification criteria, produce an intervention packet rather than treating it as an implementation fork.

Switch into boundary realignment:

1. Restate the initial objective and the full-landing target that is still in force.
2. Identify the exact boundary class: permission/authority, evidence insufficiency, destructive or external side effect, credential/secret, value judgment, or safety/legal risk.
3. Mark confirmed vs unconfirmed facts, including what evidence would remove the boundary.
4. Continue any safe read-only, local, reversible, dry-run, patch-preparation, rollback-design, or verification work that does not cross the boundary.
5. Produce a compact intervention packet for the blocked action: requested authorization or choice, blast radius, rollback/escape hatch, verification after execution, and the default safe next step.
6. Stop only at the smallest necessary confirmation point, preserving the original plan and dependency order.

For complex tasks, run these steps before substantive execution:

1. **Objective & cost function**
   - Define success in concrete terms.
   - List hard constraints/red lines.
   - State what to minimize: risk, regression, user steering, downtime, token cost, migration cost, data loss, etc.

2. **Situation model**
   - Identify key objects, actors, state stores, dependencies, invariants, and permissions.
   - Separate facts already evidenced from assumptions.
   - For project work, locate the canonical source of truth before editing.

3. **Candidate paths**
   - Generate at least two viable paths unless only one is technically possible.
   - Include the “do nothing / defer / ask human” path when authority or evidence is insufficient.

4. **Consequence prediction**
   - For each path, predict likely outcome, failure mode, blast radius, rollback path, and verification burden.
   - Prefer paths that preserve existing behavior, are reversible, and produce evidence quickly.

5. **Selection and execution plan**
   - Choose one path and say why it wins against the cost function.
   - Convert it into small verifiable steps.
   - If action has side effects beyond granted scope, stop and ask or record a taskpool candidate.

6. **Evidence verification**
   - Before claiming completion, attach real evidence: test output, diff, logs, HTTP responses, screenshots, readback, or source citations.
   - If verification is blocked, report the blocker and what was still completed.
   - For multi-repo work, check branch names and pre-existing dirty files before committing. If the active branch is unrelated to the task or unrelated local changes are present, stop at verified working-tree changes and report a scoped commit boundary instead of mixing them into a commit.
   - When a task name can refer to multiple repositories, apps, dashboards, or similarly named artifacts, verify the target artifact path before editing. If the user intends one artifact but wants you to borrow patterns or authority boundaries from another, treat the latter as a reference model, not as the edit target.
