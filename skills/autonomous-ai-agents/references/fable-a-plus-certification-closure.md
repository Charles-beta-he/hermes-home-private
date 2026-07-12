# Fable 5 A+ Certification Closure Pattern

Use when the user asks to use Claude Code Fable 5 to certify a Hermes/system repair, push an audit score to A+, or run a final multi-dimensional self-check after remediation.

## Core pattern

1. Define the A+ bar explicitly before invoking Fable:
   - A+ means prior P0/P1 blockers are closed with current, falsifiable local evidence.
   - A+ does **not** mean the system is risk-free, all historical debt is gone, or external/live surfaces were exercised.
   - Safety boundaries such as “no push/deploy/external send/hardware/credential action” are not defects.
2. Build a compact evidence packet from real command output and readbacks:
   - portfolio/registry doctor output and counts;
   - taskpool/selfcheck/proof-check status, failures, warnings;
   - cron/job rerun receipts or deterministic script receipts;
   - coverage registry dimensions/freshness policy;
   - route/cost/UI freshness readbacks;
   - git scoped status and commit requirement.
3. Ask Fable for structured JSON:
   - `grade`, `a_plus_achieved`, `p0_blockers`, `p1_blockers`, `p2_followups`, `evidence_assessment`, `commit_requirement`, `remaining_cannot_claim`.
4. Use Claude Code print mode with Fable and bounded turns:
   - If `--max-turns 1` or `3` returns `error_max_turns` but `modelUsage` contains `claude-fable-5`, retry with a higher turn cap.
   - For read-only audit/certification, use `--tools ""` to prevent Claude Code from trying to inspect or edit files and to force the assessment to stay on the provided evidence packet.
5. If Fable says A+ is conditional on landing state, make a scoped local commit after verification, then re-run the critical local checks.
6. Report both the achieved grade and the “cannot claim” list. Do not collapse P2/P3 follow-ups into blockers, but do not hide them.

## Verification checklist

- [ ] `modelUsage` includes `claude-fable-5`.
- [ ] Fable result has `grade: A+` and `a_plus_achieved: true` before claiming A+.
- [ ] P0/P1 arrays are empty.
- [ ] The final landing step required by Fable, usually a scoped commit, was completed or explicitly left as a blocker.
- [ ] Post-commit checks were re-run for the surfaces touched.
- [ ] Final report distinguishes A+ certification from system-wide risk elimination.

## Pitfalls

- Do not treat `error_max_turns` as model failure if `modelUsage` proves Fable ran; it may simply need more turns or no tools.
- Do not let Fable browse or mutate when the task is certification over a prepared evidence packet; use no-tool mode for the final read-only verdict.
- Do not save session-specific grades or commit SHAs as durable memory. Save the procedure here; keep exact receipts in project evidence.
- Do not treat historical proof/hash debt as current P0 unless the live check has `failures` or blocks the declared success criteria.
