# Skill Library Change Efficiency Report

Generated: 2026-06-07T19:55:31
Before: `eb80bebc1bf9`
After: `5e759f860969`

## Executive Summary

Verdict: **PASS**

- Positive gap units closed: **183**
- Changed files: **45**
- Changed lines: **16928** (16827 insertions, 101 deletions)
- Gap units closed per changed file: **4.067**
- Gap units closed per changed line: **0.01081**

Interpretation: this was intentionally a broad governance/coverage pass. The direct line-efficiency ratio is low because the commit also added a complete coverage report JSON and reference playbooks. The operational efficiency is high for the target gaps: all measured P1/P2/P3 omission classes reached zero in one scoped commit, with recursive submodule verification restored.

## Before / After Metrics

| Metric | Before | After | Closed |
|---|---:|---:|---:|
| skill_count | 230 | 237 | n/a |
| active_count | 211 | 213 | n/a |
| bad_yaml | 2 | 0 | 2 |
| duplicate_names | 2 | 0 | 2 |
| bad_eval | 31 | 0 | 31 |
| stock_boilerplate | 26 | 0 | 26 |
| backticked_template_refs | 5 | 0 | 5 |
| scanner_high_risk | 80 | 0 | 80 |
| scanner_broken_refs | 32 | 0 | 32 |
| scanner_placeholder_contracts | 5 | 0 | 5 |
| scanner_full_matrix | 199 | 237 | n/a |

## Scanner Runtime

- Before scan: 0.225s
- After scan: 0.261s

## Diff Cost

- Files changed: 45
- Insertions: 16827
- Deletions: 101

Large insertions are mostly generated/archival evidence and playbook references: `docs/private/skill-omission-fix-20260607/skill-pattern-coverage.json`, coverage markdown, `.gitmodules`, and new skill-governance reference files. They are not all prose rewrites.

## Submodule Verification

- `git submodule status --recursive` exit code: 0
- Runtime: 1.617s

## Efficiency Judgment

- Outcome efficiency: PASS — all targeted omission classes closed.
- Regression efficiency: PASS — frontmatter/eval/name/link/submodule checks all pass after the change.
- Cost efficiency: MIXED — line churn is high because a full coverage JSON artifact was committed; if optimizing repository weight, keep future scan JSON as runtime artifact unless audit history must be versioned.

## Recommendation

For future full-library governance passes, split into two commit classes: (1) semantic/contract changes and (2) generated reports. That preserves auditability while making code review and efficiency measurement cleaner.
