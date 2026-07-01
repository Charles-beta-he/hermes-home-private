# Hermes CLI Integration Pattern for Portfolio OS

Use this reference when promoting Portfolio OS from profile/ledger scripts into Hermes operator surfaces such as CLI commands, dashboard readbacks, or scheduled health checks.

## Applicability

Use when adding or changing commands like `hermes portfolio ...`, portfolio doctor/verify surfaces, or read-only operator projections over project profiles, progress ledgers, and the portfolio registry.

## Anti-conditions

- Do not use this as permission to modify product project code. Portfolio governance may read project metadata and ledgers; product code changes require explicit project-scoped authorization.
- Do not treat profile metadata passing as proof that any business project is production-released.
- Do not copy OAuth/session/secrets between projects.

## Core implementation checklist

1. **Read-only by default**
   - CLI/dashboard commands should inspect profiles, ledgers, and registry only.
   - No lifecycle mutation, no task transition, no project code write, no external side effect.

2. **Profile-aware paths**
   - Use Hermes profile-aware home resolution (`get_hermes_home()` in Hermes code) rather than hardcoded `~/.hermes` when integrating into runtime code.
   - Support explicit `--home` for tests and operator inspection of another Hermes home.

3. **Bounded file reads**
   - Treat profile-controlled paths as untrusted metadata.
   - Before reading a profile/registry/ledger path: require regular file, reject directories/devices/FIFOs/sockets, and enforce a byte limit.
   - Do not unbounded `read_text()` a profile-controlled `progress_ledger` path.

4. **Fail-closed schema validation**
   - Check required fields for both presence and type.
   - Profiles: validate `project`, `project_type`, `ssot_root`, `progress_ledger`, `portfolio_profile`, `promotion_policy`, `relations`, `current_components`.
   - Relations: validate object shape, non-empty `relation`, non-empty `target`, and non-empty `merge_policy`.
   - Registry: validate `projects` and `relations` are lists of objects with required scalar fields.
   - Detect duplicate project IDs across profile files; do not silently overwrite.

5. **Protected-project guard**
   - If a project has an explicit no-code-change rule (e.g. UVISA), encode and test the guard in the profile validation path.
   - A missing guard should fail doctor/verify.

6. **Operator UX**
   - Provide human summary and machine JSON output.
   - Support top-level default command JSON where natural, e.g. `hermes portfolio --json`, not only subcommands.
   - Return non-zero exit for unhealthy doctor/verify results.

7. **Tests**
   - Use temp Hermes homes, not the real profile directory, for unit tests.
   - Cover happy path plus malformed profile types, missing protected-project guard, non-regular progress ledger, malformed registry shapes, and duplicate project IDs.

8. **Verification before commit**
   - Compile changed modules.
   - Run focused tests.
   - Run live CLI readback against the real Hermes home.
   - Run independent code review on the final staged diff; if it flags blockers, fix and re-review.
   - Stage only CLI integration files; leave unrelated runtime/docs noise unstaged.

## Session-derived pitfall

A first implementation that is "read-only" can still be unsafe if it reads profile-controlled files without regular-file and size checks. Read-only does not mean harmless: a malicious or corrupted profile can point a ledger path at a special file or huge file and hang/DoS the CLI. Treat metadata paths as untrusted input.
