# External source intake and smart-router review

## When to use

Use when a report, feed, Product Hunt list, GitHub Trending list, or similar external-source digest should create governed follow-up tasks, or when a scheduled self-evolution/dreaming job is green but not producing useful progress.

## Intake principle

Do not restrict absorption to architecture-level findings. Source items can become tasks through several lenses:

- architecture/control-plane pattern;
- developer workflow or tool capability;
- browser automation/runtime/observability capability;
- product/competitor/commercial signal;
- evidence-retrieval follow-up when a source or GitHub link is present but metadata is unresolved.

For each high-signal item choose explicitly: P1/P2/P3 candidate, evidence-retrieval candidate, observation with reason, or discard with reason. Empty sidecars are suspicious when the report itself names concrete Hermes-adjacent repos/products.

## Dreaming / autonomous-evolution status split

For no-agent dreaming or self-evolution jobs, report three statuses separately:

1. Runtime health: cron fired, script exited 0, ledger wrote, no degraded/write_blocked.
2. Evolution effectiveness: state_advanced, distinct targets, useful score/test movement, absence of repeated no_state_change.
3. Routing/certification readiness: model quorum, skipped providers, truth-gate quality, advisory vs certified result.

A job can be runtime-green but effectiveness-red if it repeatedly audits the same target with `state_advanced=false`.

## Smart-router review pattern

- Inspect provider/router readiness first.
- Use T1 for local control-plane selector/cooldown/verifier issues; reserve T2/T3 for broad routing/certification or lifecycle authority changes.
- Build claim-linked evidence before multi-model review: cron output, ledger tail, router probe, relevant script snippet.
- Treat `fanout_quorum_met` as planner availability only. `truth_not_certified` or `not_certified` remains advisory and cannot close lifecycle.
- Missing optional provider auth, such as Gemini missing auth, is readiness debt rather than a blocker for T1 when quorum-capable models are available.

## Minimal reversible repeated-no-change fix

1. Record `last_audit_attempt`, `consecutive_no_change`, `cooldown_until`, or `blocked_reason` when score is unchanged.
2. Demote targets after bounded consecutive no-change and rotate to other active candidates.
3. Add focused tests for target rotation, improvement path, regression rollback, and archived/read-only protection.
4. Verify with preflight, controlled dry-run/selector probe, ledger readback, and taskpool proof.
