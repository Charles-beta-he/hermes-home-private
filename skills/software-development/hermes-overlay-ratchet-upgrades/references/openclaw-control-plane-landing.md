# OpenClaw control-plane landing in local Hermes overlay

Use this reference when a local Hermes fork already has helper modules (for example `agent/openclaw_control_plane.py`) but they are only partially wired into runtime.

## What landed successfully

1. Keep enhancements `default-off` and `fail-soft`.
   - Import optional overlay helpers inside `try/except`.
   - If helper import fails, return empty context / no-op gate instead of breaking the main path.

2. Wire helper-only features into real runtime seams.
   - `agent/prompt_builder.py`
     - add optional import of `load_experimental_config` and `render_scoped_policy_context`
     - create `_load_scoped_policy_context(cwd_path)`
     - append scoped policy context in `build_context_files_prompt()` after project context
   - `tools/memory_tool.py`
     - add optional import of `load_experimental_config` and `memory_write_gate`
     - create `_memory_write_gate_report(action, target, content)`
     - run gate before `add` / `replace`
     - if gate rejects, return structured error payload with `gate=...`

3. Respect the existing experimental config surface.
   - `openclaw_control_plane.scoped_policy_context`
   - `openclaw_control_plane.memory_write_gate`
   - leave disabled by default until verification is complete

## Important pitfall

`memory_write_gate()` expects OpenClaw memory-contract source names such as `semantic_memory`, while `memory_tool()` exposes user-facing targets `memory` and `user`.

Do not pass `memory` or `user` directly into `memory_write_gate()`.
Map the durable memory-tool write to `semantic_memory` unless you are explicitly extending the contract and tests at the same time.

## Test pattern that worked

Add focused tests rather than broad suite-first validation:
- `tests/agent/test_prompt_builder.py`
  - opt-in injects scoped policy context
  - default-off does not call the renderer
- `tests/tools/test_memory_tool_openclaw_gate.py`
  - gate enabled + WIP/temporary content => blocked
  - gate enabled + durable preference/fact => allowed
- keep `tests/agent/test_openclaw_control_plane.py` in the run list as regression coverage for helpers already present

## Verification commands

Use the repo venv explicitly when shell `pytest` is absent:

```bash
python3 -m py_compile \
  agent/prompt_builder.py \
  tools/memory_tool.py \
  tests/agent/test_prompt_builder.py \
  tests/tools/test_memory_tool_openclaw_gate.py

./venv/bin/pytest -q \
  tests/agent/test_openclaw_control_plane.py \
  tests/agent/test_prompt_builder.py \
  tests/tools/test_memory_tool_openclaw_gate.py
```

Observed good result during landing: targeted suite passed (`133 passed, 1 skipped`).

## Why this matters for ratchet upgrades

This pattern converts local overlay code from "helper exists" into "runtime seam + tests + config gate". That makes later upstream rebases safer because the enhancement is:
- easier to detect when drift breaks the seam
- easier to replay after update
- easier to certify with focused evidence
