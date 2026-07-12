# Absorption Report

## Source identity

- Repository: `https://github.com/Shubhamsaboo/awesome-llm-apps`
- Pinned commit: `426cfa66b5fd832090038c36e50a6aa1dab3119c`
- Root license: Apache-2.0
- Local reference clone: `/Users/charles/.hermes/runs/awesome-llm-apps-reference-review-20260713/repo`
- Boundary: dependency, model, API and data licenses were not yet audited per application.

## Static inventory result

The deterministic scanner found 162 runnable-example directories with README plus a runtime/package indicator. This is static source evidence, not proof that all 162 applications run locally.

| Capability family | Source examples |
|---|---:|
| General agent | 43 |
| Multi-agent | 39 |
| RAG | 31 |
| MCP/tools | 20 |
| Generative UI | 14 |
| Voice | 12 |
| Research | 9 |
| Memory | 7 |
| Finance | 6 |
| Content | 4 |
| Coding | 3 |
| Data analysis | 3 |
| Monitoring | 1 |

## Module pool

Generated 18 valid candidate modules:

- 5 governance/foundation modules: intent capture, source evidence, risk model, output contract, evidence gate.
- 13 source-derived functional families listed above.

All modules passed `validate_capability_module`; maturity remains `candidate` and retention remains project-scoped/domain candidate. No module was promoted to validated/common/canonical.

## Loop recommendation

Workflow Kernel Loop v2 executed all nine stages and returned PASS for contract coverage. Its decision was `session_plan`, which is correct for a temporary workflow. It explicitly reported:

- global certification: false
- canonical ratchet promotion: false
- external, cron, taskpool and AgentOS side effects: false
- procedure registry: attention required, so its 100% is contract coverage rather than global operational certification

## Temporary workflow

`temporary-workflows/awesome-functional-absorption.json` contains:

```text
intent_seed_capture
→ source_evidence_collector
→ risk_modeler
→ output_contract_builder
→ evidence_gate
→ selected functional families
```

The current broad query selects all 13 functional families. For a real request, the query should be narrowed so the same builder selects only relevant modules.

Gates:

1. source identity gate
2. license/dependency gate
3. runtime evidence gate

Closure states:

- recommended
- static_evidence_only
- runtime_verified
- blocked
- rejected

## Recommended replication order

P0 — shared primitives:

1. RAG ingestion/retrieval/citation primitives
2. MCP/tool adapters and tool-contract normalization
3. memory ownership, recall and lifecycle primitives
4. source/evidence and runtime proof gates

P1 — reusable workflows:

1. research workflow
2. multi-agent reviewer/executor composition
3. always-on monitoring with explicit scheduler/dispatch gates
4. voice intake and transcript routing

P2 — domain compositions:

1. finance research
2. data analysis
3. coding/repository analysis
4. content workflows
5. generative UI

## Not proven

- No upstream application dependencies were installed.
- No model/provider credentials were used.
- No upstream example was runtime-certified.
- No external API, UI, production, scheduler or dispatch capability was enabled.
- The scanner classification is filename/path based and requires per-family source review before implementation.
