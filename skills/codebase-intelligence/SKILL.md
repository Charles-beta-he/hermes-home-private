---
name: codebase-intelligence
description: Use when analyzing codebase structure, before refactoring, assessing change impact, extracting reference-architecture patterns from one codebase to improve another without direct integration, or mapping codebase design patterns to CS/math theory with formal models and academic references.
version: 1.0.0
author: Hermes Agent
license: MIT
triggers:
- what imports this
- blast radius
- impact analysis
- dead code check
- call chain
- before modifying shared packages
- theoretical foundations
- abstract principles from code
- formal model of system
- academic references for architecture
metadata:
  hermes:
    tags:
    - codebase
    - analysis
    - blast-radius
    - imports
    related_skills:
    - source-driven-development
    - code-simplification
    - github-code-review
---

# codebase-intelligence

## Overview


Use `code-intel.py` — a pure Python stdlib tool that provides GitNexus-like analysis without npm dependencies.

## When to Use

- Analyzing codebase structure, before refactoring, or assessing change impact
- what imports this
- blast radius
- impact analysis
- dead code check
- call chain
- before modifying shared packages
- **Theoretical framework synthesis**: user asks for "theoretical foundations", "abstract principles", "formal model", "academic references" for a system's architecture → use `references/theoretical-framework-synthesis.md`
- **Template/data contract debugging**: rendered email/notification/PDF/SMS/push/in-app content shows raw placeholders, empty fields, or partially rendered data → use `references/template-data-contract-debugging.md` and trace screenshot/content → template source → sender vars → renderer behavior → data providers.

## Quick reference

| Task | Command |
|------|---------|
| Hermes self-analysis | `python3 ~/.hermes/scripts/code-intel.py summary` |
| TS project import graph | `python3 ~/.hermes/scripts/code-intel.py import-graph --repo /path` |
| Blast radius | `python3 ~/.hermes/scripts/code-intel.py blast-radius --repo /path --file X` |
| Call chain (TS) | `python3 ~/.hermes/scripts/code-intel.py call-chain --repo /path --function F` |
| Python import deps | `python3 ~/.hermes/scripts/code-intel.py import-graph` |

## Capabilities

- **Python**: AST-based import/from analysis (stdlib ast module)
- **TypeScript/JavaScript**: Regex-based import/export/function detection
- **Monorepo-aware**: Resolves relative imports, package aliases
- **Zero dependencies**: Only Python stdlib
- **Fast**: 500 files in ~5s

## Known limitations

- TS/JS regex parser cannot resolve pnpm monorepo workspace aliases (e.g., `@tg/core`). Use `grep -rl "@tg/core"` as fallback.
- No tree-shaking analysis (dead exports within a file).
- No type-level dependency tracking (TypeScript interfaces/types).

## Linked reference
- `references/template-data-contract-debugging.md` — iceberg-search workflow for rendered artifact defects: trace visible placeholders/partial data back through template source, sender variable map, renderer missing-var semantics, data providers, and post-render guardrails.
- `references/notification-system-taxonomy-analysis.md` — reusable checklist for analyzing notification/message-center systems: category taxonomy, sub-type inference, tab filtering, row rendering, impact routing. Pair with project-specific detail files.
- `references/uvisa-notification-system.md` — UVISA notification architecture: type fields, category taxonomy, inference regexes, tab structure, i18n keys, impact router, UX gap (all transactionType badges same green color).
- `references/theoretical-framework-synthesis.md` — multi-model dispatch pattern for mapping codebase design patterns to CS/math theory, finding academic references, building formal models, and verifying properties. Use when user asks for "theoretical foundations", "abstract principles", or "academic works" for a system.
- `references/prototype-source-to-current-codebase-mapping.md` — how to convert a cloned prototype/demo repo plus current frontend/backend repos into durable project-profile navigation and domain landing maps.
- `references/backend-existing-frontend-unwired-analysis.md` — how to classify backend logic as already wired, directly wireable without UI change, requiring backend orchestration, requiring UI change, or out of module scope.
- `references/uvisa-payout-fee-display.md` — UVISA payout screen architecture: two screens (PayoutUsdtScreen vs PayoutCryptoScreen), `feeDisplay`/`feeOf` logic, backend BigDecimal→string flow, Lark 401531e0 unit-append bug and test coverage, debugging checklist for bare-number fee display.
- `references/uvisa-payment-pin-verification-coverage.md` — UVISA-only map for `/api/auth/pin/verify` and `/me/payment-pin/verify`: direct callers, `/pay/verify/pin` transitive coverage, encrypted field behavior, backend DTO/docs checks, and pitfalls around new `type`/`purpose` fields. Use only for UVISA tasks and re-verify current code before claims.
- `references/uvisa-exchange-fee-architecture.md` — UVISA FX exchange fee flow: dual-fee model (channel fee explicit + platform spread implicit), quote→confirm phases, `pairOpt.isPresent()` branching bug, fee-displayed-but-not-deducted pattern, math verification checklist.
- `references/uvisa-currency-architecture.md` — UVISA currency data flow: admin registry → currencyService → Zustand store → useRegistry() → consumer pages (home/topup/payout/exchange). FIAT vs CRYPTO kind, exchange picker FIAT-only rule, ALL_CCYS fallback anti-pattern, adding-new-currency checklist.
- `references/uvisa-email-notification-templates.md` — UVISA email notification two-layer architecture: hardcoded Java title/body strings + DB HTML shell templates (Flyway seed). Key insight: message content is NOT in templates or admin config — it's in Java call sites. Covers all payout notification variants, debugging checklist.
- `references/uvisa-i18n-audit.md` — UVISA i18n audit patterns: frontend key namespaces (order.timeline.*, order.channel.*), BizException→ErrorCode→MessageSource error flow, TransactionAggregationService hardcoded Chinese timeline descriptions, failReason untranslated upstream errors, channel translation accuracy, audit shell commands.
- `references/uvisa-payment-pin-verify-contract.md` — UVISA-scoped mapping/checklist for C-side payment PIN verify coverage: `/auth/pin/verify` vs `/me/payment-pin/verify`, `type` scene metadata, `purpose=phone-rebind`, and TDD verification points.

