---
name: project-profile-certification-loop
description: Use when a project needs an evidence-gated local certification or closure loop without polluting the application repository with progress ledgers, temporary reports, screenshots, or workflow scripts. Store project state in Hermes project profile/SSOT and keep the repo limited to product code and durable product docs.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [certification, project-profile, ssot, evidence, workflow, closure]
    related_skills: [abstraction-governance, project-evidence-grounding, development-closure-consensus, mobile-frontend-delivery]
---

# Project Profile Certification Loop

## Overview

Use this workflow to run a repeatable local certification loop for a software project while keeping progress state out of the application repository. The application repo should contain product code, product-facing docs, tests that belong to the product, and durable source assets. Hermes-owned progress ledgers, screenshots, smoke outputs, certification reports, verifier packets, and loop runner scripts should live under the project's Hermes profile/SSOT.

Default SSOT shape:

```text
~/.hermes/project-profiles/<project-id>.json
~/.hermes/workflows/projects/<project-id>/progress-ledger.md
~/.hermes/workflows/projects/<project-id>/docs/
~/.hermes/workflows/projects/<project-id>/evidence/
~/.hermes/workflows/projects/<project-id>/scripts/
```

The loop may read and verify the repo, but it writes reports to SSOT unless the user explicitly asks for repo-local evidence.

## When to Use

- User asks for certified/full acceptance, closure, loop engineering, or evidence-gated delivery.
- Progress/evidence artifacts are starting to appear in the application repo.
- A project needs cross-session resumability through a project profile rather than stale global memory.
- You need to reuse a certification loop across projects with project-specific manifests.

Do not use for:

- Product tests that are intended to run in CI and belong in the repo.
- Product documentation/ADRs that the development team should version with source.
- One-off smoke checks that do not need durable state.
- Secret, token, session, or credential storage; redact those and never write them to SSOT.

## Objective Model

Before writing anything, classify each artifact:

| Artifact | Default landing zone |
|---|---|
| App source changes | application repo |
| CI/product tests | application repo |
| Product ADR/API/user docs | application repo |
| Progress ledger | Hermes project SSOT |
| Screenshots/manual smoke outputs | Hermes project SSOT |
| Certification reports/verdicts | Hermes project SSOT |
| Loop runner scripts | Hermes project SSOT or reusable skill template |
| Project-specific manifest/config | project profile or SSOT |
| Cross-project procedure | skill |

Success criteria:

1. The project profile names `ssot_root` and `progress_ledger`.
2. The app repo stays clean of Hermes progress/evidence artifacts.
3. The loop can be rerun with an explicit repo path.
4. The report cites concrete commands, evidence files, blockers, and open gates.
5. Closure claims distinguish local certification from remote, authenticated, device, deploy, or production certification.

## Workflow

1. Resolve project identity.
   - Read `~/.hermes/project-profiles/<project-id>.json`.
   - Confirm `primary_repo`, `ssot_root`, and `progress_ledger`.
   - If missing, create or update the project profile before running a long loop.

2. Build the SSOT directories.

```bash
mkdir -p ~/.hermes/workflows/projects/<project-id>/{docs,evidence,scripts,receipts}
```

3. Move existing progress artifacts out of the repo.
   - Copy first, then remove from repo.
   - Preserve evidence under `ssot_root/evidence/`.
   - Remove package scripts that only run Hermes certification workflows unless they are intended product CI.
   - Commit repo cleanup separately with a message such as `chore: move certification artifacts to project profile`.

4. Parameterize the loop runner.
   - Accept the app repo path as an argument.
   - Use repo cwd only for readback commands: git status, build, lint, tests, browser smoke.
   - Write reports to `ssot_root/evidence/...`, not `<repo>/evidence`.
   - Include `workingTreeCleanAtGeneration` or equivalent to prove no dirty repo progress artifacts.

5. Run the loop.
   - Prefer smallest relevant checks: scoped lint/build/smoke for the changed slices.
   - Parse existing evidence files and fail closed on missing/invalid evidence.
   - Emit JSON with `ok`, `blockers`, `certificationLevel`, command tails, and open gates.

6. Independent verification.
   - Ask a read-only verifier to inspect the repo, profile pointers, SSOT report, and git cleanliness.
   - Include the expected clean-state snapshot in the verifier brief: target commit, current HEAD, expected `git status --short --branch`, and whether later local commits are allowed. If autonomous safe-slice work will continue while the verifier runs, say explicitly that HEAD may advance and the target commit only needs to be an ancestor of the current clean HEAD.
   - Treat APPROVE as upgrade only for the bounded certification level under review.
   - Treat AMEND as a blocker only when it points to the target slice, evidence, loop, or current clean readback. If AMEND only reports a dirty working tree caused by later concurrent safe-slice work, classify it as a stale-environment AMEND, write an SSOT receipt, do not promote, and re-dispatch a fresh read-only verifier against the current clean repo instead of rewriting product code.
   - If the verifier has been dispatched but has not returned, do not call the slice certified or complete. Record the local evidence level, keep the verification gate open, and hand off a DecisionPacket/ContinuationPacket with pending vote, rollback path, and next verification command.
   - For async verifier AMENDs caused only by stale concurrent dirty worktrees, use `references/async-verifier-stale-amend.md`: write a stale-AMEND receipt, keep the slice at L2, and re-dispatch a fresh verifier against the current clean repo instead of changing product code or treating the stale vote as L3 evidence.

7. Update the profile and ledger.
   - Project profile stores current level, latest report, verifier verdict, open gates, and progress-storage policy.
   - Progress ledger records what was verified and what remains blocked.
   - Do not save task progress to global memory.

