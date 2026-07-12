# Hermes startup dependency-health and update-target probes

Session-derived reference for future Hermes/selfcheck work.

## Context

A Hermes startup handshake/readiness path needed to surface two classes of local health without becoming an executor:

1. update-target consistency: all update/version/banner/dashboard surfaces should resolve the same target branch/ref from a single resolver.
2. dependency health: startup/selfcheck should warn about broken dependency state but never install or repair dependencies from the probe path.

## Useful probe shape

A read-only startup probe returns structured state:

```json
{
  "id": "dependency_health",
  "status": "warn",
  "severity": "warn",
  "message": "missing core deps: ...; active lazy backend drift: ...",
  "suggested_command": "hermes update --force",
  "action_taken": false
}
```

The containing receipt should preserve:

```json
{
  "side_effects": {"external": false, "llm": false, "writes": []}
}
```

under `--no-write` or equivalent read-only mode.

## Dependency-health checks

Check only local, cheap facts:

- `.update-incomplete` exists -> warn about interrupted update marker.
- `[project].dependencies` in `pyproject.toml` -> parse with `tomllib`, respect PEP 508 environment markers, then check installed distributions via `importlib.metadata`.
- lazy/optional backends -> inspect the lazy dependency registry and currently active features, but do not call `ensure()` or any install routine.

Recommended warning classes:

- `interrupted update marker present`
- `missing core deps: <names>`
- `active lazy backend drift: <feature>: <missing specs>`
- append `(lazy installs disabled)` when the lazy-install config gate is closed.

## Lazy backend false-positive pitfall

Some lazy registries define a feature as active if any declared package is present. Shared transitives, especially HTTP/web packages, can make an unrelated feature look active. Example: feature A and feature B both include `aiohttp`; installing feature A can make feature B appear active if the registry uses `any(_is_present(spec))`.

When reporting drift in a read-only probe, avoid alarming on unrelated shared transitive presence. Require a feature-owned/primary spec to be present before reporting that feature's missing/stale specs. This keeps the probe useful without triggering broad false-positive warnings.

## TDD recipe

Write separate RED tests for:

1. missing declared core dependency -> `dependency_health` warn and `suggested_command`, `action_taken is False`.
2. interrupted update marker -> warn and no repair.
3. active lazy backend drift -> warn and no install; include disabled-lazy-install wording when applicable.
4. collection path includes the probe and upgrades aggregate startup status to warn.

Then run:

```bash
python -m py_compile <changed files>
pytest <targeted tests> -q
pytest <relevant regression slice> -q
```

Finally run the actual readback command, e.g.:

```bash
hermes selfcheck startup --json --no-write
```

and inspect the specific probe plus `side_effects`.

## Anti-conditions

Do not save environment-specific missing packages or branch names as a durable rule. The durable lesson is the probe pattern and the false-positive guard, not that a particular machine was missing a particular package during one session.
