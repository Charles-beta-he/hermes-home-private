# External SDK → Rowboat/Hermes Workflow Tool Integration Pattern

Applicability: use when integrating a third-party SDK or API into a workflow/agent tool surface (for example Rowboat builtin tools, Hermes workflow executors, or background-task agents) where agents will later call the capability programmatically.

Anti-conditions:
- Do not store project-specific IDs, screen IDs, API keys, branches, PR numbers, or one-off task progress here.
- Do not treat read-only smoke tests as authority to perform external writes such as generating/editing remote resources; require a concrete user target or explicit authority for write calls.
- Do not hardcode credentials in source, examples, tests, fixtures, or committed config.

## Procedure

1. Locate the actual tool surface before editing.
   - Identify where agent tools are registered, how schemas are exposed, and how tool availability is gated.
   - Prefer adding a narrow adapter/client module over scattering SDK calls through the tool registry.

2. Add the dependency through the project package manager, not by hand-editing lockfiles.
   - Re-run install if workspace symlinks/dependencies are missing after changing the package graph.
   - Build the dependent workspace package chain, not just the edited package, when generated/dist packages are imported by siblings.

3. Create a small config/client boundary.
   - Read credentials from environment or local user config outside the git workspace.
   - Provide `isConfigured()` and an `isAvailable` tool gate so tools do not appear unusably when credentials are absent.
   - Save local credentials with restrictive permissions where the platform supports it (for example `chmod 600`).
   - Always close/dispose SDK clients in a `finally` path when the SDK keeps network transports open.

4. Expose agent-facing tools at the right abstraction level.
   - Include a setup/config tool only if the app already supports local secret storage.
   - Include read/discovery tools (`list-tools`, `list-projects`, `list-resources`) before write tools.
   - For write-capable SDK methods, preserve provider semantics in the description (for example long-running generation/edit calls should not be blindly retried on timeout if the server may still be working).
   - Return both normalized summaries and raw response when the upstream response shape is broad or evolving.

5. Normalize response shapes defensively.
   - Add helper functions that extract IDs and artifact URLs from known locations but tolerate nested/raw response variants.
   - Deduplicate discovered resources by stable ID.
   - Keep raw payloads available for follow-up debugging.

6. Verify in layers.
   - Build the workspace dependency chain.
   - Run lint if available, but classify pre-existing unrelated lint failures separately from build failure.
   - Smoke-test the SDK through the built artifact, not only TypeScript source.
   - Smoke-test the actual agent tool registry so the new tools are visible and `isAvailable` gates behave.
   - Perform at least one read-only live API call with the provided credential when safe.
   - Search the git workspace for the literal secret and confirm it does not appear in tracked or untracked repo files.

## Verification evidence shape

Report concise evidence like:

- `npm run deps` → shared/core/preload build passed.
- SDK smoke: `configured true`, expected tool names visible.
- Tool registry smoke: new builtin tool names listed and availability true.
- Live read smoke: read-only API call succeeded with count/shape only, not full secret-bearing payload.
- Secret hygiene: workspace literal-secret scan returned empty; local config exists outside repo with restrictive mode.

## Common pitfalls

- Running only a subpackage build before generated/shared workspace outputs exist; the failure is setup order, not necessarily the new integration.
- Letting a foreground-command safety scanner reject shell snippets containing `&`; rewrite the snippet instead of recording a durable tool limitation.
- Treating `npm run lint` failure as integration failure when it reports unrelated legacy lint errors. Still report it, but separate from build/smoke evidence.
- Calling remote create/edit/generate endpoints just to prove a tool exists. Prefer `listTools`/`listProjects` unless the user provided a specific target and granted write authority.
