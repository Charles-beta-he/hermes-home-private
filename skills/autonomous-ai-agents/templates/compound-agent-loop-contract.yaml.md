# Compound Agent Loop Contract Template

Scope: class-level autonomous-agent workflow contracts for any substantial maker/verifier loop, including bilevel or meta-loop patterns where an outer loop proposes changes to an inner loop's search strategy.

Applicability: use before dispatching or delegating multi-step agent work that needs measurable acceptance, budget limits, independent verification, scoped state read/write, and explicit authority gates.

Anti-conditions: do not use this template to store task progress, private payloads, credentials, provider-specific marketing claims, or project-specific facts. Do not treat completing this template as permission to execute workers, schedule cron jobs, publish, deploy, send messages, or perform destructive actions.

```yaml
compound_agent_loop:
  source:
    request: ""
    source_refs: []
    source_boundary: "user_request | repo_docs | official_doc | social_source | inferred"
    unverified_claims: []
    claims_not_proven: []

  objective:
    goal: "observable desired state"
    success_criteria: []
    measurable_objective:
      metric: "metric or observable comparator used for pass/fail"
      benchmark: "fixed benchmark, task suite, command, dataset, or reproducible scenario"
      comparator: "baseline, inner_loop_only run, previous verifier result, or control condition"
    constraints: []
    non_goals: []
    red_lines: []

  loop_roles:
    inner_loop_responsibility: "execute bounded task attempts inside the declared objective/evaluator"
    outer_loop_responsibility: "change or select the search strategy/mechanism; not ordinary retries"
    not_outer_loop: "parameter/prompt/config retuning inside a fixed mechanism unless it alters exploration behavior"

  budget:
    max_turns: null
    max_runtime_minutes: null
    max_cost_usd: null
    stop_conditions:
      - acceptance_met
      - evidence_missing_after_attempt
      - authority_boundary
      - budget_exhausted

  context_read:
    project_state_refs: []
    skills: []
    evidence_files: []
    repo_docs: []
    prior_lessons_used: []
    meta_loop_input_boundary:
      allowed_observation_surface:
        - code
        - traces
        - logs
        - benchmark_outputs
        - experiment_ledger
      disallowed_observation_surface:
        - arbitrary private context
        - credentials
        - unrelated runtime state

  workspace:
    mode: "read_only | local_write | isolated_worktree | temp_dir"
    path: ""
    rollback: "how to revert or discard"

  maker:
    role: "executor"
    model_or_tool: ""
    allowed_tools: []
    disallowed_tools: []
    required_output:
      - changed_artifacts_or_findings
      - command_log_or_readback
      - residual_risks

  verifier:
    role: "independent verifier"
    model_or_tool: "deterministic command | separate model | human | self_review_with_deterministic_evidence"
    rubric: []
    evidence_only_context: true
    verdict_schema:
      status: "pass | warn | fail | blocked"
      missing_evidence: []
      next_action: ""

  outer_loop:
    enabled: false
    outer_loop_change_surface: "none | prompt_strategy | skill_reference | workflow | evaluator | search_policy | script_patch | memory_schema_proposal"
    mechanism_change_surface: "what exploration/search mechanism may change, if any"
    mechanism_carrier: "code | prompt | skill | workflow | evaluator | memory_schema_proposal | none"
    exploration_or_diversification_delta: "how this differs from repeating the same inner loop"
    benchmark_comparator_required: true
    no_authority_expansion: true
    no_authority_expansion_boundary: >
      Mechanism/search-strategy changes stay inside the declared change surface and do not widen tool authority,
      lifecycle authority, scheduler/worker authority, external dispatch, publish/deploy, destructive actions, or secret access.
    injected_mechanism_claims_not_proven: []

  evidence:
    required_refs:
      - command:
      - artifact:
      - screenshot:
      - url:
      - proof:
    claims_supported: []
    claims_not_proven: []

  writeback:
    candidates:
      - lesson: ""
        landing: "project_state | skill_reference | memory | user_memory | taskpool | experience_atom | none"
        gate: "verified_reusable | project_scoped | stable_preference | reject_task_progress"
    anti_ghost_check:
      no_task_progress: true
      no_secret_or_private_payload: true
      scope_is_correct: true
      removal_or_demotion_path: true

  authority_gates:
    external_read: "allowed | needs_approval | blocked"
    local_write: "allowed | needs_approval | blocked"
    lifecycle_write: "allowed | needs_approval | blocked"
    scheduler_or_worker: "allowed | needs_approval | blocked"
    external_dispatch: "allowed | needs_approval | blocked"
    publish_deploy_push: "allowed | needs_approval | blocked"
    destructive_or_payment_or_secret: "blocked unless exact authority"

  closure:
    state: "not_started | running | pass | warn | fail | blocked"
    evidence_refs: []
    remaining_boundaries: []
```

Minimum completion rule: do not mark `pass` unless the verifier verdict and evidence refs support every material success criterion. If a safe next local slice remains and the user asked to continue/full-land, continue rather than finalizing.

Outer-loop rule: do not claim bilevel/compound self-improvement unless the contract names the measurable objective, benchmark/comparator, verifier, inner-loop responsibility, outer-loop mechanism/search-strategy change surface, trace/code/log/ledger input boundary, claims_not_proven, and no-authority-expansion boundary. Without those fields, the claim is at most an anecdotal retry pattern, not a governed outer-loop mechanism improvement.
