# P4 Dashboard UI Read-only Projection

Timestamp: 2026-07-08T04:45:00Z

## Design Document

Expose Context Engineering preflight as a read-only dashboard panel on the System page. The panel calls the existing dashboard API projection and displays the returned gate/status/result/side-effect fields without adding executor controls.

## Scope

Frontend files:

- `/Users/charles/.hermes/hermes-agent/web/src/lib/api.ts`
- `/Users/charles/.hermes/hermes-agent/web/src/pages/SystemPage.tsx`

UI surface:

- System page section: `Context Engineering preflight`
- Labeled input: `Context Packet path`
- Button: `Check preflight`
- Status badges: preflight status, gate enabled/disabled, packet checked/not checked, runtime prompt injection flag
- Result readback: sources, evidence IDs, checks, closed authority
- Side-effect readback: external, llm, writes

## Boundary

- Read-only UI projection.
- No executor buttons.
- No LLM call.
- No writes.
- No taskpool lifecycle mutation.
- No scheduler/cron action.
- No gateway delivery.
- No runtime prompt injection.

## Verification Readback

Frontend typecheck/build:

```text
npm --workspace web run typecheck && npm --workspace web run build

> web@0.0.0 typecheck
> tsc -p . --noEmit

> web@0.0.0 build
> tsc -b && vite build

✓ built in 319ms
```

Backend/API regression:

```text
./venv/bin/python -m pytest tests/hermes_cli/test_context_engineering_cmd.py tests/hermes_cli/test_context_preflight_api.py -q
.............                                                            [100%]
13 passed in 0.40s
```

Syntax check:

```text
./venv/bin/python -m py_compile hermes_cli/context_engineering.py hermes_cli/subcommands/context.py hermes_cli/web_server.py hermes_cli/main.py
exit 0
```

Browser readback:

- Started local dashboard on `http://127.0.0.1:9129/system`.
- System page rendered the new `Context Engineering preflight` section.
- Visible controls: `Context Packet path` input and `Check preflight` button.
- Visible boundary text: `Read-only projection only: no LLM call, no writes, no taskpool lifecycle mutation, and no runtime prompt injection.`
- After clicking `Check preflight` with the default config gate disabled, visible badges included: `disabled`, `gate disabled`, `packet not checked`, `runtime prompt injection: false`.
- Browser console readback showed zero console messages and zero JavaScript errors.

## Notes

The disabled readback is expected on the default profile because `agent.context_engineering_packet_preflight` is default-off. Enabled behavior is covered by the API TestClient smoke in `09-dashboard-api-projection.md`; the UI intentionally does not mutate config to turn the gate on.
