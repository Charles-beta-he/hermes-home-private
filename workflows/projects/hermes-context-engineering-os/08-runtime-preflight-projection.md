# P2 Runtime Preflight Projection

Timestamp: 2026-07-08T04:05:00Z

## Design Document

Advance beyond the edge validator into a default-off runtime preflight projection while preserving Hermes prompt-cache and core-loop boundaries.

## Scope

## Command

```bash
hermes context preflight --packet <packet.json> --json
```

## Gate Readback

Config key:

```yaml
agent:
  context_engineering_packet_preflight: true
```

Default behavior is disabled. Disabled mode does not validate the packet and does not affect runtime prompt assembly.

## Boundary

- Local-only projection.
- No LLM call.
- No writes.
- No external dispatch.
- No taskpool lifecycle mutation.
- No cron/scheduler action.
- No runtime prompt injection.
- No prompt-cache mutation.

## Verification Readback

Targeted tests:

```text
./venv/bin/python -m pytest tests/hermes_cli/test_context_engineering_cmd.py -q
.........                                                                [100%]
9 passed in 0.13s
```

Syntax check:

```text
./venv/bin/python -m py_compile hermes_cli/context_engineering.py hermes_cli/subcommands/context.py hermes_cli/main.py
exit 0
```

Disabled/default real CLI readback:

```text
hermes context preflight --packet /Users/charles/.hermes/workflows/projects/hermes-context-engineering-os/examples/sample-context-packet.json --json
{
  "enabled": false,
  "gate": "agent.context_engineering_packet_preflight",
  "message": "preflight gate disabled; no packet validation performed",
  "packet_checked": false,
  "runtime_prompt_injection": false,
  "side_effects": {"external": false, "llm": false, "writes": []},
  "status": "disabled"
}
```

Enabled real CLI readback with temporary HERMES_HOME:

```text
HERMES_HOME=<tmp-with-config> hermes context preflight --packet /Users/charles/.hermes/workflows/projects/hermes-context-engineering-os/examples/sample-context-packet.json --json
{
  "enabled": true,
  "status": "ok",
  "packet_checked": true,
  "result": {"checks": 2, "closed_authority": 4, "evidence_ids": 2, "sources": 2},
  "runtime_prompt_injection": false,
  "side_effects": {"external": false, "llm": false, "writes": []}
}
```

Enabled fail-closed missing packet readback:

```text
HERMES_HOME=<tmp-with-config> hermes context preflight --json
status=blocked
message=enabled context preflight requires --packet
exit=1
```

## Next Safe Slice

P3 may add a read-only dashboard/API projection of the same preflight result. Do not add executor buttons or prompt injection. Runtime prompt assembly can only be touched after a separate prompt-cache invariant test proves disabled/enabled behavior does not alter stable/context/volatile cache boundaries unexpectedly.