8. Abstract only the transferable part.
   - Project-specific commands/evidence stay in profile/SSOT.
   - The reusable procedure belongs in this skill or an adjacent skill reference.
   - Candidate future automation can become an experience-ratchet proposal, not direct global policy.

9. Avoid hardcoded autonomous triggers.
   - Do not route only from exact words like `certified`, `closeout`, or one project name.
   - Store project `workflow_capability_tags` and hazard inventory in the project profile/SSOT.
   - Trigger the loop from tag + touched surface + evidence gap + authority boundary.
   - For mobile H5/PWA projects, use `references/mobile-h5-hazard-manifest.md` to capture reusable hazards such as keyboard focus, scroll-owner, safe-area, bottom-tab shell, route guards, and API-backed blank sections.

10. Enable project-scoped safe-slice autonomy when explicitly authorized.
   - Use `references/autonomous-safe-slice-progression.md` to store a local safe-slice switch and receipt in the project profile/SSOT.
   - Continue through safe local reversible slices after verifier APPROVE instead of stopping after one green slice.
   - Do not let mid-run status reports interrupt automation. Report only on concrete gate/blocker, final convergence, verifier AMEND, or when a human decision/authority is required; otherwise keep draining the next safe slice.
   - Keep push/deploy/credential/real-order/production/external gates closed until exact target + rollback + readback are supplied.
   - For mobile/browser smoke loops, see `references/mobile-cdp-safe-slice-smoke.md` for fresh-preview/profile, post-click baseline, and WIP rollback patterns.
   - For concurrent verifier and preview notifications during autonomous safe-slice work, see `references/concurrent-verifier-hygiene.md` for stale dirty-tree AMEND classification, SSOT receipts, fresh verifier redispatch, fresh APPROVE resolution, evidence redaction, and non-blocking preview SIGTERM checks.
   - For repetitive verifier drains, reuse or copy helpers from `scripts/verifier_drain_helpers.py` to standardize git readbacks, query redaction, stale-AMEND receipts, and L3 verdict skeletons.

## Certification Levels

Use bounded labels:

- L0 plan-only: plan exists; no loop run.
- L1 evidence-collected: evidence exists but not loop-validated.
- L2 local-loop-verified: deterministic local loop passed.
- L3 local-certified-packet: L2 plus independent verifier APPROVE or resolved AMEND.
- L4 shared-branch-certified: pushed branch/PR plus remote/CI readback.
- L5 environment/device-certified: deployed/test/prod URL, auth/session, real device/WebView, rollback/readback.

Never call L2/L3 “full production certified”.

## Loop Runner Contract

A reusable runner should produce at minimum:

```json
{
  "generatedAt": "...",
  "repoRoot": "...",
  "ssotRoot": "...",
  "certificationLevel": "L2-local-loop-verified",
  "boundedClaim": "local-only...",
  "gitStatus": "## branch...",
  "workingTreeCleanAtGeneration": true,
  "commands": [],
  "checks": [],
  "blockers": [],
  "boundaries": [],
  "ok": true
}
```

Recommended checks:

- repo status readback;
- repo clean at generation;
- required SSOT evidence exists;
- scoped lint/build/test commands pass;
- evidence JSON semantic checks pass;
- negative requirements have negative evidence;
- open gates are explicit.

## Common Pitfalls

1. Writing screenshots, smoke JSON, certification reports, or verifier packets into the application repo just because the code under test lives there.
2. Adding `npm run certify:*` to the app repo when the command is a Hermes project-profile workflow rather than a product CI contract.
3. Treating an old report generated before commit cleanup as proof of current cleanliness.
4. Confusing repo `ahead` count with dirty state; check modified/untracked/index entries separately.
5. Treating a verifier AMEND from a stale concurrent workspace as a product defect. When later safe-slice work made the tree dirty during verification but the target slice/evidence was OK, record the stale AMEND in SSOT and re-dispatch against a fresh clean readback.
6. Upgrading from local loop certification to production/device/full certification without remote/deploy/auth/device evidence.
7. Saving project progress to global memory; use project profile/ledger instead.
8. Abstracting local project paths or evidence filenames into a global skill instead of parameterizing them.
9. Treating autonomous progress as hardcoded trigger words. For ongoing parity/closure work, route from capability tags, touched surfaces, hazard inventory, evidence gaps, and authority boundaries.
10. Creating a readable plan but no executable backlog. For continuing work, maintain SSOT indexes/backlog/matrix packets so the next safe slice can be selected without the user repeatedly decomposing tasks.
11. Repeating the same failing verification command until a tool guardrail blocks it. If a smoke probe fails, split diagnostics, inspect generated expressions/logs, and change the command signature before retrying.
12. Writing L3 verdicts from stale-AMEND receipts alone. A stale dirty-tree AMEND can be classified and re-dispatched, but L3 requires a fresh APPROVE or a resolved objective AMEND with current readback.
13. Letting SSOT evidence or replies preserve raw quasi-credential identifiers from URLs/request summaries. Redact trade/session/token/API-key-like fields before durable verdicts or user-facing summaries.

## Verification Checklist

- [ ] Project profile has `ssot_root`, `progress_ledger`, and certification pointers.
- [ ] Application repo contains no Hermes-only `evidence/`, certification reports, or loop scripts unless explicitly intended.
- [ ] Loop runner accepts an explicit repo path and writes reports to SSOT.
- [ ] Latest loop report is read back from SSOT and has `ok: true` or clear blockers.
- [ ] `git status --short --branch` is read back after cleanup.
- [ ] Independent verifier result is recorded before claiming L3.
- [ ] L4/L5 gates are listed separately and not implied by L2/L3.
