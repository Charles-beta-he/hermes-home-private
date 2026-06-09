# Hermes UX 9.0 Long-Term Stable Optimization SSOT

Date: 2026-05-31
Status: active SSOT / degraded multi-model advisory, not certified consensus
Scope: Hermes Agent self-optimization, cloud-brain/edge-tentacle UX, consult_models friction, runtime issue capture, taskpool governance

## Goal

Raise Hermes self-architecture UX from ~6.52/10 to 9.0 through stable architecture primitives, not ad-hoc patches.

North star: supervised autonomy. Hermes should be a controllable cloud-brain + edge-tentacle system where every automatic action is visible, evidence-backed, bounded by capability/trust, recoverable, and explainable.

## Runtime issue that triggered this SSOT

During a long multi-model prompt run, the command below failed:

```bash
python3 ~/.hermes/scripts/consult_models.py ... --prompt-file /tmp/hermes_ux_longterm_prompt.txt
```

Live error:

```text
consult_models.py: error: unrecognized arguments: --prompt-file
```

Observed workaround was to manually call `consult_models.py state "$(cat file)" ...`, which is brittle for long prompts, quoting, shell limits, and multi-line Chinese text.

## Decision 1 — add `consult_models.py state --prompt-file`

Decision: yes, `consult_models.py state` should support `--prompt-file`.

Rationale:
- Long multi-model prompts are durable artifacts and should not be forced through shell quoting.
- Prompt files are the natural SSOT input boundary for evidence-based multi-model runs.
- This reduces operator friction without changing model selection, quorum, truth gate, or fan-out semantics.
- It is low-risk: only state construction input is expanded.

Contract:
- `question` positional becomes optional.
- `--prompt-file PATH` reads UTF-8 text, strips surrounding whitespace, and rejects empty files.
- Positional question and `--prompt-file` are mutually exclusive.
- Existing positional behavior remains compatible.

Verification:
- `python3 -m py_compile ~/.hermes/scripts/consult_models.py`
- `consult_models.py state --prompt-file /tmp/file --out /tmp/state.json`
- conflict case exits 2 when both positional question and `--prompt-file` are supplied.

## Decision 2 — runtime problems should become taskpool candidates, not silent memories

Decision: yes, runtime problems encountered during Hermes operation should be capturable into taskpool automatically, but the default mode must be safe candidate capture, not unconditional enqueue.

Why not memory:
- Runtime failures like unsupported flags, bad CLI UX, hook errors, parse failures, and taskpool wedging are not stable user preferences.
- They are work items with evidence, reproduction, impact, and verification, so they belong in taskpool/evidence spine.

Why not unconditional auto-enqueue:
- Many runtime errors are transient, duplicates, user mistakes, or low-value noise.
- Direct enqueue can flood taskpool and create false urgency.
- Some issues require triage before becoming execution work.

Stable pattern:

```text
RuntimeFrictionEvent
  -> fingerprint/dedup
  -> candidate record under ~/.hermes/state/runtime-issue-candidates.jsonl
  -> severity + impact classification
  -> enqueue only if explicit mode=enqueue or policy says high-confidence P1/P2
  -> taskpool item references SSOT/evidence, not copied chat summaries
```

Modes:
- `suggest`: default. Record candidate only.
- `enqueue`: create taskpool item with governed metadata.
- `drop`: ignore known-benign patterns.

Required fields:
- title
- source_command
- error_excerpt
- reproduction
- impact
- expected_behavior
- severity
- architecture_target
- evidence_ref
- fingerprint

Dedup key:
- normalized source command + first stable error line + architecture target.

Taskpool policy:
- P1: breaks core workflow or blocks dispatch/multimodel/taskpool progress.
- P2: repeated friction or missing UX primitive with clear fix.
- P3: polish/low-frequency ergonomic issues.

Guardrails:
- Never auto mark done.
- Never auto enqueue high-blast-radius implementation.
- Never store secrets from command output.
- Redact tokens, API keys, Bearer headers, cookies, and env values.
- Attach reproduction and evidence_ref.
- Event-driven only; no cron polling by default.

## Core theoretical basis

### 1. John Dewey, How We Think (1910)
Core claim: reflective thought starts from felt difficulty, turns it into a problem, investigates, hypothesizes, tests, and learns.
Hermes constraint: runtime friction should become structured learning loops, not discarded anecdotes.

### 2. Donald Schön, The Reflective Practitioner (1983)
Core claim: professionals improve through reflection-in-action and reflection-on-action.
Hermes constraint: when Hermes hits a live tool/CLI mismatch, it should capture the mismatch while the context is fresh.

### 3. Chris Argyris & Donald Schön, Organizational Learning (1978)
Core claim: single-loop learning fixes immediate errors; double-loop learning changes governing assumptions.
Hermes constraint: unsupported `--prompt-file` is single-loop fix; runtime issue capture is double-loop mechanism.

