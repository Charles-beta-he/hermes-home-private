# Mobile CDP safe-slice smoke patterns

Use this reference when a project-profile certification loop validates mobile H5/PWA slices with Chrome DevTools Protocol or a similar browser harness.

## Landing-zone classifier

- Reusable procedure / debugging path / verification checklist: keep here or in the parent SKILL.md.
- Project-specific URLs, ports, trade ids, evidence paths, branches, screenshots: keep in the project profile/SSOT, not in this reference.
- Transient stale-build or profile failures: do not memorialize as “the tool is broken”; capture the retry/freshness pattern.

## Procedure

1. Build first, then restart preview when validating built output.
   - After `npm run build`, a long-running preview can serve old chunks or keep stale service-worker/profile state.
   - Prefer a fresh preview process or a fresh origin/profile before treating a browser failure as product evidence.

2. Use fresh browser profiles for each smoke when state matters.
   - Generate a unique `--user-data-dir` per smoke run, or clear the prior profile before retrying.
   - This avoids stale chunks, cached login/logout state, old service workers, and previous route state leaking into the current slice.

3. Select the intended DevTools page target explicitly.
   - Do not pick the first `/json` target; choose the app URL/origin expected for the smoke.
   - Browser extensions/background pages can otherwise produce misleading JS evaluation or screenshot failures.

4. Treat old preview-exit notifications as a freshness check, not an automatic blocker.
   - When a background preview process exits with SIGTERM during iterative smoke work, it may be an older intentionally killed/stale preview while a newer preview is still serving the port.
   - Before restarting or reporting a blocker, read the process list and run a health probe against the expected local URL/port.
   - If another tracked preview is running and the health probe returns OK, continue using it; restart only when no live preview remains or the health probe fails.
   - This avoids turning normal preview churn into false blockers or unnecessary restarts.

5. For negative side-effect checks, establish a post-ready baseline.
   - Let the page finish initial read-only data requests.
   - Record `baselineRequestCount` immediately before the user action under test.
   - Assert no forbidden mutation/order/collect/password requests appear after that baseline, rather than filtering the whole page-load request list.

6. Make UI preconditions prove the intended element, not a broad container.
   - Narrow selectors by visible bounds, role/label, text, and expected geometry.
   - Avoid clicking a full-width parent that contains the desired text but has no business interaction handler.
   - If a drawer/modal cannot be opened reliably by the harness, do not land product changes against that unproven surface; either repair the harness first or revert the WIP slice.

7. Regress neighboring safe slices after a UI primitive change.
   - Example classes: semantic button conversion, keyboard input attributes, login boundary, route roundtrip.
   - Re-run the smallest existing CDP smokes that exercise adjacent route/auth/form behavior.

8. Keep failed exploratory changes reversible.
   - If eslint/build/smoke cannot prove the slice after diagnostic changes, restore the WIP before moving on.
   - Commit only after product code, scoped checks, smoke JSON, screenshot/readback, SSOT updates, and local certification are coherent.

## Verification checklist

- [ ] Fresh build or dev server state chosen intentionally.
- [ ] Fresh browser profile or cleared profile when cache/auth/SW can affect result.
- [ ] DevTools target matched the app origin, not a background page.
- [ ] If a preview process exit notification appeared, current process list and URL health probe were read before restarting/reporting a blocker.
- [ ] Action target selector is scoped to the actual visible interactive element.
- [ ] Negative API checks are measured after a pre-action baseline.
- [ ] Screenshot/readback shows no runtime error page.
- [ ] WIP product changes are reverted if the smoke cannot reliably reach the surface.
- [ ] SSOT evidence records both positive and negative requirements without secrets or raw tokens.
