# Dynamic Self-Check Coverage Architecture — Evidence Pack

Date: 2026-07-06
Scope: Hermes dynamic self-check coverage that adapts to Hermes updates/iterations and to each user's enabled systems.
Status: design/evidence pack, not runtime implementation.

## Objective

Upgrade self-check from a fixed checklist into a local-first adaptive control plane:

1. Discover each user's active systems and workflows.
2. Detect update/change/failure events.
3. Maintain a Coverage Registry of what is covered, missing, stale, or risky.
4. Generate dynamic coverage proposals.
5. Promote only safe local/read-only/success-silent monitors automatically; gate external writes, push/deploy, credentials, destructive actions, and broad delivery.

## Research grounding

### 1. Cybernetics / feedback control

Core claim: a self-check system is a feedback controller. It must observe system state, compare it with a desired state, and choose corrective action under constraints.

Core works:
- Norbert Wiener, *Cybernetics: Or Control and Communication in the Animal and the Machine* (1948).
- W. Ross Ashby, *An Introduction to Cybernetics* (1956), DOI: 10.5962/bhl.title.5851.
- Ashby's Law of Requisite Variety: the controller needs enough variety to handle the variety of disturbances.
- John L. Hellerstein et al., *Feedback Control of Computing Systems* (2004), DOI: 10.1002/047166880x.

Design implication:
- Static checks cannot cover diverse user systems. The self-check controller must expand its observation/action variety through user-system profiles and change-aware coverage maps.

### 2. Autonomic computing / MAPE-K

Core claim: long-running systems need Monitor → Analyze → Plan → Execute over shared Knowledge.

Core works:
- IBM autonomic computing vision; e.g. *The dawning of the autonomic computing era* (IBM Systems Journal, 2003), DOI: 10.1147/sj.421.0005.
- J. O. Kephart & D. M. Chess, autonomic computing / self-managing systems framing.
- MAPE-K self-adaptive systems literature; e.g. SEAMS work and surveys.

Design implication:
- Hermes dynamic self-check maps directly to MAPE-K:
  - Monitor: cron/jobs, logs, issues, git diff, MCP/tools, providers, delivery paths.
  - Analyze: classify risk/surface/coverage gap.
  - Plan: generate coverage proposal and verification matrix.
  - Execute: run checks or create approved local-only monitors.
  - Knowledge: Coverage Registry + evidence ledger + user system profile.

### 3. Viable systems / organizational cybernetics

Core claim: a system that must remain viable needs recursive control, operational autonomy, coordination, intelligence, and policy boundaries.

Core works:
- Stafford Beer, *Brain of the Firm*; Viable System Model.
- Stafford Beer, *The Heart of Enterprise*.

Design implication:
- Self-check should be recursive: core Hermes, workflows, taskpool, gateway, project profiles, and user-facing channels each need local monitors, but policy governs side effects globally.

### 4. SRE / observability

Core claim: reliable systems distinguish symptoms, causes, service-level indicators, alerting noise, and actionable remediation.

Core works:
- Google SRE book, especially monitoring distributed systems and alerting philosophy.
- Observability practice: logs/metrics/traces, actionable alerts, toil reduction.

Design implication:
- Default success-silent checks reduce alert fatigue.
- Every alert/proposal must name owner/system, evidence, severity, next action, rollback, and whether it is user-facing.

### 5. Regression test selection / change impact analysis

Core claim: after code changes, verification should be selected by dependency/impact rather than running a fixed universal suite every time.

Core works:
- Gregg Rothermel & Mary Jean Harrold, safe regression test selection, DOI: 10.1109/ICSM.1993.366926 and DOI: 10.1145/248233.248262.

Design implication:
- Hermes update-aware coverage planner should map changed files/surfaces to specific checks:
  - doctor.py -> doctor tests + doctor CLI smoke.
  - provider adapters -> exact provider runtime smoke + route eligibility.
  - prompt/system prompt -> cache/role/ghost prevention checks.
  - cron/gateway -> delivery readback and output artifact inspection.

### 6. Safety engineering / STAMP / resilience engineering

Core claim: accidents often arise from unsafe control actions and missing constraints, not only component failures.

Core works:
- Nancy Leveson, *Engineering a Safer World* (2012), DOI: 10.7551/mitpress/8179.001.0001.
- Erik Hollnagel et al., *Resilience Engineering: Concepts and Precepts*.

Design implication:
- Dynamic coverage must not become dynamic uncontrolled execution.
- Promotion gates and authority boundaries are part of the safety controller.

### 7. Continuous monitoring governance

Core claim: monitoring is a continuous program that maintains ongoing awareness of system risk.

Core works:
- NIST SP 800-137, Information Security Continuous Monitoring (ISCM).

Design implication:
- Coverage Registry should include freshness, stale checks, known gaps, and risk posture, not just pass/fail.

## Multi-model review status

Attempted Hermes consult_models review:
- T2 review attempt: degraded; gpt-5.5 marked unhealthy/timeout; only MiMo attempted; consensus timed out.
- T0 short review attempt: no planners available after quota/health gate; Claude quota evidence stale/unobservable; MiMo unhealthy.
- consult_models selfcheck itself passed earlier, but runtime model availability was not sufficient for certification.

