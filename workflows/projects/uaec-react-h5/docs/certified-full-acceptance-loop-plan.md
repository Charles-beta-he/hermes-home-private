# UAEC React H5 Certified Full Acceptance Loop Plan

> For Hermes: execute this as a loop-engineering workflow, not as a one-off checklist. Each loop must produce machine-readable evidence, update the progress ledger, and stop only at a concrete authority/evidence boundary.

## Goal

Move `uaec-react-h5` toward "certified / 全量验收完成" by repeatedly closing the strongest safe local evidence gaps first, while keeping production, push, credentials, real-device, and authenticated-session gates explicit.

## Objective model

### Success criteria

A claim may be upgraded only when the matching evidence class exists:

1. Local H5 preview runtime verified:
   - exact local URL readback;
   - same-origin `/api` preview proxy works;
   - mobile viewport smoke proves no blank home/market sections;
   - route smoke proves public/anonymous guarded behavior;
   - targeted lint and build pass;
   - evidence files are tracked in git.
2. Certified local H5 packet:
   - all local evidence above;
   - deterministic loop script passes from a clean working tree or documents only allowed local SSOT/doc changes;
   - independent verifier vote is `APPROVE` or all `AMEND` items are resolved by readback;
   - converge matrix maps every claim to evidence.
3. Full production / real-device certified:
   - local packet plus test/prod-domain deployment readback;
   - real iOS Safari / Android Chrome / WebView proof where safe-area or native shell behavior is claimed;
   - authenticated-session route smoke for protected pages;
   - explicit push/deploy authority, rollback, and post-action verification.

### Hard constraints / non-goals

- Do not push or deploy without exact target authorization.
- Do not type, store, or fabricate credentials/tokens/sessions.
- Do not claim authenticated behavior from anonymous redirect evidence.
- Do not claim production/test-domain or real-device acceptance from local headless Chrome.
- Do not hide known baseline failures such as full-repo lint issues.
- Do not remove existing routes, fields, auth state, or H5 flows to make certification easier.

## Certification levels

| Level | Name | Required evidence | Current boundary |
|---|---|---|---|
| L0 | Draft / plan only | plan exists | not enough for completion |
| L1 | Local evidence collected | individual evidence files exist | evidence may be stale/untracked |
| L2 | Local loop verified | deterministic script validates evidence + lint/build | local-only, not prod/device/auth |
| L3 | Local certified packet | L2 + independent verifier approve + converge matrix | still no push/prod/device/auth unless separately done |
| L4 | Shared branch certified | L3 + authorized push + remote/CI/readback | needs push authority |
| L5 | Full production/device certified | L4 + real domain + real device/WebView + authenticated smoke | needs env/session/device/rollback |

Current target for this workflow is L3 first. L4/L5 require separate human gates.

## Loop engineering workflow

Each loop is one small, reversible slice:

1. Intake
   - read `git status --short --branch`;
   - read `docs/certified-full-acceptance-loop-plan.md` and progress ledger;
   - classify remaining gaps into safe-local vs authority/evidence-boundary.
2. Plan next slice
   - pick the highest-certification-impact safe-local gap;
   - define acceptance and negative cases;
   - list exact evidence files and commands.
3. Execute
   - code/doc/script changes only if needed;
   - keep changes scoped and reversible;
   - no push/deploy/secret entry.
4. Verify
   - run the deterministic loop command;
   - run any targeted browser/API/visual smoke needed by the slice;
   - write machine-readable evidence under `evidence/certification/` or the slice evidence folder.
5. Converge
   - map every material claim to evidence;
   - record blockers as `needs-user-target`, `needs-human-secret`, `needs-real-device`, `needs-external-push`, or `needs-backend-payload`.
6. Commit
   - commit scoped local files when policy allows;
   - update ledger before completion claims.
7. Review
   - dispatch independent verifier for L3 upgrade;
   - resolve AMEND items with readback, not narrative.

## Current evidence matrix

| Claim | Evidence | Status | Boundary |
|---|---|---|---|
| Local preview `/api` blank-list fix works | `evidence/2026-07-09-h5-api-preview/home-ranking-api-response.json`, `home-ranking-preview-127-4173-390x844.png` | pass | local preview only |
| Home top anonymous interactions route correctly | `evidence/2026-07-09-slice2/home-top-click-route-smoke-390x844.json` | pass | authenticated post-login routes need session |
| Bottom TabBar safe-area visible in mobile viewport matrix | `evidence/2026-07-09-slice3/tabbar-safe-area-smoke.json`, PNGs | pass | true iOS/WebView safe-area needs device |
| Bottom tabs route in anonymous mode | `evidence/2026-07-09-slice4/tab-route-smoke-390x844.json` | pass/tracked | asset authenticated behavior needs session |
| Banner runtime current payload is safe | `evidence/2026-07-09-slice1/banner-runtime-smoke-390x844.json` | pass | current backend payload has no redirect target |
| Banner redirect helper respects token boundary | `evidence/2026-07-09-slice1/banner-navigation-fixture-smoke.json` | pass | real redirect-banner click needs backend payload |
| Build and scoped lint pass | loop command output | required every loop | full-repo lint baseline still fails |
| Independent verifier approval | delegation result | pending/recheck | model vote is advisory until objective evidence cited |

## Deterministic local loop command

Run:

```bash
npm run certify:h5:local
```

Expected:

- exits 0;
- runs scoped eslint and `npm run build`;
- validates all known evidence JSON files;
- verifies required evidence files are tracked by git;
- writes:
  - `evidence/certification/local-h5-loop-latest.json`
  - `evidence/certification/local-h5-loop-<timestamp>.json`

## Converge matrix template

| Acceptance claim | Code/doc evidence | Command evidence | Runtime/API/UI evidence | Status | Remaining gap |
|---|---|---|---|---|---|
| ... | ... | ... | ... | pass/warn/fail | ... |

## Stop gates

Stop and produce a DecisionPacket when the next action requires:

- pushing to remote, opening/merging PR, deploy, or production/test-domain mutation;
- account credentials, token/session injection, payment, or secret entry;
- real-device/WebView access not available locally;
- backend changing the live banner payload or API behavior;
- destructive cleanup, route removal, schema/data migration, or broad fan-out.

## Resume protocol

1. Read this file.
2. Read `/Users/charles/.hermes/workflows/projects/uaec-react-h5/progress-ledger.md`.
3. Run `git status --short --branch`.
4. Run `npm run certify:h5:local`.
5. If it passes and no safe local gaps remain, dispatch/consume independent verifier and update the converge matrix.
