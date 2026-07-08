# P3 Dashboard/API Read-only Projection

Timestamp: 2026-07-08T04:20:00Z

## Design Document

Expose the same Context Engineering preflight projection through the Hermes dashboard API, keeping the dashboard a read-only operator surface and not an executor.

## Scope

Endpoint:

```text
GET /api/context/preflight?packet=<packet.json>
```

Authentication:

- Uses existing dashboard `/api/` session-token middleware.
- Unauthenticated calls return 401.

## Boundary

- Read-only API projection.
- No LLM call.
- No writes.
- No scheduler/cron action.
- No gateway delivery.
- No taskpool lifecycle mutation.
- No runtime prompt injection.
- No executor buttons.

## Gate Readback

The endpoint reuses `collect_context_preflight()` and therefore preserves the default-off config gate:

```yaml
agent:
  context_engineering_packet_preflight: true
```

When disabled, the API returns `status=disabled` with `packet_checked=false` and all side effects closed.

When enabled and packet-valid, the API returns `status=ok` with packet summary and all side effects closed.

When enabled and packet missing/invalid, the API returns HTTP 400 with `status=blocked`.

## Verification Readback

Targeted tests:

```text
./venv/bin/python -m pytest tests/hermes_cli/test_context_engineering_cmd.py tests/hermes_cli/test_context_preflight_api.py -q
.............                                                            [100%]
13 passed in 0.37s
```

Syntax check:

```text
./venv/bin/python -m py_compile hermes_cli/context_engineering.py hermes_cli/subcommands/context.py hermes_cli/web_server.py hermes_cli/main.py
exit 0
```

API smoke using Starlette TestClient against the actual FastAPI app:

```text
GET /api/context/preflight?packet=/Users/charles/.hermes/workflows/projects/hermes-context-engineering-os/examples/sample-context-packet.json
status=200
{"enabled": true, "status": "ok", "packet_checked": true, "runtime_prompt_injection": false, "side_effects": {"external": false, "llm": false, "writes": []}, "result": {"checks": 2, "closed_authority": 4, "evidence_ids": 2, "sources": 2}}
```

## Next Safe Slice

P4 can add a minimal dashboard UI panel that calls this API and displays: gate status, packet checked, result counts, side-effect flags, and runtime_prompt_injection=false. It must not add executor controls or lifecycle mutation.