### 4. W. Edwards Deming, Out of the Crisis (1982)
Core claim: continuous improvement requires feedback loops, measurement, and systemic correction rather than blaming operators.
Hermes constraint: repeated operational friction should feed a governed improvement queue with evidence and priority.

### 5. Nancy Leveson, Engineering a Safer World (2011)
Core claim: safety is a control-structure problem; feedback and constraints maintain safe behavior.
Hermes constraint: issue capture must be bounded by policy gates, not uncontrolled self-modification.

### 6. Norbert Wiener, Cybernetics (1948)
Core claim: communication and feedback are the basis of control.
Hermes constraint: runtime errors are feedback signals; ignoring them weakens the control loop.

### 7. Donald Norman, The Design of Everyday Things (1988/2013)
Core claim: good UX provides visibility, feedback, constraints, mapping, and recoverability.
Hermes constraint: CLI friction should be visible, explainable, and directly convertible into repair candidates.

### 8. John Allspaw, Etsy blameless postmortems / resilience engineering practice
Core claim: incidents reveal how systems actually work; learning systems capture weak signals without blame.
Hermes constraint: runtime friction events should be treated as improvement evidence, not user/operator fault.

### 9. Google SRE, Site Reliability Engineering (2016)
Core claim: reliability is managed through SLOs, error budgets, incident response, and automation with human oversight.
Hermes constraint: issue capture should classify impact and feed taskpool, but execution remains governed.

### 10. Martin Fowler, Event Sourcing (2005)
Core claim: state should be explainable from an append-only event log.
Hermes constraint: runtime issue candidates should be append-only events; taskpool tasks are projections/decisions.

### 11. Pat Helland, Life Beyond Distributed Transactions (2007)
Core claim: distributed systems need local transactions, messages, idempotency, and compensation.
Hermes constraint: issue capture should append local candidate events first; enqueue is a separate idempotent projection.

### 12. Russell Ackoff, Redesigning the Future / systems thinking
Core claim: improvement requires redesigning the system that produces problems, not only fixing individual symptoms.
Hermes constraint: fixing `--prompt-file` is necessary but insufficient; Hermes needs a runtime-friction-to-taskpool system.

## 9.0 roadmap

### Phase A — Immediate friction closure
- Add `consult_models.py state --prompt-file`.
- Verify py_compile and CLI behavior.
- Record this SSOT.

UX gain: small but concrete. Removes long-prompt shell friction.

### Phase B — RuntimeFrictionEvent capture
- Add a default-safe capture utility.
- Default `suggest` mode writes append-only JSONL candidates.
- Explicit `enqueue` mode creates taskpool items with priority/dependency/multimodel triage metadata.
- Integrate later into high-value entrypoints: consult_models failures, taskpool hooks, bg-review, post-update-check, provider/router failures.

UX gain: Hermes learns from live problems without hallucinating completion.

### Phase C — DiagnoseContract v1
- `hermes-edge diagnose --json` and/or `hermes diagnose --json` schema.
- Reason codes, recovery actions, risk level, evidence refs.

UX gain: makes failures explainable and machine-consumable.

### Phase D — DeviceTwin reported-only
- Read-only sidecar state projection.
- reported/observed/verified/desired state separation.
- trust/health/capability posture.

UX gain: devices become first-class product objects.

### Phase E — Pairing + progressive trust
- One-time pairing code, short-lived token, revoke/re-pair.
- unpaired -> paired -> attested -> trusted_low/high -> degraded/quarantined/revoked.

UX gain: multi-device onboarding becomes product-grade.

### Phase F — TaskLedger explainability + lease/fencing
- Task transition reason_code, attempt_id, lease_epoch, idempotency key, dead-letter, recovery proposal.

UX gain: taskpool becomes a recoverable commitment ledger.

### Phase G — MultiModelGovernance UX
- certified/degraded/single/failed statuses.
- evidence coverage, model disagreement, fallback reason, action restrictions.

UX gain: multi-model complexity becomes understandable governance.

### Phase H — dashboard/wizard/timeline
- Device dashboard.
- Pairing wizard.
- Task timeline.
- Red/yellow/green health.

UX target: 9.0.

## Invariants

- No silent downgrade.
- No trust without evidence.
- No task done without evidence_ref.
- No degraded advisory triggering high-risk execution.
- No runtime issue auto-done.
- No unconditional runtime issue enqueue without dedup/severity/policy.
- No secrets in candidate logs.
- No polling-first design when an event can trigger capture.

## Current landing status

- `consult_models.py state --prompt-file` implemented in live profile script.
- Runtime issue capture scaffold should be added as a low-risk utility before broad integration.
- Broader 9.0 work remains staged through taskpool candidates and verifier-first implementation.
