# Engineering Coverage Truth Audit

Use when auditing whether an agent/workflow ecosystem is genuinely engineered end to end, rather than merely rich in skills, schemas, nodes, tests, or monitoring records.

## Landing-zone boundary

This is a reusable audit method. Keep live paths, job ids, model names, branches, transient dependency failures, and one-session scores in the scoped audit report or project SSOT—not in this reference.

## Core rule

Separate four claims that are often collapsed:

1. **Architecture/spec coverage** — contracts, schemas, capability nodes, skills, profiles, and documented gates exist.
2. **Runtime integration coverage** — the live conversation/task/runtime path actually calls those components.
3. **Operational health** — current real probes succeed on the live path.
4. **Closure coverage** — failures are classified, repaired or explicitly gated, read back, and retired from active projections.

A high score in one layer does not prove the next layer.

## Audit procedure

### 1. Build a dimension model

Score at least:

- intent intake and routing;
- spec/SSOT;
- planning and decomposition;
- execution/orchestration;
- verification/evidence;
- lifecycle/closure;
- monitoring/observability;
- recovery/self-healing;
- automation/delivery;
- learning/ratchet;
- authority/safety governance.

Define weights before calculating the total. Report the total as an evidence-calibrated maturity estimate, not code coverage.

### 2. Test the exact user intent

Run the live router on the user's original wording, including its actual language. Inspect:

- selected domain;
- ambiguity status;
- suggested capability nodes;
- risk and side-effect class;
- whether the suggestions are semantically relevant.

A large capability graph does not compensate for an exact-intent route that returns `unknown` or irrelevant nodes.

### 3. Audit registry truth, not only registry summary

For every registered system require exactly one state:

- `covered` — at least one concrete current check with evidence;
- `missing` — expected check absent;
- `N/A` — explicitly justified non-applicability.

Fail the registry audit if a system has no attached current checks but is silently counted as covered.

Useful metrics:

```text
attached_check_ratio = systems_with_current_checks / registered_systems
classified_ratio = systems_with(covered|missing|N/A) / registered_systems
```

Do not use `missing_checks` count alone as the coverage percentage.

### 4. Separate static readiness from real runtime smoke

Static selfchecks may prove imports, config shape, adapter registration, or candidate availability. They do not prove real provider/tool/runtime availability.

For any health claim that gates certification or autonomous promotion, require both:

- deterministic/static readiness result;
- fresh real invocation result on the same route/tier.

If static readiness passes but real invocation fails, report `readiness_ok_runtime_degraded`; never project this as healthy or certified.

### 5. Reconcile current state with event history

A current scheduler/job status may be healthy while the event ledger still contains a recent failure. Distinguish:

- current projection;
- recent unresolved event;
- historical resolved event.

Do not call the root cause closed until repair/readback evidence exists. Conversely, do not keep resolved history as an active outage.

### 6. Measure closure debt and signal quality

Inspect:

- open findings by component/severity;
- waiting-for-judgement plans;
- debounced/coalesced fingerprints;
- expected policy rejections misclassified as failures;
- TTL/resolved/retired behavior;
- stale findings that no longer block the live system.

A system that detects hundreds of findings but cannot retire or classify them has strong observability but weak closure engineering.

### 7. Validate skill/reference integrity carefully

When scanning `references/...` mentions, distinguish:

- local support-file reference;
- explicit cross-skill reference;
- external/scoped document reference;
- superseded reference;
- genuinely broken local reference.

Do not label every unresolved same-directory path as broken; first classify the intended reference type. Prefer machine-readable reference types or explicit neighboring-skill qualifiers.

### 8. Run independent review without overclaiming

A failed multi-model fan-out is itself operational evidence. Report the audit as deterministic/main-review only and state `not multi-model certified`. Do not discard the deterministic audit, but do not imply independent consensus.

## Evidence hierarchy

Strongest to weakest:

1. fresh live invocation/readback on the target path;
2. integration/E2E test using real imports and temp state;
3. focused unit test;
4. runtime source wiring inspection;
5. generated projection/registry;
6. schema, design doc, skill text, node/file count.

Never let a lower level override contradictory higher-level evidence.

## Common pitfalls

- Treating node count or skill count as coverage.
- Treating passing static provider selfcheck as real model health.
- Treating `0 high-risk systems` as proof when the registry omits systems or leaves them unclassified.
- Treating current green status as proof that a recent failure was root-cause closed.
- Treating all historical findings as current outages.
- Producing one blended score without exposing weak dimensions.
- Claiming multi-model certification after quorum failure.

## Verification checklist

- [ ] The exact original intent was routed live.
- [ ] Every registered system is covered, missing, or explicitly N/A.
- [ ] Attached-check and classified ratios were calculated.
- [ ] Static readiness and real runtime smoke were compared.
- [ ] Current state and recent event history were reconciled.
- [ ] Closure debt and false-positive controls were inspected.
- [ ] Reference mentions were type-classified before calling them broken.
- [ ] The final score cites fresh evidence and names its certification boundary.
