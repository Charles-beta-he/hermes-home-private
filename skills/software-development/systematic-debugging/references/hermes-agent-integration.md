# Systematic Debugging Hermes Agent Integration

Extracted from `/Users/charles/.hermes/skills/software-development/systematic-debugging/SKILL.md` on 2026-07-01T08:52:42.874486+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## Hermes Agent Integration

### Development iceberg scans

Applicability: use for software development debugging or change-impact work where a visible symptom, requested file, route, field, API, branch, or PR may hide coupled failures in adjacent surfaces. Anti-condition: do not use this section to import project-specific facts, branch names, repository names, product domains, credentials, or local paths into a global rule; resolve concrete surfaces from the active project profile and current repo each time.

“Iceberg scan” means the visible symptom/file is only the entry point. Expand to hidden coupled surfaces before choosing the fix point, but keep the expansion bounded by task risk and evidence.

Intervention timing:

1. **Intake / before implementation** — run a light iceberg scan when the request mentions a bug symptom, UI screenshot, reference-platform parity, API contract, auth/token, money/precision/order/status/time, permission, cache/service worker, notification/message center, routing/deep link, or release/deploy behavior. Goal: choose the correct landing point and avoid single-file assumptions.
2. **After first reproduction / root cause hypothesis** — run a medium scan when the bug reproduces or a suspected fix point appears. Goal: build producer → transformer → consumer → guard/test map before editing.
3. **After a fix touches shared code** — run a targeted blast-radius scan when editing request wrappers, auth interceptors, stores, route guards, global hooks, caches, i18n, config, or shared components. Goal: catch secondary surfaces activated by the fix.
4. **Before commit/PR/merge** — run a pre-merge iceberg scan when the user asks for “iceberg scan / hidden issue scan / same-batch check”, auto-merge, release readiness, or when recent adjacent commits touch the same runtime surface. Goal: decide what belongs in the current PR vs follow-up.
5. **After deployed behavior differs from source** — run a deployed-behavior iceberg scan: branch tip semantics → deployment metadata → served artifacts → browser/client cache → backend/data state.

Scan decomposition:

- **Source/requirement layer**: current user/task/doc/prototype/profile and conflict resolution.
- **Entry/UI layer**: route, menu/tab/card/deep-link, visible text, empty/loading/error states.
- **State/adapter layer**: store, normalizer, fallback/defaults, i18n, feature flags, local/session storage.
- **Contract layer**: service wrapper, request signer/interceptor, API params/envelope, backend/controller when available.
- **Side-effect layer**: auth/session refresh, telemetry, audit, notification, cache/service worker, sockets, background jobs.
- **Persistence/runtime layer**: database/migrations, deployment config, static assets, CDN/browser/client cache, native bridge or reference-platform boundary.
- **Verification layer**: existing tests, missing regression case, browser/API evidence, build/lint, device/reference parity.

Depth ladder:

- L0 Narrow lookup: answer from named file only when no related surface can change truth.
- L1 Light scan: named file + direct imports/usages + route/API wrapper.
- L2 Contract scan: producer/consumer + adapter/store + request/backend contract + focused tests.
- L3 Runtime scan: browser/network/deploy/cache/service-worker/socket/telemetry evidence.
- L4 Batch/release scan: adjacent commits, branch/deploy metadata, clean worktree dry merge, test/build gates.

Stop conditions:

- Stop when the hidden-surface map is closed enough for the task’s risk class and every remaining uncovered surface is explicitly listed.
- Do not expand into unrelated modernization. Fix in-scope findings; record adjacent out-of-scope issues as follow-up.
- If three attempted fixes reveal new coupled surfaces, stop patching and question the architecture before another fix.

Output contract:

- Trigger: why iceberg scan was needed.
- Scope/depth: L0-L4 and surfaces checked.
- Finding table: surface, evidence path/command, severity, in-scope vs follow-up.
- Chosen fix point and why lower/higher layers were not chosen.
- Verification evidence and uncovered surfaces.

### Pre-merge iceberg scans

When the user asks to auto-merge a PR and then requests a broader “冰山扫描” or same-batch commit check, pause the merge, define the batch scope, scan adjacent commits and deployment/config surfaces, and only fold in-scope fixes into the PR. Keep unrelated findings as follow-up work. See `references/pre-merge-iceberg-scan.md`.

### Investigation Tools

Use these Hermes tools during Phase 1:

- **`search_files`** — Find error strings, trace function calls, locate patterns
- **`read_file`** — Read source code with line numbers for precise analysis
- **`terminal`** — Run tests, check git history, reproduce bugs
- **`web_search`/`web_extract`** — Research error messages, library docs

### With delegate_task

For complex multi-component debugging, dispatch investigation subagents:

```python
delegate_task(
    goal="Investigate why [specific test/behavior] fails",
    context="""
    Follow systematic-debugging skill:
    1. Read the error message carefully
    2. Reproduce the issue
    3. Trace the data flow to find root cause
    4. Report findings — do NOT fix yet

    Error: [paste full error]
    File: [path to failing code]
    Test command: [exact command]
    """,
    toolsets=['terminal', 'file']
)
```

### With test-driven-development

When fixing bugs:
1. Write a test that reproduces the bug (RED)
2. Debug systematically to find root cause
3. Fix the root cause (GREEN)
4. The test proves the fix and prevents regression
