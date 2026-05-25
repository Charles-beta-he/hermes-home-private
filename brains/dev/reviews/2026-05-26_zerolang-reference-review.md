# Zerolang Reference Review for Hermes Dev Brain

Source: https://github.com/vercel-labs/zerolang
Reviewed commit: `80c87fe6e0cbe87f60029af80c3bfa50a64940fc`
Local clone: `/Users/charles/.hermes/runs/zerolang-reference-review-20260526-012618/repo`
Multi-model artifacts: `/Users/charles/.hermes/tick-20260525-173452-929420-p99657-55410d45-62b930a5/`
Boundary: reference-only. Do not integrate zerolang as a Hermes runtime dependency. Do not claim zerolang is production-ready. Treat it as an experimental agent-first language whose workflow patterns can improve Hermes dev-brain governance.

## Evidence inspected

- `AGENTS.md`: pre-1 agent-first language; breaking changes are acceptable when they simplify agent workflows; security vulnerabilities are expected; use isolated/disposable environments.
- `README.md`: compiler exposes stable structured output through `zero check --json`, `parse --json`, `graph --json`, `size --json`, `fix --plan --json`, and version-matched `zero skills` surfaces.
- `skills/zero/SKILL.md` and `skill-data/*.md`: static skill is a thin stub; current workflow comes from the same compiler binary being used.
- `scripts/snapshot-command-contracts.mts`: asserts command JSON contracts, `schemaVersion`, required fields, deterministic repeated build hashes, no ANSI control bytes, release target contracts, and generated artifacts.
- `scripts/reliability-smoke.mts`: writes a reliability report with golden, fuzz, and crasher repro rows.
- `scripts/provenance-guardrails.mts`: validates provenance surface rows, checker owners, and fixture coverage against the conformance runner.
- `docs/articles/optimization.md`: treats size/performance profiles as product contracts and exposes budget/readiness data through JSON.

## Local verification

- `node --version` -> `v24.14.0`
- `pnpm --version` -> `11.1.3`
- `make -C native/zero-c` -> `MAKE_OK`
- `bin/zero --version --json` -> `schemaVersion=1`, `version=0.1.4`
- `bin/zero check --json examples/hello.0` -> structured OK report with diagnostics, cache facts, and compile-time sandbox facts.
- `bin/zero graph --json examples/systems-package` -> structured package/target/capability/readiness report.
- `bin/zero fix --plan --json examples/agent-repair-demo/broken.0` -> diagnostic `TYP009`, repair id `make-binding-mutable`, safety `behavior-preserving`, plan mode only.

## Multi-model result

T2 fanout met quorum: 4 successful planners out of min quorum 3. Consensus was weak but directionally aligned. The combined planners recommended adopting bounded verifier/governance patterns rather than adopting zerolang semantics.

Adopt:
1. Machine-readable automation contracts for agent-consumed CLI/script output.
2. Version-matched workflow loading from the exact tool binary when available.
3. Deterministic JSON contract snapshot verification.
4. Sandbox/disposable-workspace default for experimental compilers, CLIs, evals, benchmarks, generated artifacts, and untrusted examples.
5. Typed repair-plan safety labels.
6. Provenance owner-to-fixture coverage matrices for nontrivial correctness/coverage claims.
7. Optimization/readiness artifacts for performance, size, memory, or readiness claims.

Defer:
- Generic infrastructure to auto-discover and load arbitrary tool-emitted skills/schemas. The dev brain now records the rule; a future Hermes-core tool can implement generic discovery.

Reject:
- Runtime integration of zerolang into Hermes.
- Any production trust claim based on this experimental repository.
- Copying zerolang-specific compiler profiles (`debug`, `fast`, `small`, `tiny`) as global Hermes concepts.
- Breaking compatibility as a global Hermes rule. Zerolang's pre-1 policy is repo-specific; Hermes still preserves user-visible behavior unless explicitly changed.

## Landed Hermes dev-brain changes

Files:
- `/Users/charles/.hermes/brains/registry.yaml`
- `/Users/charles/.hermes/brains/dev/brain.yaml`
- `/Users/charles/.hermes/brains/dev/profile.md`
- `/Users/charles/.hermes/brains/dev/tool-policy.md`
- `/Users/charles/.hermes/brains/dev/verification.md`
- `/Users/charles/.hermes/brains/dev/reviews/2026-05-26_zerolang-reference-review.md`

New dev-brain capabilities:
- `machine_readable_automation_contracts`
- `version_matched_tool_workflow_loading`
- `sandbox_first_experimental_tooling`
- `typed_repair_plan_governance`
- `provenance_fixture_coverage_matrix`
- `optimization_budget_readiness_artifacts`

Acceptance criteria:
- `brainctl` validates all brain YAML.
- Registry records dev-brain routing categories for agent-facing CLI contracts, version-matched workflow, and experimental compiler tasks; runtime fuzzy routing remains a separate `brainctl.py` implementation follow-up because that file already has unrelated uncommitted WIP.
- Dev profile/tool-policy/verification docs explicitly encode the new patterns.
- Git commit is scoped to dev-brain/reference docs and registry only.
