# Taskpool done-gate closeout heuristics

Applicability: use when `auto-close-review` stalls with review tasks that appear evidence-complete, especially advisory/review-gap tasks blocked by `execution_flow_closeout_blocked:*` failures.

Anti-conditions: do not use this to weaken proof gates for true implementation/work-lane tasks. Work tasks that actually touch UI/API/backend still need deterministic test/build/browser/curl/readback/commit evidence as required by their completion gate.

## Pitfall: substring false positives in execution-flow hints

A broad closeout heuristic can accidentally classify advisory evidence tasks as implementation/UI/API tasks when it matches English substrings inside unrelated words or frontmatter fields. Examples observed:

- `FixtureKit` matched `fix`, so advisory Product Hunt evidence was treated as an implementation fix.
- `capability` matched `API`, so source-analysis tasks were treated as API/backend work.
- Generic frontmatter such as `required_authority`, `guidance`, or `workflow_contract` can trigger `UI`/`contract` hints even though the task is not a UI/API delivery.

Symptom pattern:

1. `brain_task_orchestrator.py auto-close-review --json` returns `closed_count: 0` and many skipped review tasks.
2. Skips show failures like `execution_flow_closeout_blocked:browser_or_ui_surface_proof` or `api_or_backend_readback_proof` for advisory/review-gap tasks that only need evidence/ratification closeout.
3. `selfcheck` may still be PASS; this is not a global health failure.

## Diagnostic checklist

Run a read-only comparison before changing gates:

1. List review skips:
   `python3 ~/.hermes/scripts/brain_task_orchestrator.py auto-close-review --max-tasks 100 --authority autonomous-execution --json`
2. For skipped review tasks, inspect whether `lane=advisory` or the task is a review-gap repair child.
3. Compare the closeout hint matches against title/body/frontmatter. If the match is a substring inside an unrelated word (`FixtureKit`, `capability`, etc.), treat it as a heuristic bug, not missing proof.
4. After any patch, re-run `py_compile`, `selfcheck`, and `auto-close-review`. A valid fix should allow previously evidence-complete advisory tasks to close while true work-lane tasks remain gated.

## Durable fix pattern

For English hint regexes used by closeout classification, use word boundaries for token-like keywords:

- Good: `\b(?:implement|fix|ui|browser|frontend|backend|api|route|tab|modal|build|test)\b`
- Good: keep Chinese keywords as direct alternatives, e.g. `修复|实现|落地|接口|页面|按钮|验证`
- Avoid: bare `(fix|UI|API|contract)` across serialized task/frontmatter blobs.

Verification evidence from the originating incident: tightening the regex changed advisory false positives from `needs_ui=true/needs_api=true` to no closeout failure and immediately allowed two review tasks to close to done, while remaining work-lane tasks stayed blocked on real proof requirements.
