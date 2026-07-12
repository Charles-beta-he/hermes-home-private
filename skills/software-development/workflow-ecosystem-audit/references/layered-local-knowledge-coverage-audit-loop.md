# Layered Local-Knowledge Structure and Coverage Audit Loop

## Applicability

Use when auditing a Markdown-first local brain, knowledge vault, workflow SSOT, or similar system whose “coverage” may mean several different things at once: document presence, navigation, schema, links, runtime retrieval, tests, freshness, governance, or closure.

Anti-conditions:
- Do not collapse these dimensions into one composite percentage unless the denominator and weighting were agreed in advance.
- Do not bulk-fill metadata, expiry dates, statuses, or evidence boundaries merely to make validation green.
- Do not treat fixture validation, static docs, or isolated unit tests as proof of live runtime integration.
- Project-specific paths and counts belong in the audit artifact/profile, not in this reusable procedure.

## Objective model

Before mutation, capture:
1. success criteria: structure inventory, measurable coverage, gaps, and fresh readback;
2. SSOTs: canonical content, registry/routing, derived indexes, dashboards, task lifecycle;
3. non-goals: no status fabrication, no proof reconstruction, no unsafe bulk rewrite;
4. evidence requirements: file readback, command output, tests, negative checks, and explicit OPEN claims.

## Coverage dimensions

Keep separate rows for:

| Dimension | Typical evidence |
|---|---|
| Canonical structure | top-level index, directory inventory, SSOT declaration |
| Registry/routing | registered brains/profiles validate and resolve |
| Metadata/schema | notes with required frontmatter divided by scoped denominator |
| Link integrity | parsed internal links, broken links, placeholder classification |
| Retrieval index | index exists, fresh timestamp, indexed block count |
| Runtime read path | real adapter query, bounded projection, source/hash binding |
| Test coverage | focused assertions and negative tests, not filename counts |
| Dashboard/projection | regenerated snapshot agrees with canonical scan |
| Governance | expiry/evidence-boundary/policy validators |
| Closure/certification | fresh receipts and explicit authority boundary |

## Audit loop

### 1. Discover breadth without trusting capped searches

Count files recursively or partition by top-level directory. Search caps prove only a lower bound. Find canonical indexes, architecture docs, coverage matrices, registries, runtime adapters, tests, dashboards, and audit scripts.

### 2. Read authority documents first

Read the root index, project architecture, read-path contract, registry, health dashboard, and outstanding backlog before scoring. Record which document is normative versus derived or historical.

### 3. Establish deterministic baselines

Run structural validation, registry validation, index status, focused tests, and any exhaustive link/secret audit. Record exact denominators and timestamps. Keep “validator passed” distinct from “runtime integrated.”

### 4. Classify broken links honestly

Distinguish:
- real internal broken links;
- template placeholders that should not be parsed as links;
- absolute runtime artifact paths that are external to the vault;
- historical evidence that no longer exists.

Repair syntax/classification without inventing missing artifacts. Historical unavailable evidence should remain explicitly unavailable rather than masquerading as a live vault link.

### 5. Refresh derived projections in dependency order

When authorized and reversible:
1. rebuild the derived retrieval index;
2. read back index timestamp/count;
3. run canonical validation;
4. regenerate the dashboard from validator output;
5. read the dashboard back.

A fresh dashboard may legitimately show FAIL. Freshness PASS is not governance PASS.

### 6. Add a live adapter selfcheck under TDD

If unit/fixture checks exist but no live readback is visible:
1. write a failing test for a small injectable selfcheck;
2. exercise the real read adapter with a bounded query;
3. project only path/heading/hash/score, excluding excerpts/content from authority-bearing receipts;
4. require at least one valid hash-bound result;
5. sanitize errors to type/category;
6. include a negative adapter-failure test;
7. expose the result in the main selfcheck without silently upgrading it to execution authority.

This proves adapter reachability and projection safety, not global chat/provider integration.

### 7. Separate profile-contract warnings from task failures

Missing project profile policy blocks may be repaired as scoped configuration when the user requested local control-plane advancement. Reuse established neighboring profile shapes, preserve existing profile content, validate JSON/schema, then rerun semantic selfcheck. Do not infer external-write permission from policy completeness.

### 8. Inventory remaining debt instead of bulk fixing

Emit a machine-readable debt inventory grouped by decision class, for example:
- active L3 expiry requiring human/domain review;
- canonical schema backfill;
- review evidence-boundary backfill;
- fixture/evidence scope exception candidate;
- terminal/archive legacy.

The grouping is an audit aid, not automatic mutation authority.

### 9. Converge claim by claim

For every material claim, map:
- code/config/document evidence;
- fresh test/command/readback evidence;
- PASS, OPEN, BLOCKED, or N/A.

Negative requirements need negative evidence: no dispatch, no lifecycle transition, no external send, no secret leakage, malformed inputs fail closed.

## Pitfalls

1. Reporting “300 Markdown files” when the search hit its 300-result cap.
2. Treating 100% registry validation as 100% system coverage.
3. Calling a fixture benchmark a live retrieval E2E.
4. Declaring dashboard health from a fresh timestamp while ignoring validator failures.
5. Removing broken evidence paths without preserving their historical-unavailable meaning.
6. Checking raw search hits for authority neutrality when the real contract is the sanitized projection; verify both raw validity and projected field exclusion.
7. Editing a profile from a stale read after another controller changed it; reread immediately before the scoped patch.
8. Turning concrete follow-up engineering work into a skill instead of a taskpool/proposal candidate.

## Verification checklist

- [ ] Every percentage has a numerator, denominator, scope, and timestamp.
- [ ] Canonical, derived, runtime, test, and certification claims are separate.
- [ ] Structural audit includes link and secret checks.
- [ ] Index and dashboard freshness were read back after regeneration.
- [ ] Live read selfcheck uses the real adapter and bounded hash-bound projection.
- [ ] Adapter failure and authority-neutral negative cases pass.
- [ ] Profile/schema changes were reread and revalidated.
- [ ] Remaining validator debt is machine-readable and classified, not hidden.
- [ ] Converge matrix contains explicit OPEN claims.
- [ ] No external side effect or lifecycle mutation was inferred from advisory/read-only health.
