# Always-Callable Agent Module Contract

Version: 1.1.0

## Purpose

`root-cause-ownership-council` is not meant to be pasted into every prompt. It should become an always-callable module: every model/agent may request it when risk signals appear, while the full role/council content stays progressively loaded.

Core rule:

```text
Always callable, not always loaded.
```

## Three-layer loading model

### Layer 0 — Micro-router, safe to keep broadly visible

A compact trigger contract can be included in model/system/workflow routing surfaces:

```yaml
agent_module:
  id: root-cause-ownership-council
  call_when:
    - repeated_fix
    - multi_controller_shared_state
    - high_risk_runtime_change
    - evidence_gap_or_model_disagreement
    - final_certification_needed
    - user_requests_root_cause_or_existing_issue_tests
  do_not_call_when:
    - trivial_one_line_bug_with_direct_evidence
    - pure_copy_or_style_tweak
    - low_risk_crud_without_shared_state
    - one_off_demo_with_accepted_limited_verification
  first_action: council_router.plan
```

This layer should not contain all role definitions.

### Layer 1 — Role registry, load on demand

Load role cards only after Layer 0 triggers. Source:

- `references/agent-role-registry.md`
- `templates/agent-card.yaml.md`

This layer answers: which roles should run?

### Layer 2 — Full council workflow, load only for real council sessions

Load full SKILL.md, session template, calibration domains, and repo evidence only when:

- a high-risk or repeated problem is confirmed;
- multiple roles are needed;
- an ownership/evidence/falsifier packet is required;
- a final PASS/BLOCK verdict will be issued.

Sources:

- `SKILL.md`
- `templates/council-session.yaml.md`
- `references/calibration-domains.md`
- `references/github-agent-repos-evidence.md`

## Authority boundary

This module may produce:

- role plan;
- owner contract;
- evidence ledger;
- dissent ledger;
- regression matrix;
- implementation boundary;
- certification verdict.

This module must not by itself:

- push, merge, deploy, publish, or send external messages;
- mutate taskpool lifecycle or scheduler state;
- write durable memory;
- enter credentials or payments;
- perform destructive operations;
- treat model votes as completion evidence.

Execution still requires the current Hermes tool policy, explicit user authority when needed, and fresh readback evidence.

## Integration surfaces

Safe consumers:

- Hermes skills and project workflows;
- code review workflows;
- debugging flows;
- taskpool/mission planning packets as proposal-only evidence;
- multi-model review prompts;
- future Agent Role Registry / Council Router runtime.

Unsafe by default:

- external dispatch adapters;
- production deployment automation;
- payment/credential flows;
- automatic memory/skill mutation;
- irreversible lifecycle advancement.

## Falsifier

This module should be narrowed if it causes:

- routine small tasks to over-route into council mode;
- role ceremony without better evidence;
- token bloat from always-loading full role text;
- false confidence from model consensus;
- implementation delay when direct evidence already proves a simple fix.
