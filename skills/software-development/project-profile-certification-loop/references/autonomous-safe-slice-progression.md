# Autonomous safe-slice project progression

Use this reference when a user authorizes ongoing local progress for a mobile/H5 parity project, but high-side-effect gates must remain closed.

## Applicability

- A project profile and SSOT exist.
- The user wants autonomous progression beyond one slice.
- Safe local actions are allowed: source edits, local smokes, screenshots, SSOT evidence, scoped lint/build, local commits, verifier dispatch.
- The project has a backlog or capability graph that can select the next slice without user decomposition.

Anti-conditions:

- Do not use this as authorization for push, deploy, production/test-domain mutation, credential entry/extraction, real payments/orders/funds mutation, destructive git history rewrites, or external fanout.
- Do not claim device/auth/PWA/production certification without corresponding evidence.
- Do not turn this into a global background daemon unless the user separately authorizes cron/mission/taskpool durable automation.

## Project profile shape

Add a project-scoped switch, not global memory:

```json
{
  "autonomous_progression": {
    "enabled": true,
    "mode": "local-safe-slice-autonomy",
    "authorized_scope": [
      "local H5 code edits",
      "Hermes SSOT evidence/profile/ledger writes",
      "mobile viewport smoke/screenshot",
      "scoped lint/build",
      "local git commit",
      "independent verifier dispatch"
    ],
    "hard_stop_gates": [
      "push",
      "deploy",
      "production/test-domain mutation",
      "credential/password/token/session extraction or entry",
      "real order/payment/funds mutation",
      "destructive history rewrite/delete",
      "external fanout",
      "device/auth/PWA certification claim without evidence"
    ],
    "queue_policy": "select next safe slice by backlog priority + evidence gap + touched surface + hazard inventory + authority boundary; continue while safe local reversible slices remain"
  }
}
```

Write a small receipt under `ssot_root/receipts/` and link it from the profile.

## Execution loop

1. Read `git status --short --branch`, project profile, backlog, and hazard inventory.
2. Select the next safe slice by priority and evidence gap. Prefer anonymous/read-only/local-verifiable route or UI semantics before auth/device/PWA gates. For route/page-level candidates, do a cheap auth-boundary preflight before investing in edits: if the local H5 route redirects to `/Login` or requires credentials/session state, mark it as gated and choose another auth-free slice instead of patching and then rolling back.
3. Record the selected slice in the session todo.
4. Inspect native reference and H5 target files before editing.
5. Make the smallest scoped product-code patch.
6. Verify with changed-file lint, build, and a mobile viewport runtime smoke. For UI/route work, generate SSOT JSON plus screenshot.
7. Update backlog and progress ledger in SSOT, not the app repo.
8. Commit only product code when changed.
9. Run the local certification loop if present.
10. Dispatch a read-only independent verifier before upgrading to L3.
11. Treat verifier dispatch as a background side-effect, not a stopping point: after the dispatch returns, immediately run next-slice selection and keep progressing if repo/preview are healthy and no hard gate is reached. Do not final-report merely because a verifier is now pending.
12. If verifier APPROVE, write bounded verdict and continue the next safe slice. If AMEND, fix blocker first.
13. Do not end a turn immediately after a verifier receipt when the project has an enabled safe-slice autonomy switch and repo/preview readbacks are healthy. First run a next-slice selection pass; only final-report if no auth-free/fixture-free local slice remains or a hard stop gate is reached.
14. When the selection pass finds no remaining auth-free/fixture-free local slice, write an explicit authority-boundary packet instead of calling the work “continued” or “root cause fixed”. The packet must include fresh repo status/HEAD, routes or actions preflighted, why each remaining lane is gated, the exact authority/evidence needed to open each lane, and what remains allowed without more authority (read-only audits, SSOT planning, pending verifier receipts).
15. If a user asks why autonomy stopped, classify the stop before acting: (a) workflow bug with safe work still available -> briefly acknowledge and execute the next safe slice in the same turn; (b) clean-window/verifier hygiene -> pause WIP, write stale-AMEND receipt, re-dispatch, and keep repo clean; (c) true authority boundary -> write/read back the boundary packet and ask for/offer exact gated lanes. Do not present (c) as an automation failure or pretend to keep editing.

## Evidence packet requirements

- `gitStatus` clean except branch ahead.
- commit hash and changed files.
- evidence JSON paths and screenshot paths.
- a timestamped per-slice loop report path; keep `latest` pointers only as convenience, not identity proof for older target commits.
- fresh command results: lint/build/smoke/cert-loop.
- negative gates: no real order, no credential/session/token read, no production mutation.
- open boundaries: push/CI, auth/session, Android/iOS/WebView, PWA install/standalone, deploy domain.

## Verifier queue hygiene

See `references/verifier-clean-window-retries.md` for the full stale-AMEND clean-window retry procedure, receipt shape, retry verifier brief, and L3 promotion checklist.

