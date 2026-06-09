# Compiled Project Closure Consensus Template

Use this template as the C-layer derivative produced from:

- A: `development-closure-consensus`
- B: a canonical project profile

Do not treat a filled copy as the only truth source. Regenerate it when A or B changes.

```yaml
id: project-closure-consensus:<project_id>:<optional-domain>
compiled_consensus_version: YYYY-MM-DD.N
generated_at: YYYY-MM-DDTHH:mm:ssZ
generator_version: closure-compiler-v1
status: fresh

source_global_consensus:
  id: development-closure-consensus
  version: YYYY-MM-DD.N
  source_path: ~/.hermes/skills/software-development/development-closure-consensus/SKILL.md

source_project_profile:
  project_id: <project_id>
  version: YYYY-MM-DD.N
  source_path: ~/.hermes/project-profiles/<project_id>.json

derived_from:
  - development-closure-consensus@YYYY-MM-DD.N
  - project-profile:<project_id>@YYYY-MM-DD.N

stale_policy:
  stale_if_global_consensus_changes: true
  stale_if_project_profile_changes: true
  stale_if_repo_topology_changes: true
  stale_if_validation_contract_changes: true
  stale_if_truth_source_order_changes: true

project_topology:
  repos:
    - role: frontend
      path: /absolute/path
      default_base: main
      validation:
        - command: npm run build
          evidence_type: build
    - role: backend
      path: /absolute/path
      default_base: main
      validation:
        - command: mvn test
          evidence_type: test

closure_execution:
  trigger_phrases:
    - 检查任务闭环情况
    - 全盘推进
    - 收口
  truth_source_order:
    - task body / issue / Lark
    - project profile
    - product docs / PRD
    - prototype source
    - current frontend implementation
    - backend source of truth
    - tests / validation scripts
  main_chain_definition: <what user/system chain must be closed>
  best_fix_point_rules:
    - Prefer source-of-truth layer over symptom layer.
    - If backend contract is wrong, fix backend before frontend workaround.
  red_lines:
    - <project-specific non-negotiable rule>
  validation_gates:
    - name: frontend build
      command: <command>
      required: true
    - name: browser smoke
      command: <command or manual protocol>
      required: true
  delivery_gates:
    - verify fresh branch before commit
    - rebase onto true remote base before PR
    - rerun validation after baseline changes
    - create PR with explicit base/head
    - record cross-repo dependency and merge order
  learning_writeback:
    public_consensus_candidates: []
    project_profile_candidates: []
    scripts_or_pipeline_candidates: []
    adr_candidates: []

last_compilation_report:
  profile_found: true
  assumptions: []
  unresolved_gaps: []
```
