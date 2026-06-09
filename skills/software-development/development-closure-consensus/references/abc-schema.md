# A/B/C Schema — Public Consensus, Project Profile, Compiled Closure Consensus

Use this schema when a closure-check task must become project-specific without letting project-specific derivatives drift away from the public rules.

## Layer A — Public Development Closure Consensus

Truth source for cross-project rules.

Minimum fields:

```yaml
id: development-closure-consensus
version: YYYY-MM-DD.N
principles:
  - id: closure-starts-at-handoff
    statement: Closure begins when the user hands over a task for closure checking.
    source_refs: [Software Requirements, Pragmatic Programmer]
  - id: evidence-precedes-done
    statement: No verified evidence, no closure claim.
    source_refs: [TDD, CI, Continuous Delivery]
stages:
  - intake
  - project-profile-resolution
  - main-chain-diagnosis
  - implementation-gap-closure
  - validation-evidence
  - delivery-closeout
  - learning-writeback
writeback_policy:
  public_rule: update A or shared skill/reference
  project_fact: update B
  deterministic_repeated_action: create script/template/pipeline
  session_progress: do not persist as memory/profile
```

Layer A must not contain project paths, project-specific commands, temporary branch names, or one-off session status.

## Layer B — Project Profile

Truth source for project facts.

Minimum fields:

```yaml
project_id: example-project
version: YYYY-MM-DD.N
repos:
  - role: frontend
    path: /absolute/path
    remote: owner/repo
    default_base: main
  - role: backend
    path: /absolute/path
    remote: owner/repo
    default_base: main
tech_stack:
  frontend: [React, Vite, TypeScript]
  backend: [Java, Maven]
truth_sources:
  product_docs: []
  prototypes: []
  backend_contracts: []
red_lines:
  - Do not remove existing user-visible flows.
  - DB/entity changes require migration verification.
validation:
  frontend:
    build: npm run build
    browser_viewports: [1280x720, 375x812]
  backend:
    compile: mvn -pl api/api-admin -am -DskipTests compile
main_chains:
  exchange:
    frontend_routes: []
    backend_controllers: []
    acceptance_evidence: []
profile_update_history:
  - date: YYYY-MM-DD
    source: evidence source
    change: compact durable fact
```

Layer B must not contain generic closure methodology unless it is a project-local convention that changes execution.

## Layer C — Compiled Project Development Closure Consensus

Derived execution consensus for a project and optionally a task/domain.

Minimum fields:

```yaml
id: project-closure-consensus:<project_id>[:domain]
compiled_consensus_version: YYYY-MM-DD.N
generated_at: ISO-8601
generator_version: closure-compiler-v1
source_global_consensus_version: YYYY-MM-DD.N
source_project_profile_version: YYYY-MM-DD.N
derived_from:
  - development-closure-consensus@YYYY-MM-DD.N
  - project-profile:<project_id>@YYYY-MM-DD.N
stale_policy:
  stale_if_global_consensus_changes: true
  stale_if_project_profile_changes: true
  stale_if_repo_topology_changes: true
  stale_if_validation_contract_changes: true
status: fresh | suspect | stale
execution_plan:
  intake_questions: []
  source_truth_order: []
  best_fix_point_rules: []
  validation_gates: []
  delivery_gates: []
  learning_writeback_rules: []
```

Layer C is never the only truth source. If it needs a lasting edit, first classify the edit into A or B, then regenerate C.

## Invalidation rules

1. A changed -> all C derived from A become `suspect` or `stale`.
2. B changed -> C for that project becomes `stale`.
3. Repo topology, validation commands, red lines, or truth-source order changed -> C becomes `stale`.
4. Session-local findings do not change C unless reclassified into A or B.

## Drift prevention rule

Do not manually maintain long-lived project closure consensus text. Treat it as a compiled cache with provenance. Durable edits belong upstream in A or B.
