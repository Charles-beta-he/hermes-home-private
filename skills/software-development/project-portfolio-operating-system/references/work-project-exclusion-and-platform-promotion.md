# Work-project exclusion and vertical-to-platform promotion

Scope: portfolio governance when a user separates work/client projects from personal/self-advancing projects, or when a narrow vertical product should become a broader platform direction.

Applicability:
- User says a project is a work project and should only advance when explicitly selected.
- Portfolio execution order mixes work projects with self-owned projects and needs a default queue correction.
- A project named after its first use case has accumulated shared platform capabilities and should be reframed as a platform plus first vertical.

Anti-conditions:
- Do not cancel, archive, or mutate task lifecycle merely because a project is work-only; this is an execution-policy change unless the user explicitly asks for task mutations.
- Do not copy business facts, credentials, auth/session state, or private data from work projects into the platform project.
- Do not claim the platform is production/released because the framing changed; require existing evidence gates.
- Do not rename repos or project IDs casually; preserve stable IDs and add a product-model/platform-framing field when IDs are already referenced by ledgers/tasks.

## Procedure

1. Classify the project queue.
   - `work/on-demand`: excluded from autonomous portfolio advancement; resume only when the user explicitly switches context or names the project.
   - `platform/control-plane`: safe local advancement can continue under existing side-effect gates.
   - `vertical/application`: advance only through its own evidence/authority boundaries.

2. Land metadata, not broad side effects.
   - Update project profile execution policy.
   - Update portfolio registry role/status.
   - Append an execution-order addendum or decision note.
   - Keep taskpool lifecycle untouched unless the user explicitly authorizes lifecycle mutations.

3. Reframe vertical-to-platform when evidence supports it.
   - Identify shared capabilities already present: shared core package, gateway/projection, multi-end entry, RN/PWA shells, rollback proof, model/router contract, UI verification, etc.
   - State the new abstraction as `Platform core -> shell(s) -> local assistant/handoff -> vertical modules`.
   - Preserve the original vertical as `first_vertical`, not the whole product boundary.

4. Preserve authority boundaries.
   - Platform mobile/edge clients should not become canonical fact sources unless a separate architecture decision and proof exists.
   - Mobile/offline verticals may store local projections, drafts, selected evidence, and handoff queues, but not write canonical memory/tasks/facts or external side effects offline.
   - External release, push/deploy, device distribution, credentials, payment, destructive cleanup, and broad fan-out remain exact-target gates.

5. Verify after metadata changes.
   - JSON parse changed profiles/registry.
   - Run portfolio doctor and strict verify when available.
   - Run taskpool selfcheck if execution ordering can affect dispatch.
   - Report the distinction between metadata policy landed vs implementation/release not performed.

## Output pattern

Use concise language:

```text
Accepted: work projects are dormant by default; platform/control-plane projects continue.
Project X is now framed as Platform Y; original use case Z is first vertical.
Landed: profile/registry/status metadata only.
Not done: no task lifecycle mutation, no code push/deploy/release, no cross-project secret/fact merge.
Next safe slice: ...
```