Conclusion:
- This packet is not multi-model certified.
- However, the degradation itself supports one design requirement: model/provider health must be a first-class coverage surface, and dynamic self-check must fail closed for model-quorum-dependent automation.

## Final architecture

### A. Coverage Registry

Path proposal:
`~/.hermes/state/selfcheck/coverage_registry.json`

Core records:
- system_id
- detected_from
- owner/profile/project
- active/inactive
- risk_level
- current_checks
- missing_checks
- stale_checks
- evidence_refs
- last_observed_at
- proposals
- promotion_state
- rollback

### B. User System Profile

Sources:
- cron jobs
- project profiles
- git remotes and open issues
- MCP/tool registry
- gateway channels
- model providers
- taskpool/local brain
- memory/skills
- storage/logs

Output:
`~/.hermes/state/selfcheck/user_system_profile.json`

### C. Change-aware Coverage Planner

Inputs:
- git diff / commit / update
- issue type
- cron failure class
- delivery failure
- MCP reload
- provider health drift

Output:
`~/.hermes/state/selfcheck/coverage_plan_<timestamp>.json`

Surface mapping examples:
- `hermes_cli/doctor.py`: doctor tests, doctor --fix, post-update-check.
- `agent/*adapter*.py`: provider runtime smoke, fallback route eligibility, quota state.
- `agent/prompt_builder.py` / `system_prompt.py`: prompt cache, role alternation, ghost prevention.
- `cron/jobs.json` / gateway: delivery readback, failed output artifact, resend proposal.
- taskpool/kanban: boundary selfcheck, stale claim scan, evidence gate.

### D. Proposal Generator

Each proposal must include:
- id
- reason
- evidence
- target system
- workflow type
- schedule
- script/check command
- no_agent/local-only status
- success behavior
- failure behavior
- side effects
- promotion authority needed
- rollback/remove command
- first-run verification

### E. Promotion Gate

Auto-promote allowed only for:
- read-only monitor
- local-only no-agent cron
- success-silent output
- deterministic script with dry-run/readback
- no external writes

Require explicit authority for:
- Telegram/Discord/Slack delivery
- GitHub issue comment/close
- push/deploy/publish
- credential entry
- destructive cleanup
- broad fanout

### F. Runtime lifecycle

1. Discover profile.
2. Detect events.
3. Update coverage registry.
4. Generate coverage plan.
5. Run immediate safe checks.
6. Emit proposals for missing persistent coverage.
7. Promote gated proposals.
8. Record evidence/readback.
9. Retire stale checks.

## Stability risks and mitigations

1. Workflow explosion
   - Mitigation: TTL, owner/system grouping, max new proposals per run, dedupe keys.

2. Alert fatigue
   - Mitigation: success-silent, severity threshold, user-facing only when delivery authorized.

3. Self-modification loops
   - Mitigation: proposal-before-promotion, local-only default, no recursive cron creation from cron runs.

4. False coverage claims
   - Mitigation: every coverage claim needs readback evidence and freshness.

5. Model dependency instability
   - Mitigation: deterministic checks first; model reviews advisory unless quorum and evidence gates pass.

6. User-specific privacy/authority leakage
   - Mitigation: user profile stays local; external dispatch requires exact target/payload/readback.

7. Stale user system profile
   - Mitigation: profile discovery every selfcheck run; confidence/freshness fields.

## Implementation roadmap

P1: Read-only registry and report
- Build `dynamic_selfcheck_coverage.py discover --json`.
- Produce registry/report only; no workflow creation.

P2: Change-aware planner
- Add diff/issue/cron-failure to check mapping.
- Output coverage plans.

P3: Proposal generator
- Generate local-only workflow proposals with rollback and first-run commands.

P4: Allowlisted auto-promotion
- Promote only read-only/local/no-agent/success-silent monitors.

P5: User-facing repair packets
- For delivery failures, generate resend/repair packet, but require exact authority before external send.

## Final recommendation

Adopt dynamic self-check as a gated MAPE-K control plane:
- dynamic in coverage discovery and proposal generation;
- conservative in workflow promotion;
- deterministic and local-first by default;
- evidence-ledger backed;
- model-assisted but not model-dependent;
- user-profile adaptive without leaking authority.

## Commit-gate evidence labels

design_doc: This document plus `skills/autonomous-ai-agents/hermes-agent/references/dynamic-selfcheck-coverage-control-plane.md` define the scoped design, lifecycle states, local-only execution gate, and rollback boundary for the dynamic self-check coverage control plane.

gate_readback: Latest local verification readback: `python3 -m pytest scripts/tests/test_dynamic_selfcheck_coverage.py -q` returned 11 passed; `python3 -m py_compile scripts/dynamic_selfcheck_coverage.py` returned exit 0; cron job `29d9eaa6bf48` read back `last_status=ok`, `deliver=local`, `no_agent=true`; `coverage_lifecycle.json` read back active=5, resolved=0, retired=0.
