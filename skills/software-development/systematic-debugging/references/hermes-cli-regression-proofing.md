# Hermes CLI regression-proofing notes

Use this note when a CLI/test regression appears after expanding a command's native capability surface.

Patterns captured
- Internal command helpers may be called from both real argparse parsing and hand-built `argparse.Namespace` fixtures in legacy tests.
- Adding a new CLI field (for example `capability`, `tenant`, template-derived metadata) can break old direct-helper tests if implementation reads `args.new_field` directly.
- Prefer `getattr(args, 'field', None)` in helper internals when the value is optional and parser evolution should remain backward-compatible for older call sites.

Debugging recipe
1. Reproduce the narrow failing test first; look for `AttributeError` on a newly introduced arg field.
2. Search for tests that call the helper directly with synthetic `Namespace` objects instead of the full parser.
3. Fix the helper for backward compatibility rather than patching every old test fixture, unless the new field is genuinely required.
4. Re-run the narrow failure, sibling tests around the same helper, then the broader CLI/DB/state slice.

Thin-wrapper migration note
- When a script only shells to another local wrapper which then shells to the native CLI, collapse the outer script to call the native CLI directly.
- Preserve a `--dry-run` mode during thinning so you can verify generated commands without side effects.

Post-update / release bootstrap import guards
- A post-pull `py_compile` guard is necessary but insufficient: it catches syntax/conflict-marker failures, but not missing imported modules.
- If `hermes_cli/main.py` registers a new subcommand, add a fresh-interpreter import smoke for `hermes_cli.main` in the update guard before declaring update success.
- The import smoke must point `PYTHONPATH` at the just-pulled tree and run in a subprocess, because the current update process may still have old modules cached.
- On import-smoke failure, rollback to the pre-pull SHA just like syntax failures.
- Regression shape to preserve: a temporary tree where `main.py` imports `hermes_cli.subcommands.context`, the file is absent, `py_compile` passes, and `_validate_critical_imports()` fails with `No module named ...`.
- Release gates should validate both source tree and packaged wheel: run source-level `critical-imports`/CLI smoke before tag/push, then build the wheel, install it into an isolated venv, and run packaged `python -m hermes_cli.main --version` plus representative subcommand help (e.g. `context --help`) before PyPI/GitHub release publish.
- Prefer `uv venv`/`uv pip install --python <venv-python>` for wheel smoke when `ensurepip` is unreliable in the active Python distribution; fall back to stdlib `venv` only when uv is unavailable.

Session example
- `hermes_cli.kanban._cmd_create()` gained template/capability metadata merge logic; older tests built a `Namespace` without `capability`, so direct `args.capability` access crashed. Switching optional reads to `getattr(..., None)` restored compatibility while keeping native template behavior intact.
- `taskpool_run_validation_suite.py` was thinned from `validation_suite -> taskpool_create_standard_task.py -> hermes kanban create` to direct `hermes kanban create --template ... --json` calls, plus a `--dry-run` command preview.