## Workflow: backend exists but frontend/admin is not wired

When the user asks which backend logic already exists but is not connected to a frontend/admin module, especially under a "do not change UI/functionality" constraint:

1. Read the target page/component to identify actual interactions and current service calls.
2. Read the frontend service module to enumerate wrappers/endpoints, then search usages to verify whether each wrapper is actually used by the target module.
3. Read backend controllers and permission annotations for matching endpoints.
4. Classify each candidate as: already wired, directly wireable without UI change, backend-orchestration needed, UI/feature change required, or out of module scope.
5. Treat local mock/fallback helpers, in-memory audit, hard-coded dates, and toast-only actions as likely wiring gaps, but only call them direct gaps after mapping them to a backend capability.
6. If an endpoint needs sensitive fields not present/safe in the UI (e.g. full card number) or has different permission semantics, do not recommend browser direct wiring; recommend keeping the UI unchanged and wrapping orchestration behind the existing domain endpoint.

See `references/backend-existing-frontend-unwired-analysis.md` for the detailed checklist and reporting format.

## Workflow: before modifying a shared package

```
# 1. Know what you're touching
python3 code-intel.py blast-radius --repo . --file packages/core/src/crypto.js

# 2. Search for workspace alias references (monorepo)
grep -rl "@tg/core" apps/ --include="*.js" --include="*.jsx"

# 3. List all affected files
# 4. Run tests on affected packages only
# 5. Proceed with change
```

## Reference Architecture Gap Analysis

When the user wants to improve a target system based on another repo (not integrate it), follow `references/reference-architecture-gap-analysis.md`: set a non-integration boundary, extract class-level patterns, create a gap matrix, land target-system artifacts, and verify them. Do not claim live integration or feature parity unless explicitly implemented.

When the user corrects or supplies the authoritative GitHub URL, verify the exact repository before continuing: clone or query the GitHub API, record canonical repo metadata and commit hash, read repository-local agent instructions, then inspect the source files behind the claimed capabilities. If an earlier task/log used the wrong source, explicitly append corrected evidence rather than silently reusing the old analysis.

Linked reference: `references/agentmemory-reference-architecture.md` captures the source-verified AgentMemory patterns for shared local memory servers, hook-driven capture, layered retrieval, supersession/versioning, retention/audit/privacy governance, and Hermes-specific cautions.

Linked reference: `references/bytebot-desktop-agent-reference.md` captures source-verified Bytebot patterns for containerized desktop agents, REST/MCP computer-use action spaces, takeover traces, explicit NEEDS_HELP/NEEDS_REVIEW task states, and safety gates before Hermes adoption.

Linked reference: `references/local-codegraph-advisory-evaluation.md` captures the local code-graph/indexer spike pattern: source pinning, isolated cache, runtime compatibility notes, fixed retrieval-case comparison against `search_files`/direct reads, multi-root caveats, cleanup, and the rule that graph output is advisory rather than truth evidence.

## Cross-Repo Architecture Reconnaissance

When user asks about "mobile files", "native packaging", "Capacitor", or platform-specific artifacts that don't exist in the named repo, follow `references/cross-repo-architecture-recon.md`: check all branches, scan sibling repos in workspace, identify tech stacks (Flutter/RN/Capacitor/native), and report with the structured template. Never assume the mobile app uses the same framework as the web project.

## Common Pitfalls

1. Loading this skill outside its trigger class and skipping a simpler, more direct path.
2. Ignoring prerequisites such as platform, credentials, installed commands, or linked reference files.
3. Treating the skill as a static memo instead of verifying the exact commands, artifacts, or outputs in the current environment.
4. **Assuming a web project's mobile counterpart uses the same tech stack.** Always scan sibling repos and check for Flutter (pubspec.yaml), React Native (metro.config.js), or native (build.gradle) before concluding.

## Verification Checklist

- [ ] The task actually matches this skill's trigger class and the current route is still appropriate.
- [ ] All prerequisites, linked references, templates, scripts, and required tools have been checked before execution.
- [ ] Claimed outputs, commands, files, or external side-effects were read back or otherwise verified before completion.
- [ ] Reviewer calibration: findings include a severity or rubric boundary and cite evidence.
