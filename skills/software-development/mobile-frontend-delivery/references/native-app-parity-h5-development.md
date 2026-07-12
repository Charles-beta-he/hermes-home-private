# Native-app parity for H5/Web development

Use when a user asks for a React/Vue/PWA/H5 frontend to match an existing Android/iOS app 1:1 in business logic, scenarios, and user-perceived UX.

## Applicability

- A native app source tree is available and is the business/scenario reference.
- The web/H5 app already exists and must preserve current routes, APIs, and auth state.
- The user wants an independently organized plan, not merely execution of an issue tracker.
- There is a develop-equivalent branch target and feature-branch development is expected.

Anti-conditions:

- Do not apply as a visual-only style transfer; use a design/pixel-parity skill for that.
- Do not store project-specific branch names, domains, tokens, or API paths in the class skill; keep those in the project profile or a scoped task SSOT.
- Do not claim full 1:1 completion from one slice; only the verified slice is complete.

## Procedure

1. Establish a compact parity spec before editing:
   - Goal and non-goals.
   - Native reference hierarchy: which native files/classes/routes are authoritative.
   - H5 implementation surface: routes, layout shell, API/service layer, state stores.
   - Web adjustments: browser/PWA permissions, safe area, routing, external-link handling, cache/SW behavior.
   - Red lines: auth state machine fields, money precision fields, route preservation, token/link safety.
   - Evidence gates: build, targeted lint/type check where possible, runtime screenshot/readback, negative checks.

2. Branch correctly:
   - Discover the actual develop-equivalent branch (`develop`, `dev`, etc.) from remote branches.
   - Create a feature branch from that remote baseline.
   - Commit the feature slice, then merge locally into the develop-equivalent branch.
   - Do not push or remote-merge unless the user explicitly authorized the exact target.

3. Build a native-to-H5 surface map:
   - App shell/nav: native tab/fragment/activity graph -> H5 route modules, layout, bottom nav.
   - Home/discovery: native header/banner/shortcut/ranking logic -> H5 page + service + API.
   - Market/trading/assets/security/settings: native class groups -> H5 page/service/API/store files.
   - For each row, record Android/iOS source, H5 target, data model, entry points, and required evidence.

4. Pick the first slice by low blast radius and high reference confidence:
   - Prefer one small cross-cutting parity behavior such as banner navigation, external-link context, safe empty states, or shell navigation.
   - Avoid starting with a large trading/order-state rewrite until the reference map is stable.

5. Code with browser-safe native adaptation:
   - Support native response fields in H5 types without removing existing H5 fields.
   - Keep native destination priorities when they encode business intent (for example native `appRedirectUrl` over generic `link`).
   - For WebView-like context parameters, append auth/session context only to same-origin or owned domains. Never add tokens to third-party external links.
   - Replace crash-on-missing-data assumptions with visible empty/loading/error fallbacks for nonstandard or unavailable API responses.
   - Preserve native auth boundaries before adapting controls: anonymous collect/favorite/order/asset actions should route to login before mutation APIs or password/order flows, and the smoke should include negative evidence for no forbidden API after the click.
   - Use semantic browser controls for H5 equivalents of native tappable actions (`button`, labels, disabled/loading states) instead of clickable `div`s when the action is a submit/login/route boundary.
   - Add mobile input hints for numeric trading fields (`inputMode`, `pattern`, autocomplete policy) without changing money precision logic or backend decimal-string handling.

6. Verify narrowly and honestly:
   - Run the smallest relevant build command.
   - Run targeted lint/type checks for changed files if full lint/typecheck is polluted by unrelated existing errors.
   - If full lint/typecheck fails, report it as existing/repo-wide only after changed-file checks pass.
   - Use a fresh preview origin/port or clear SW/cache when validating PWA build output, because old service workers can keep showing stale runtime errors.
   - Capture browser screenshot/readback for visible UI changes; do not rely on code review alone.

## Pitfalls

- Treating Lark/Jira/GitLab issues as the plan when the user asked for native-app parity. Issues are evidence, not the execution model.
- Copying native mechanics literally when browser/PWA constraints require an equivalent user-perceived behavior instead.
- Adding token/session parameters to third-party banner links.
- Destructuring nested API metadata before checking it exists; local previews, proxies, and degraded gateways often return nonstandard bodies.
- Claiming UI completion from `vite build` only. At minimum, visually smoke the route after the build.
- Forgetting stale PWA/service-worker state during preview validation; use a fresh port/origin or explicit cache/SW reset.
- Applicability: browser-based native-parity smoke tests for nested surfaces such as drawers, sheets, modals, and popovers. Do not let a harness failure masquerade as product proof: if the harness cannot reliably open the surface or identify the intended control, repair the harness or revert the WIP slice instead of committing unproven behavior.
- Applicability: negative side-effect checks in auth/order/favorite/payment-like flows. Measure forbidden APIs after a pre-action baseline, not across the whole page-load request list; initial read-only data requests are not proof that the click caused a mutation.

## Verification checklist

- [ ] Native reference files and H5 target files are named in the slice plan.
- [ ] Develop-equivalent branch was discovered from git, not guessed from user wording.
- [ ] Feature branch was based on the develop-equivalent remote branch.
- [ ] Existing H5 fields/routes/state names were preserved.
- [ ] Owned-domain and third-party external-link behavior were tested separately when tokens are involved.
- [ ] Build passed.
- [ ] Changed-file lint/type gate passed, or the exact blocker was documented.
- [ ] Browser screenshot/readback shows no blocking runtime error banner for the changed route.
- [ ] Merge target and push status are reported explicitly.
