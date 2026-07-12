# H5 preview parity smoke evidence

Use when a React/Vite H5 or PWA page looks correct on a production/test URL but local dev or `vite preview` shows blank API-backed sections, missing bottom navigation, or unproven mobile route behavior.

## Applicability

- Vite/React H5/PWA running on local dev or `vite preview`.
- API-backed home/market sections can render blank because local origin/port does not match the configured API base.
- Acceptance requires mobile H5 viewport proof, not desktop-width DOM-only proof.
- You need bounded local evidence before push/deploy.

## Anti-conditions

- Do not treat local preview proof as production/test-domain proof; deploy/test-domain needs separate readback.
- Do not claim iOS Safari, Android Chrome, or native WebView safe-area acceptance from headless Chrome alone.
- Do not fabricate authenticated state. If asset/message/customer/scan routes are guarded, anonymous redirect-to-login proof is valid only for anonymous behavior; post-login behavior needs a real session.
- Do not persist task progress or specific project URLs in the skill. Keep those in project SSOT/profile/evidence ledgers.

## Procedure

1. **API base and proxy parity**
   - Inspect the API client and `vite.config.*` together.
   - Prefer same-origin `/api` for Vite dev and local `vite preview` so the exact opened host/port (`localhost`, `127.0.0.1`, alternate dev ports) can use the proxy.
   - Configure both `server.proxy` and `preview.proxy` when `vite preview` is used for local H5 acceptance.
   - Verify the exact user-reported URL, not a nearby one.

2. **Mobile viewport proof**
   - Use mobile dimensions such as 375x812, 390x844, and 414x896.
   - Capture both screenshot evidence and structured DOM/geometry readback.
   - For bottom TabBar/safe-area checks, assert all tab labels are visible, each button rect is inside the viewport, nav bottom equals viewport bottom, and no error text is present.
   - Add `height: calc(64px + env(safe-area-inset-bottom, 0px))` plus `padding-bottom: env(safe-area-inset-bottom, 0px)` only when the bottom bar is fixed and could underlap mobile home indicators.

3. **Route smoke for anonymous tabs/actions**
   - Drive real browser clicks, not only router config inspection.
   - Record route readback and active-state readback (`aria-current` where available).
   - Public tabs should land on their route; protected tabs/actions should redirect to Login in anonymous mode if that is the route guard contract.
   - State explicitly that authenticated route behavior remains a separate gate until a valid session is available.

4. **Banner/navigation parity**
   - First read the live banner payload. If it has image URLs but no `appRedirectUrl`, `redirectUrl`, or `link`, runtime click should remain on the current page; that is payload-bound evidence, not proof that redirect logic executed.
   - Add a fixture-level smoke for redirect utilities: owned absolute URL appends context, relative URL remains relative, third-party URL is unchanged/no token leak, and `appRedirectUrl` priority beats `redirectUrl`/`link`.
   - Capture negative token-leak evidence by checking captured request URLs for `?token=`/`&token=` where relevant.

5. **Evidence and closure wording**
   - Store evidence under a scoped project evidence directory, not in memory.
   - Commit code changes and evidence in small scoped commits when project policy allows local commits.
   - Completion wording must be bounded: `local H5 preview runtime-verified` is not `production certified`.
   - If a verifier vote is pending, report `not certified yet` with a DecisionPacket/ContinuationPacket rather than claiming full closure.

6. **Loop-certified local packet freshness**
   - For `certified` / `全量验收` requests, promote the smoke evidence into a deterministic local loop command when feasible, for example `npm run certify:h5:local`.
   - The loop should validate tracked evidence files, scoped lint, build, API/smoke JSON semantics, and write a machine-readable latest + timestamped report.
   - Do not generate the final report before the plan/script/evidence are tracked and then treat that report as current. A report that embeds `git status` with `M ...` or `?? ...` from before commit is an AMEND-worthy stale-evidence packet.
   - Add an explicit `workingTreeCleanAtGeneration` (or equivalent) check derived from `git status --short --branch`: ignore the first branch/ahead line, but fail/warn on any modified or untracked worktree entries. Note that branch ahead count may legitimately change after committing the report.
   - Independent verifier AMENDs should be resolved by rerunning the loop after the fix and committing the refreshed report, not by narrative explanation.

## Minimal evidence packet

- Target URL and viewport.
- API curl/readback for the exact local `/api` path if API blankness was the issue.
- Screenshot(s) for the mobile viewport.
- JSON smoke output with route/geometry/error-text checks.
- Lint/build commands and exit status.
- Boundaries: real device, WebView, authenticated session, production/test-domain, push/deploy, and independent verifier status.
