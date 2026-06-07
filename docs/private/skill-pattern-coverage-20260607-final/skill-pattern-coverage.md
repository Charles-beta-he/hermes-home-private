# Hermes Skill Pattern Coverage Audit

Date: 2026-06-07 18:09:13
Skills root: `/Users/charles/.hermes/skills`
Scope: non-mutating heuristic audit of existing `SKILL.md` files.

## Executive summary

- Total skills scanned: 237
- Active skills scanned: 213; archived skills scanned: 24
- Active `## When to Use`: 213/213 (100.0%)
- Active verification or Definition of Done: 213/213 (100.0%)
- Active minimum eval prompts: 213/213 (100.0%)
- Active full routing matrix: 213/213 (100.0%)
- Active broken concrete linked-file references: 0/213 (0.0%)
- Active high-risk skills by heuristic: 0/213 (0.0%)
- Skills with `## When to Use`: 237/237 (100.0%)
- Skills with verification or Definition of Done: 237/237 (100.0%)
- Skills with minimum eval prompts: 237/237 (100.0%)
- Skills with full routing matrix: 237/237 (100.0%)
- Skills with broken concrete linked-file references: 0/237 (0.0%)
- Skills with placeholder/example linked-file contracts: 7/237 (3.0%)
- High-risk skills by heuristic: 0/237 (0.0%)

Interpretation: this is coverage telemetry, not an automatic rewrite mandate. Pattern labels are candidates until human/agent review confirms semantics.

## Primary pattern coverage

| Pattern | Count | Share |
|---|---:|---:|
| wrapper | 88 | 37.1% |
| pipeline | 70 | 29.5% |
| generator | 41 | 17.3% |
| reviewer | 21 | 8.9% |
| memory | 6 | 2.5% |
| router | 6 | 2.5% |
| monitor | 3 | 1.3% |
| inversion | 2 | 0.8% |

## Risk distribution

| Risk | Count | Share |
|---|---:|---:|
| high | 0 | 0.0% |
| medium | 0 | 0.0% |
| low | 237 | 100.0% |

## Category coverage

| Category | Count |
|---|---:|
| software-development | 64 |
| .archive | 24 |
| creative | 20 |
| mlops | 16 |
| devops | 11 |
| productivity | 11 |
| autonomous-ai-agents | 10 |
| github | 8 |
| research | 7 |
| ui-ux-pro-max | 7 |
| apple | 6 |
| media | 5 |
| smart-home | 5 |
| ui-skills | 4 |
| mcp | 3 |
| social-media | 3 |
| data-science | 2 |
| email | 2 |
| note-taking | 2 |
| api-and-interface-design | 1 |
| chinese-platforms | 1 |
| code-simplification | 1 |
| codebase-intelligence | 1 |
| deprecation-and-migration | 1 |
| diagramming | 1 |
| documentation-and-adrs | 1 |
| dogfood | 1 |
| domain | 1 |
| feeds | 1 |
| framework-audit | 1 |
| gaming | 1 |
| gifs | 1 |
| gsd-bridge | 1 |
| incremental-implementation | 1 |
| inference-sh | 1 |
| loop | 1 |
| p10 | 1 |
| p10-architecture-self-check | 1 |
| p7 | 1 |
| p9 | 1 |
| personal-productivity | 1 |
| post-deploy-verification | 1 |
| pro | 1 |
| red-teaming | 1 |
| source-driven-development | 1 |
| workflow | 1 |

## Most common gaps

| Flag | Count | Share |
|---|---:|---:|

## Broken concrete linked-file references

None detected by backtick-link heuristic.

## High-risk skills to inspect first

None by current heuristic.

## Skills missing minimum eval prompts, sample

None.

## Unclassified skills, sample

None.

## Recommended next actions

1. Do not batch-edit all skills. Use this report as a triage queue.
2. Fix broken linked-file references first; they are silent runtime failures.
3. Pilot 10 representative skills: 2 each from Wrapper, Generator, Reviewer, Inversion, Pipeline.
4. For any skill whose `description` changes, add/refresh `evals/prompts.csv` before committing.
5. Treat high-risk Wrapper skills without read-back signals as safety-priority audits.
6. Promote recurring scan usage into the `agent-skill-design-patterns` skill script; keep generated reports in docs/private.

## Boundary / human intervention

This audit intentionally stops before bulk mutation. Human/owner review is needed before:

- changing many skill descriptions, because descriptions are routing logic;
- deleting or merging skills;
- deciding whether a broken linked reference was intentionally removed;
- labeling a heuristic pattern as canonical metadata for a skill;
- enabling automated routing tests across multiple model families.

## Method limits

- Pattern classification is keyword-based and may over-detect broad workflow words.
- Linked-file detection only catches backtick paths under references/templates/scripts/assets/evals.
- Eval presence is file-coverage only; it does not prove the evals were executed against the active router.
- Verification section presence does not prove verification quality.
