# H5 certification loop engineering

Use when a React/Vite H5 local-preview parity task needs to move from scattered smoke evidence toward a bounded `certified / 全量验收完成` claim.

## Applicability

- The project already has slice evidence such as API readbacks, mobile viewport screenshots, route-smoke JSON, safe-area geometry checks, or banner/navigation fixture checks.
- The user asks for `certified`, `全量验收完成`, `全盘推进`, or repeatable workflow execution rather than a one-off fix.
- Local proof is allowed, but push/deploy/session/real-device authority may still be closed.

## Anti-conditions

- Do not use this pattern to claim production, real-device, WebView, or authenticated acceptance from local headless/browser evidence.
- Do not treat a model/verifier vote as evidence unless it cites objective file/command readbacks.
- Do not store project-specific URLs, branches, commit hashes, or session progress in this skill; keep those in the project ledger/profile.

## Certification levels

Use explicit levels so wording cannot outrun evidence:

| Level | Meaning | Typical gate |
|---|---|---|
| L0 | plan only | no completion claim |
| L1 | evidence collected | evidence may be stale/untracked |
| L2 | local loop verified | deterministic script validates evidence + scoped lint/build |
| L3 | local certified packet | L2 + independent verifier approve or resolved amend + converge matrix |
| L4 | shared branch certified | L3 + authorized push + remote/CI/readback |
| L5 | production/device certified | L4 + deployed URL + real device/WebView + authenticated smoke |

## Deterministic loop script pattern

Create a project-local command such as `npm run certify:h5:local` that:

1. Reads `git status --short --branch` and records it in the report.
2. Uses `git ls-files <evidence...>` to prove required evidence files are tracked, not merely present locally.
3. Runs scoped eslint for files touched by the H5 parity/certification slices.
4. Runs the project build.
5. Parses JSON evidence and validates material claims, for example:
   - API response has success meta and expected rows;
   - anonymous route smokes have `ok: true` and no error text;
   - safe-area matrix has all target viewports passing and nav/buttons inside viewport;
   - banner runtime smoke has no token-bearing third-party leaks;
   - banner redirect fixture covers owned, relative, third-party, and priority branches.
6. Writes both:
   - `evidence/certification/local-h5-loop-latest.json`
   - `evidence/certification/local-h5-loop-<timestamp>.json`
7. Exits non-zero on blockers.

## Verifier amend pattern

If an independent verifier returns `AMEND` because evidence is untracked or stale:

1. Fix the objective blocker with a readback (for example stage/commit the evidence, then `git ls-files` it).
2. Re-dispatch a narrow verifier asking only whether the blocker is resolved.
3. Do not upgrade to L3 until the amended item is objectively resolved and recorded in the converge matrix.

## Closure wording

Safe wording:

- `L2 local H5 loop verified`
- `local H5 preview runtime evidence packet validated`
- `not production/device/auth certified`

Unsafe wording unless the matching gates exist:

- `full certified`
- `production ready`
- `real iOS/WebView verified`
- `authenticated flow verified`

## Ledger update

Record the loop command, report path, certification level, blocker count, and remaining authority gates in the project progress ledger before any completion claim.