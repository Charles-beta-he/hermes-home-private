# final_landed evidence gate multimodel result — 2026-05-27

## User request

多模型分析：按最终方案修复。

## Question

Hermes taskpool manual-review reopened tasks were falsely auto-closed again as `done` using weak evidence such as `py_compile_taskpool PASS`, proof hashes, and PASS_ADVISORY_ONLY/advisory artifacts. Should the final_landed gate remain token substring based, or be changed to a structured bundle gate?

## Model results

### consult_models T1

Command attempted:

`python3 ~/.hermes/scripts/consult_models.py run /Users/charles/.hermes/docs/private/final-landed-gate-multimodel-state-20260527.json --tier T1 --quorum 4 --discussion --max-rounds 2 --keep --timeout 180`

Result: degraded quorum. DeepSeek returned a valid plan; Claude/gpt/mimo timed out or failed in this run.

DeepSeek verdict:

- root cause class: verifier_gap
- recommendation: replace broad token matching with structured bundle requirement
- required tests: reject weak incidental token only; require implementation artifact + verification evidence
- enforcement location: `lifecycle_gate -> completion_gate_failures`, so manual transition and auto-close-review share the same fail-closed gate

### Direct model cross-checks

DeepSeek direct: approve.

Key recommendation:

- token substring matching is a category error for a semantic final-llanding gate
- introduce an explicit landing bundle, not emergent text scanning
- add weak/advisory/manual-review exclusions as defense-in-depth
- version/fail-close the bundle semantics

GPT route with OpenAI primary fallback to Gemini: approve.

Key recommendation:

- define a strict schema requiring `implementation_artifacts` and `verification_evidence`
- remove token substring matching from the control plane
- reject invalid or incomplete bundles before state transition

## Final implementation decision

Use a structured final-landed bundle predicate:

1. Only tasks with `manual_review_final_landed: false` and approval action outside `{approve_close_as_partial, approve_watch}` are gated.
2. To enter `done`, evidence must contain both:
   - implementation artifact evidence: commit / code / script / skill / config / implementation artifact
   - feature-specific verification evidence: pytest/vitest/npm test/benchmark/read-back/browser/playwright/curl/real-api/regression/test pass
3. Weak evidence is ignored for this gate:
   - `py_compile_taskpool`
   - `PASS_ADVISORY_ONLY`
   - `ExperienceAtom`
   - `discussion_result.json`
   - manual-review report references
   - raw proof hashes
4. Enforcement remains in `completion_gate_failures(...)`, called by `lifecycle_gate(...)`, so `transition ... --to done` and `auto-close-review` both share the same rule.
5. Partial/watch manual-review outcomes remain closeable as non-final outcomes.

## Implemented files

- `/Users/charles/.hermes/scripts/brain_task_orchestrator.py`
- `/Users/charles/.hermes/scripts/test_brain_task_orchestrator.py`

## Verification

RED:

- Added tests initially failed because `command:selfcheck PASS + command:pytest PASS` and `command:selfcheck PASS + command:git commit abc123` were accepted by the old token-only predicate.

GREEN:

- `python3 -m pytest /Users/charles/.hermes/scripts/test_brain_task_orchestrator.py -q -k 'manual_review_final_landed or manual_review_reopen' -o addopts=`
- result: `5 passed, 50 deselected`

Control-plane verification:

- `python3 ~/.hermes/scripts/brain_task_orchestrator.py selfcheck --json`: PASS
- `python3 ~/.hermes/scripts/brain_task_orchestrator.py proof-check --json`: PASS
- `python3 -m py_compile /Users/charles/.hermes/scripts/brain_task_orchestrator.py /Users/charles/.hermes/scripts/test_brain_task_orchestrator.py`: PASS

Broader suite note:

- Full `test_brain_task_orchestrator.py` currently has unrelated/pre-existing failures around mission envelope/event-hook side effects and a monkeypatched subprocess boundary test. The targeted final_landed regression slice passes.

Post-update check note:

- `post-update-check.py --fix` reports most guards OK; known remaining attention: `skill_quality` missing tests and `hook_registry_selfcheck` broken by `/Users/charles/.hermes/hermes-agent/python3` shell-hook path. Not introduced by this final_landed patch.

## Post-fix taskpool state

After committing the gate:

- final_landed gate task was closed with scoped commit/test/selfcheck/proof evidence.
- T02 continuation/resume was released `blocked -> pending` because the false-close guard is now active.
- T04 continuous verification/pre-merge was released `blocked -> pending` for the same reason.
- T17 was in `review`; a targeted `auto-close-review --task T17` returned `closed_count=0` and skipped it with the expected failure:
  `manual_review_final_landed=false requires final landed evidence bundle ...`

Final taskpool checks after these transitions:

- `selfcheck`: PASS
- `proof-check`: PASS
