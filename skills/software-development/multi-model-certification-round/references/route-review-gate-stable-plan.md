# RouteReviewGate stable-plan pattern

Use when a user asks for a multi-model intelligent routing review scheme, especially for Hermes/local-brain/taskpool/completion-claim governance.

## Core lesson

Do not define multi-model review as “always run all models” or “majority vote wins.” The stable class-level pattern is a RouteReviewGate:

`Change / Claim / Evidence -> Surface Classification -> Risk Tier -> Capability Match -> Side-effect Boundary -> Evidence-State Check -> Model Route Plan -> Fanout / Specialist Review -> Truth Gate -> Ratification / Degraded Verdict -> Action Boundary`.

## Stable principles

1. Route by `surface`, `risk`, `capability`, `side_effect`, and `evidence_state`, not by model prestige or simple majority.
2. Model output is advisory unless it cites evidence refs and at least one required non-model evidence class is present.
3. Producer/implementer self-report never counts toward completion-critical certification quorum.
4. T2/T3, lifecycle, runtime, external, destructive, publish/deploy/push, credential/payment, and canonical-rule changes require role separation, objective evidence, and fail-closed behavior when quorum/health/evidence is insufficient.
5. Degraded results can guide next evidence requests but cannot be reported as fully certified or used to force `done`.
6. Keep theory-route capability separate from live readiness: current model health/quota/skip status must be read back before claiming a route can execute.

## RouteReviewRecord skeleton

```yaml
RouteReviewRecord:
  schema: route_review_record_v1
  subject:
    kind: change|claim|completion_claim|brain_constraint|taskpool_closeout|skill_update|ssot_update|external_action
    summary: string
    target_files: []
    claim_ids: []
  classification:
    surfaces: []
    risk_tier: T0|T1|T2|T3
    side_effect_class: read_only|local_write|lifecycle_write|external_dispatch|publish_deploy_push|destructive|credential_payment
    blast_radius: local|project|workflow|runtime|external|global
  evidence_state:
    required_evidence: []
    provided_evidence: []
    missing_evidence: []
    evidence_coverage: 0.0
    truth_status: unsupported|needs_link_review|grounded|contradicted
    non_model_evidence_present: bool
  routing:
    primary_specialist: string
    adversarial_reviewers: []
    optional_reviewers: []
    excluded_reviewers: []
    exclusion_reasons: []
    quorum_required: int
    min_quorum: int
    role_separation_required: bool
    producer_models: []
  votes:
    - model: string
      role: specialist|adversary|arbiter|producer|observer
      verdict: approve|amend|reject|abstain|timeout|unhealthy
      evidence_refs: []
      advisory_only: bool
  verdict:
    status: pass|warn|amend|block|not_certified|degraded_not_certified|human_authority_required
    certified: bool
    multi_model_certified: bool
    allowed_actions: []
    forbidden_actions: []
```

## Tier shape

- T0: mechanical/read-only/tool-verifiable. No model or one sanity reviewer; deterministic evidence can be enough.
- T1: single-surface design/docs/local low blast radius. One specialist can advise; two reviewers needed before using multi-model wording.
- T2: cross-file/cross-workflow/local automation/code gates. Specialist + adversarial reviewer + deterministic tests; producer excluded; degraded blocks certification.
- T3: runtime/control-plane/lifecycle/external/destructive/canonical rules. Full discussion/ratification, objective evidence, and human authority where side effects exist; missing quorum/evidence is fail-closed.

## Degraded status semantics

- `single_model_quorum_met`: advisory only unless task is T0/T1 and no multi-certification claim is made.
- `below_min_quorum`: degraded_not_certified; do not close T2/T3.
- `provider_unhealthy` / quota / timeout: health boundary and retry/evidence request; do not permanently lower global quorum.
- `truth_not_grounded`: repair evidence links or gather evidence before certification.
- `not_certified`: implementation proof may be recorded, but lifecycle/taskpool `done` remains blocked.

## Final-plan landing pitfall

When the user asks for a “最终长期稳定方案,” do not leave the artifact as `active-draft` or only return prose. Land a durable SSOT/reference document or skill reference with stable status, explicit current-vs-future boundary, verification/readback, and (if scoped repo changes were made) a scoped commit. Clearly state when runtime automation is not yet live.
