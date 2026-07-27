# Synthetic Journey Probe — Capability Map

## Placement

```text
Agent OS advisory/control plane
  └─ Synthetic Journey Probe (this slice)
      ├─ declaration schema
      ├─ default-off validator
      ├─ explicit local-read runner
      ├─ typed JSON assertions
      ├─ digest-only evidence receipt
      └─ negative side-effect assertions
```

## Transfer from AWS Synthetics

| Source concept | Hermes capability | Current state |
|---|---|---|
| Canary | versioned `SyntheticProbe` declaration | landed locally |
| Scheduled run | explicit invocation only | intentionally not connected |
| Step telemetry | per-step assertion result and finding | landed locally |
| Artifact evidence | contract, runner, and target SHA-256 | landed locally |
| Alarm | typed non-zero exit + findings | landed locally |
| SNS fan-out | event projection | not connected; external dispatch closed |
| SQS work queue | Taskpool repair intake | not connected; lifecycle write closed |
| DLQ | quarantine/review lane | contract-level future work only |
| Redrive | authorized revalidation after remediation | manual explicit rerun only |

## Authority surface

Current allowed surface:

```text
explicit CLI invocation
→ validate declaration
→ bounded local JSON read below supplied project root
→ exact assertions
→ stdout receipt
→ optional atomic receipt write under evidence/ or runtime/
```

Closed surfaces:

```text
network/model/browser
cron/scheduler registration
worker/taskpool/mission mutation
external delivery
repair/remediation
memory/skill/experience ingestion
deploy/publish/push/delete/credentials
```

## Relationship to existing checks

- `status/selfcheck/doctor`: reports component and control-plane state.
- Synthetic journey probe: actively reads the real projection and verifies business-level assertions.
- Procedure validation registry: remains separate; this pilot is not registered as proof of global procedure completeness.
- Global certification: remains false regardless of this probe result.

## Promotion path

1. Independent review of this local pilot.
2. Optional procedure-receipt projector with exact evidence binding.
3. Add only local-read journeys that have stable fixtures and negative assertions.
4. Introduce quarantine semantics before any retry automation.
5. Scheduler or external journeys require separate exact authority, rollback, and post-action readback.
