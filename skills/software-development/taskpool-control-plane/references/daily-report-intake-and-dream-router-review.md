# Daily report intake + dreaming-system router review

## Applicability

Use this reference when:

- A daily report combines GitHub Trending, Product Hunt, AI/news feeds, or other external source lists with governed taskpool intake.
- The user challenges why source items were summarized but not analyzed for task creation.
- A scheduled self-evolution / dreaming / autonomous-evolution job reports `OK` but repeatedly produces `no_state_change`.
- A control-plane issue needs multi-model analysis and smart-router review before implementation.

Anti-conditions:

- Do not turn ordinary news into tasks without a capability, workflow, product, commercial, or evidence-retrieval angle.
- Do not treat advisory multi-model output as lifecycle completion proof.
- Do not let missing optional providers such as Gemini block a T1 review when quorum-capable models are available.
- Do not store one-off task progress here; keep concrete run artifacts in taskpool proof logs or project/session review notes.

## Landing-zone classifier for this class

Split mixed conclusions before writing anything durable:

- Stable preference: daily GitHub/PH/source lists should be actively triaged for absorbable tasks, not only architecture items → user profile/memory plus this taskpool intake rule.
- Reusable procedure/pitfall: source-list triage, no-change selector cooldown, advisory-vs-certified routing boundaries → this skill/reference.
- Concrete task/session result: generated task files, run IDs, timestamps, proof logs → taskpool/task notes, not skill body.
- Provider setup debt: missing OAuth/auth for optional models → provider/setup task if needed, not a global claim that the model/tool is unusable.

## Pitfall: source intake is broader than architecture intake

For daily reports, GitHub Trending and Product Hunt items are not limited to architecture-level absorption. Each item should be triaged for multiple absorbable surfaces:

1. Architecture/control-plane pattern.
2. Developer-tool or workflow capability.
3. Browser automation / runtime / observability capability.
4. Product or competitor signal.
5. Commercial / monetization / customer segment signal.
6. Evidence-retrieval follow-up when a Product Hunt or external link indicates GitHub/source evidence but metadata is unresolved.

Correct behavior:

- For each high-signal GitHub/PH item, decide one of: create P1/P2/P3 candidate, create evidence-retrieval candidate, downgrade to observation with explicit reason, or discard as ordinary news.
- P2/P3 observation or evidence-retrieval tasks are valid; taskpool intake does not require immediate architecture implementation.
- Use fail-closed fields: objective, capability_delta, anti_drift_check, acceptance_evidence, evidence_bundle, truth_gate, expiry, dependency_order.
- Avoid empty sidecars when the report itself names concrete Hermes-adjacent products/repos unless the discard rationale is explicit and evidence-based.

## Pitfall: green runtime, red evolution effectiveness

For dreaming/autonomous-evolution jobs, separate three statuses:

- Runtime health: cron fired, script exited 0, ledger wrote, no degraded/write_blocked.
- Evolution effectiveness: state_advanced, distinct targets, useful score/test change, reduced repeated no_state_change.
- Routing/certification readiness: available model quorum, skipped providers, truth-gate quality, advisory vs certified status.

If cron status is OK but state does not advance for multiple runs, do not call the system healthy without qualification. Treat it as a selector/verifier effectiveness issue.

Common root causes to check:

1. Selector repeatedly chooses the same saturated target because audit-attempt state only updates on improvement.
2. No cooldown / blocked / `last_audit_attempt` marker for consecutive `no_state_change`.
3. Auto-fix cannot address the detected issue class, so scoring remains unchanged.
4. Test fixtures are invalid (`0/N valid`), preventing meaningful advancement.
5. Model routing is a review/readiness issue, not necessarily the root cause.

## Smart-router review pattern

When the user asks for multi-model analysis or router review of a control-plane issue:

1. Run or inspect provider/router status first.
2. Choose tier by blast radius:
   - T0: deterministic local check only.
   - T1: single control-plane script or local workflow behavior; default for selector/cooldown/verifier fixes.
   - T2/T3: global routing/certification framework, provider policy, or broad lifecycle authority changes.
3. Build a claim-linked evidence state file. Include cron output, ledger tail, router probe, and current script snippets as evidence, not only prose.
4. Run multi-model fanout with discussion when risk is non-trivial.
5. Interpret results by certification class:
   - `fanout_quorum_met` means enough planners responded.
   - `truth_not_certified` / `not_certified` means advisory only; do not close lifecycle.
   - Weak agreement or missing approvals should become an intervention packet or governed task, not a done claim.
6. If a provider is unavailable because of auth/setup, classify whether it is required for the selected tier. Missing Gemini auth is a readiness debt, not a blocker for T1 if Claude/GPT/DeepSeek/MiMo quorum is sufficient.

## Minimal reversible fix shape for repeated no-change dreaming jobs

Preferred implementation slice:

1. Add deterministic selector state such as `last_audit_attempt`, `last_audit_result`, `consecutive_no_change`, `cooldown_until`, or `blocked_reason`.
2. In `new_score == old_score`, update attempt/cooldown metadata rather than only logging `skill_unchanged`.
3. Modify selection priority to prefer `last_audit_attempt` over older `last_audit`, demote repeated no-change targets, and skip targets whose cooldown is active.
4. Use a bounded threshold (for example three consecutive no-change attempts) before marking a target cooled down / blocked; this rotates work without pretending an improvement occurred.
5. On successful improvement, clear stale no-change/cooldown state so the target can re-enter normal rotation.
6. Add focused tests for:
   - RED: missing no-change recorder or unchanged target still selected;
   - one no-change attempt rotates to another candidate;
   - repeated no-change writes cooldown/blocked reason;
   - improvement still updates score and clears cooldown state;
   - score regression still rolls back;
   - archived/read-only sources remain protected.
7. Verify with preflight, controlled temp selector probe, dream ledger readback, and taskpool proof log.

## Verification probe contract

A useful deterministic probe for selector fixes should not mutate the live skill database. Use a temp Hermes home with at least two fake skills and a fake confidence DB:

- Seed `apple` with oldest `last_audit`, plus a newer alternate target.
- Assert initial selector chooses `apple`.
- Call the no-change recorder once.
- Assert selector now chooses the alternate target.
- Call no-change recorder up to the threshold.
- Assert `consecutive_no_change` reaches the threshold and `audit_blocked_reason` / cooldown is present.
- Save the probe JSON artifact and link it in the task proof log.

## Argparse pitfall in stateful CLI wrappers

If a wrapper exposes `main(argv=None)` and tests import/call `main()` under pytest, do not let `argparse` read pytest's `sys.argv`. Preferred pattern:

```python
def main(argv: list[str] | None = None) -> int:
    args = parser.parse_args([] if argv is None else argv)
    ...

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```

This keeps imported tests deterministic while preserving real CLI arguments for script execution.

## Red lines

- Do not force `done` from advisory multi-model output.
- Do not globally rewrite skills to hide selector failures.
- Do not classify missing optional provider auth as the root cause unless the selected tier actually requires that provider.
- Do not mutate production lifecycle state without claim-linked proof and normal transition gates.
