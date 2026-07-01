# Old-task dev-closure shadow run

Applicability: use this when a taskpool/control-plane workflow must be tested on old or blocked work before it is allowed to take over normal development closure.

Scope boundary: class-level taskpool procedure. Keep concrete project paths, task IDs, screenshots, and one-run outputs in the project profile, project SSOT, task note, or a per-project evidence packet. This reference stores only the reusable method.

Anti-conditions: do not use this pattern to bypass lifecycle, multimodel, certification, permission, deployment, credential, or external-side-effect gates. Do not store task progress or one-run status as durable memory.

## Core pattern

```text
read old task
-> classify lane at feature/task level
-> run only local/reversible proof
-> generate evidence ledger + closure packet
-> append proof reference to task note if safe
-> stop at lifecycle/certification gate
```

The critical distinction:

- **Dev closure loop may take over local evidence refresh and closure-packet generation.**
- **It must not take over `review/blocked -> done` unless the canonical taskpool lifecycle and certification gate pass.**

## When to use

- User says variants of: “全盘推进”, “使用旧任务测试”, “推进直至接管开发闭环”.
- A workflow/router/review/evidence loop is being promoted from notes/skills into a real project.
- Existing taskpool tasks are blocked/review/retry because certification or proof gates are unresolved.
- You need to prove the workflow can operate on real task metadata without falsely closing the task.

## Objective-model gate

Before action, define:

- success: old task produces a verified closure packet and repeatable runner/checklist;
- hard constraints: no deploy, no external side effect, no secret/PII persistence, no forced done;
- cost function: maximize evidence quality and reversibility; minimize lifecycle mutation risk;
- candidate paths:
  - read-only audit only;
  - shadow evidence refresh and packet generation;
  - direct taskpool lifecycle mutation;
- chosen default: shadow evidence refresh, because it validates the workflow while preserving gates.

## Procedure

1. **Inspect taskpool state first**
   - Run canonical selfcheck/list/next/dashboard as appropriate.
   - Identify whether reconcile is required before dispatch.
   - Do not treat `dispatchable=0` or blocked/review state as a bug by itself.

2. **Choose an old task with real evidence surfaces**
   Prefer a task that has:
   - clear acceptance criteria;
   - local tests/build/browser/API evidence available;
   - existing proof requirements;
   - no required production or credential action for the local proof refresh.

3. **Classify the task lane**
   Use task metadata, not only intuition:
   - low: docs/single-file/direct local check;
   - medium: normal tests + review;
   - high: UI/API/security/privacy/release surface;
   - very high: multi-repo, deployment, auth, money, production, or control-plane mutation.

4. **Create project-scoped dev-closure artifacts**
   Recommended files under the project SSOT:
   - project AI profile — objective, red lines, authority, completion definition;
   - router — feature/task lane classifier;
   - review checklist — blocker/warning/suggestion checklist;
   - evidence ledger — command/browser/API proof;
   - lessons — project-scoped reusable lessons only;
   - closure packet — handoff artifact for the old task;
   - optional verifier and narrow dev-closure runner scripts.

5. **Run real local proof**
   Depending on surface:
   - code: tests/typecheck/build;
   - UI: browser readback and screenshot/visual confirmation;
   - backend/API: HTTP/API readback;
   - docs/config: parser/schema/doctor command.

6. **Write a closure packet, not a done claim**
   The closure packet should include:
   - task identifier/title;
   - router lane and reason;
   - commands run and actual outputs;
   - UI/API/readback evidence;
   - safety result;
   - explicit canonical-done boundary.

7. **Write back proof reference safely**
   If editing task notes is within scope, append only factual proof references and boundary text. Do not change status to `done` unless the governed lifecycle path authorizes it.

8. **Add a narrow runner only after one manual proof succeeds**
   Initial runner should be intentionally narrow:
   - accept known task class;
   - classify lane;
   - verify artifact presence;
   - optionally run local tests with explicit execute mode;
   - always report `lifecycle_mutation=false` unless explicitly implementing a certified close path.

## Verification checklist

- [ ] Taskpool selfcheck has no new failures.
- [ ] Proof-check has no new failures; legacy warnings are labeled separately.
- [ ] Project profile / SSOT JSON or docs parse successfully.
- [ ] Dev-closure artifact verifier passes.
- [ ] Runner dry-run reports no lifecycle mutation.
- [ ] Runner execute mode, if enabled, runs real local proof and passes.
- [ ] Browser/API readback exists for UI/API tasks.
- [ ] Closure packet says whether canonical `done` remains gated.
- [ ] Any task-note writeback is factual and scoped.

## Pitfalls

1. **Local proof vs lifecycle proof confusion**: local tests plus screenshot/API readback can prove local implementation, but not taskpool `done` when the task requires certification.
2. **Runner overgeneralization**: after one successful old-task pilot, keep the runner narrow. Generalize only after multiple task classes are proven.
3. **Unrelated doctor debt ambiguity**: a broader portfolio/profile doctor failure in an unrelated profile is not proof the dev-closure slice failed. Report it as external debt, not as this slice's result.
4. **Security-tool timeout/approval block**: if a final combined validation command is blocked by the environment, do not retry by another route. Use evidence already collected and state the boundary.

## Minimal runner result shape

```json
{
  "ok": true,
  "local_closure_state": "verified_packet_ready",
  "lifecycle_mutation": false,
  "external_side_effects": false,
  "canonical_done_boundary": "requires taskpool lifecycle/certification gate; not mutated by this runner"
}
```
