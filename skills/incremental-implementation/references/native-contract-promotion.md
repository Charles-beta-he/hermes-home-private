# Native contract promotion during incremental rollout

Use this pattern when a feature starts as a thin native-aligned bridge and the user asks for a long-term, maintainable full rollout rather than stopping at the minimal green fix.

Key lessons
- After landing the minimal native path, inspect whether important contract fields still exist only in text payloads or event metadata. If a field is used for routing, querying, audit, or lifecycle decisions, promote it to a first-class persisted field instead of reparsing body text forever.
- Keep backward compatibility while promoting: prefer reading the new DB field first, then fall back to legacy frontmatter/event-derived values for older rows.
- When a validation script has already become a thin wrapper around a native command, remove the extra wrapper layer instead of preserving script-to-script subprocess chains.
- For maintainability, evolve fixed task lists into a spec-driven runner. Keep built-in defaults for the common suite, but allow an external JSON spec so future suites extend data, not code.

Concrete rollout shape that worked
1. Fix assertion drift with the smallest native-compatible change so the current chain is green.
2. Thin validation orchestration to call the native CLI directly.
3. Promote the key contract field into the DB schema plus migration path.
4. Update in-memory/task serialization to read the first-class field and fall back to legacy metadata.
5. Extend tests to assert the field persists on the task row, not only in emitted events.
6. Add dry-run/spec support to validation runners so expansion happens through declarative input.

Pitfalls
- Do not stop at event payload persistence if the field now matters operationally; that leaves routing/querying dependent on body parsing.
- Do not patch only the tests when the real issue is internal helper compatibility with older Namespace-style callers.
- Do not keep a script wrapper solely because it existed before native support landed; once the CLI is native, wrapper layers become maintenance debt.

Verification checklist
- Existing CLI compatibility tests still pass when helper callers omit newer argparse fields.
- DB migration succeeds on already-migrated schemas and old schemas missing the promoted column.
- Task fetch / JSON rendering exposes the promoted field correctly.
- Validation dry-run prints native commands directly.
- Related CLI/DB/state tests pass after the structural promotion.
