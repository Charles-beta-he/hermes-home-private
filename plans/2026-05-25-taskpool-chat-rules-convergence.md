# Taskpool / Chat Rules Convergence Plan

Goal: eliminate unsafe dual-source drift between normal chat rules and taskpool execution workers while preserving intentional isolation for independent model review.
Status: done
Created: 2026-05-25

## Steps
- [x] Step 1: Baseline repo state and fetch remote without overwriting dirty work — fetched all remotes; branch private/main is ahead 3, no remote pull needed; existing unrelated dirty work preserved.
- [x] Step 2: Run real multi-model review for the proposed architecture and capture boundary conditions — MiMo/DeepSeek/Gemini/GPT reviewed; synthesis saved to /Users/charles/.hermes/docs/private/taskpool-chat-rules-convergence-multimodel-20260525.md.
- [x] Step 3: Add RED tests proving execution workers launched with --ignore-rules still receive a canonical rules digest, while review/smoke calls remain isolated — RED failed on missing build_execution_rules_digest, GREEN passed with 2 targeted tests.
- [x] Step 4: Implement a small canonical digest builder and inject it into taskpool execution worker prompts/handoffs without broadening multimodel review prompts — implemented in /Users/charles/.hermes/scripts/agent_team_controller.py only; consult/smoke paths untouched.
- [x] Step 5: Run targeted tests, py_compile/selfcheck/post-update-check where safe, inspect git diff, and create a scoped Hermes commit — py_compile PASS; targeted pytest 2 passed; taskpool selfcheck PASS; scoped commit 6affc08 created/amended. post-update-check not run because this pass did not update vendor and ~/.hermes has broad unrelated staged/runtime churn.

## Decisions
- Keep --ignore-rules available for independent review/smoke/model-consult paths.
- Do not rely on full memory injection for taskpool workers; inject a compact digest instead.

## Files Changed
(none yet)
