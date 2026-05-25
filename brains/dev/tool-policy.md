# Dev Tool Policy

- Use git status/diff/log before edits.
- Use tests/build/lint appropriate to touched files.
- Use browser-harness for UI/H5 verification when relevant.
- Preserve user WIP; never reset unrelated changes without explicit scope.
- Prefer structured command output (`--json`, machine-readable reports, schemas) over scraping prose when the tool supports it.
- For agent-consumed CLI/script output, assert schemaVersion or contract version, required fields, failure shape, deterministic fixture/replay behavior, and no ANSI/control noise in machine output.
- For tools with version-matched workflows/help/diagnostics, run the workflow discovery command from the same binary that will execute the project; record global-vs-repo-local binary differences.
- Run experimental compilers, unfamiliar CLIs, evals, benchmarks, generated artifacts, and untrusted examples in isolated/disposable workspaces by default. Host-affecting local artifact tests require explicit rationale or opt-in.
- Keep private access material, private inputs, and production/sensitive data out of sandbox, eval, compiler, and generated-artifact experiments.
- Auto-repair proposals must be plan-first unless the user/task explicitly approves applying edits, and must include diagnostic id, repair id/summary, safety label, affected files, and retest command.
