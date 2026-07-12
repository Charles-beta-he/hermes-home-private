# PWA Web Push branch-aligned backend verification

Use when debugging a PWA/Web Push issue and the user names a shared backend branch such as `test`, `staging`, or a release branch as the source of truth.

## Applicability

- Existing frontend PWA/Web Push code calls backend endpoints such as `/platform-config/push` and `/me/push-subscription`.
- The local checkout is dirty, stale, on a gone feature branch, or otherwise not a trustworthy representation of the shared branch.
- The user corrects the target branch, e.g. “backend should pull latest test; user app is PWA-based.”

Anti-conditions:

- Do not use this to bypass required production deploy/runtime evidence.
- Do not treat code presence on a branch as proof that system notifications work; real push delivery still requires configured VAPID/provider credentials, HTTPS, browser permission, service worker registration, and a device/browser smoke test.
- Do not overwrite or pull into a dirty worktree. Use a clean temporary worktree from the remote ref.

## Procedure

1. **Protect dirty worktrees.** Inspect status, then fetch/prune. If the checkout is dirty or on a stale/gone branch, create a clean worktree from the shared ref instead of pulling in place:
   - `git fetch origin --prune`
   - `git worktree add -b work/<topic>-<branch> /tmp/<repo>-<topic>-<branch> origin/<branch>`
   - Immediately verify the new location with `git -C /tmp/<repo>-<topic>-<branch> status -sb` and an ancestry check against `origin/<branch>`.
   - **Execution-location pitfall:** `git worktree add` does not move the current shell. Run every later install/test/build with the new worktree as tool `workdir`, `git -C`, or explicit `cd ... &&`; output from the original checkout is not branch-aligned evidence.
2. **Inspect the exact remote branch.** Read endpoints, service classes, migrations, and dependencies from the clean worktree or directly from `origin/<branch>`, not from the dirty local branch.
3. **Separate notification transports before blaming a pending request.** Applicability: notification settings coexist with foreground streaming/polling and browser Web Push. A long-lived foreground stream may remain pending by design; trace the toggle's awaited chain separately: platform config → permission → service-worker registration/readiness → subscription lookup/create → backend registration → preference write. Prove which promise fails to settle. Anti-condition: do not use stream duration alone as evidence that the toggle is blocked.
4. **Verify Service Worker liveness, not only presence.** If normal registration is deferred until page load plus idle time, a user can reach settings before registration begins. The user-initiated push path should explicitly start the same idempotent registration routine before awaiting readiness. Put bounded, stage-specific deadlines around readiness and subscription operations; return diagnostic statuses and leave the backend preference disabled on timeout. Do not merely increase one page-level timeout.
5. **Verify the frontend/backend contract together.** Confirm frontend PWA code uses:
   - `PushManager.subscribe(...)`
   - explicit/idempotent Service Worker registration before `navigator.serviceWorker.ready`
   - bounded handling for browser promises that may never settle
   - `Notification.requestPermission()` only behind user action
   - `GET /platform-config/push`
   - `POST/DELETE /me/push-subscription`
   - service worker `push` and `notificationclick` handlers

   Confirm backend provides matching:
   - public push config endpoint
   - authenticated register/unregister subscription endpoints
   - dedicated subscription storage for `endpoint + p256dh + auth + deviceInstallId + vapidKeyVersion`
   - VAPID/Web Push delivery service
   - notification preference gating
   - dispatch after durable in-app notification creation/commit
6. **Separate code readiness from environment readiness.** Report branch code status separately from required environment variables/config, for example provider=`webpush`, VAPID public/private keys, VAPID subject/key version, web click base URL, and HTTPS deployment.
7. **Run narrow verification gates.** Minimum useful gates:
   - RED tests where Service Worker readiness and browser subscription creation never settle; use controllable deferred promises/fake timers, then assert bounded diagnostic results and absence of backend registration/preference writes
   - backend targeted module test for VAPID/key utilities or Web Push service behavior
   - backend compile of the push-serving module with dependencies, executed from the clean branch worktree
   - frontend push unit tests, notification-settings state tests, service-worker contract tests, lint, and production build
   - full suite; if unrelated failures occur, reproduce the same failure from a second clean `origin/<branch>` worktree before calling it pre-existing
8. **State platform boundaries.** Android/Desktop PWA can work through browser Web Push; iOS requires iOS/iPadOS 16.4+ Home Screen PWA and must not be promised for a normal Safari tab. Force-stop, notification permission denial, and aggressive OEM battery policy can still prevent delivery.

## Reporting shape

Report in four blocks:

- Shared branch readback: repo, remote ref, commit, clean worktree path.
- Contract evidence: frontend endpoints/SW path and backend endpoint/storage/dispatch path.
- Verification output: exact commands and pass/fail counts.
- Remaining runtime boundary: deploy target, env vars, VAPID rotation, and real-device push/click smoke.

## Pitfalls

- A local dirty feature branch can make a present backend endpoint look absent. Always verify the user-named remote branch before diagnosing a missing API.
- A generated service worker plus in-app notification sync is not background push unless the SW has `push` handling and the browser has a real `PushSubscription` registered with the backend.
- Do not store Web Push subscriptions in a single legacy `push_token` field. Browser Web Push needs endpoint and key material; native FCM/APNs token storage is a separate channel.
- Do not put sensitive finance details in lock-screen/system push payloads. Use push as a wake-up pointer and fetch details via authenticated APIs after open/click.