- When dispatching verifiers while autonomy may continue, brief them with target-commit ancestry and clean worktree conditions, not fixed ahead counts: target commit X must be contained in current clean HEAD; branch may be further ahead due later committed safe slices.
- Include the timestamped loop report for the target slice. Do not ask verifiers to use `local-h5-loop-latest.json` as identity proof for an older slice; it may point to a later committed slice.
- When processing an async APPROVE, do a fresh local readback before writing the L3 verdict: current `git status --short --branch`, current HEAD, target commit ancestry, and target commit changed-file scope. The verifier may have run at an older HEAD/ahead count; L3 promotion should bind the approval to the current clean repository slice.
- After writing an APPROVE verdict, immediately update all three SSOT surfaces in the same operation where possible: project profile, parity/backlog item, and progress ledger. Then run next-slice selection before ending if autonomy is enabled and no hard gate is reached.
- For same-file autonomous queues, keep each new slice as a clean commit boundary with its own timestamped loop report before dispatching a verifier. This permits older verifiers to approve by target-commit ancestry even as HEAD advances.
- If repeated stale-AMENDs occur for the same file, pause new WIP in that file until the retry verifier gets a clean read window, or switch only to non-conflicting files/surfaces. Continuing same-file WIP can make every retry fail for cleanliness even when the product slice is valid.
- Classify dirty-tree AMENDs caused solely by later uncommitted safe-slice work as stale-environment AMEND: write a receipt, keep the target at L2, re-dispatch after a clean commit, and do not treat it as a product blocker.

## Pitfalls

- Stopping after one safe slice despite the user authorizing autonomy. If another safe local reversible slice exists, continue; only stop at a concrete authority/evidence boundary or verifier blocker.
- Misdiagnosing a legitimate authority boundary as a repeated “autonomy stopped again” bug. When anonymous/local safe slices are exhausted, the root fix is not more editing; it is an authority-boundary packet with exact gated options and required evidence. Persist it in SSOT/profile/backlog so future turns do not re-litigate the same stop.
- Saying “root cause fixed” after patching the loop but before proving the terminal state. A fix is only complete when either a subsequent safe slice is executed, or a named boundary packet proves why no further safe slice may run without new authority.
- Treating async verifier receipts as the whole queue. After writing APPROVE/AMEND receipts and L3 verdicts, immediately re-read repo/preview health and run next-slice selection before final-reporting; otherwise verifier-drain becomes an accidental stop condition.
- Treating verifier dispatch or a user-facing explanation as a stop point. If the user asks “why did you stop?” or otherwise flags stalled autonomy, answer only as much as needed, then immediately execute a fresh safe slice in the same turn when repo/preview are healthy. A report that says “I will continue” but stops after dispatching a verifier has not fixed the workflow.
- Creating avoidable stale-AMEND churn by continuing WIP in the same file while old verifier briefs expect an exact clean ahead count. If autonomy continues, either pause at clean commit boundaries for verifier results or brief verifiers that HEAD may advance and target commits only need to be ancestors of the current clean HEAD.
- Verifier briefs for autonomous safe-slice queues must not make a fixed ahead count or fixed HEAD hash an approval condition unless the work is intentionally paused. Use this shape instead: “target commit X must be contained in current clean HEAD; `git status --short --branch` must have no changed files; branch may be further ahead due later committed safe slices.” If a verifier sees a dirty tree caused only by a later uncommitted safe slice, classify it as stale-environment AMEND, write a receipt, re-dispatch after clean commit, and do not treat it as a product blocker.
- Do not use `local-h5-loop-latest.json` as identity proof for older slices in verifier briefs or verdicts. Always include the target slice's timestamped loop report path; `latest` is only a convenience pointer and may have advanced while autonomous work continued.
- Keep runtime smoke assertions tied to the bounded claim, not incidental UI internals. If a safe slice only certifies that a control became a semantic button and toggles `aria-pressed`, do not fail the smoke because an unrelated input disabled state did not change; record the observed state, assert the intended semantic/negative gates, then continue.
- For MUI Slider accessibility smokes, inspect the rendered DOM before locking assertions. The accessible control may be a visually hidden `input[type="range"]` carrying `aria-label`, `min`, `max`, and `value`, not an element with `role="slider"`. If the first smoke misses the target, run a small DOM inventory and update the assertion to the intended accessible node rather than retrying the same failing query.
- Reporting a root-cause fix for autonomy without exercising it. A valid fix should update the governing skill/profile/SSOT receipt and then prove the new behavior by completing at least one subsequent safe local slice or stopping at a named hard gate.
- Treating local autonomy as a durable background service. CLI-session autonomy is not cron/mission/taskpool unless separately created.
- Letting smoke scripts depend on undeclared packages. Prefer Node built-ins when available, or add a setup step in the script evidence; do not assume `ws` or Playwright exists.
- Writing smoke outputs into the application repo. Keep Hermes evidence in SSOT.
