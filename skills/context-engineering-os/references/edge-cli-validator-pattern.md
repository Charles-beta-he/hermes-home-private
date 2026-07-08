# Edge CLI Validator Pattern for Context Engineering OS

Applicability: use when a Context Engineering / Context Packet capability has already been proven as a local script or SSOT artifact and the next safe advancement is Hermes integration.

Anti-conditions: do not use this pattern to mutate the runtime prompt, agent loop, taskpool lifecycle, cron, gateway delivery, external adapters, publish/deploy/push, credentials, or destructive operations. Those require separate exact authority, rollback/readback, and tests.

## Pattern

1. Keep the first Hermes integration at the edge.
   - Add a local-only CLI surface such as `hermes context packet lint <packet.json>` or `hermes context eval run --root <project-root>`.
   - The command should parse/read/validate and print readback; it should not call an LLM or write lifecycle state.

2. Reuse the deterministic validator contract.
   - Keep validation dependency-light where practical.
   - Validate objective, sources/evidence linkage, selected context, authority closure/readback, negative cases, and learning boundary.
   - Accept legacy packet shapes only when needed for backward compatibility, but keep the stricter current shape documented.

3. Test the CLI before claiming integration.
   - Add parser/dispatch tests for the new command.
   - Add PASS fixture tests and FAIL fixture tests for evidence drift, missing readback, and missing do-not-save / learning boundary.
   - Run the targeted test with the repository venv when global `pytest` is unavailable; do not record global command absence as durable learning.

4. Run real command readback.
   - After tests pass, invoke the actual installed/development `hermes context ...` command against the SSOT sample and fixture root.
   - Capture stdout in the SSOT/evidence document before reporting completion.

5. Commit in the correct landing zones.
   - Commit Hermes code changes in the Hermes source repo.
   - Commit SSOT/profile/skill reference changes in the profile/home repo if it is separate.
   - Keep commits scoped; do not stage unrelated logs, cron output, or task progress.

## Verification checklist

- [ ] CLI parser accepts the intended subcommand and arguments.
- [ ] Targeted tests pass.
- [ ] `py_compile` or equivalent import/syntax check passes for new modules.
- [ ] Real `hermes context ...` readback passes against the SSOT sample.
- [ ] Regression eval includes at least one expected-pass and one expected-fail fixture.
- [ ] Boundary statement explicitly says no runtime prompt mutation, no lifecycle write, no external dispatch, and no scheduler enablement.

## Pitfall

Do not skip from local script directly to runtime prompt injection. For Hermes core, prompt caching is a high-value invariant and the agent loop is a narrow waist; use an edge validator first, then consider a default-off runtime preflight gate only after cache-safe tests exist.
