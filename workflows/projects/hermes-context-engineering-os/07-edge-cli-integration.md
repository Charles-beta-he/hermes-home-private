# P1 Edge CLI Integration

Timestamp: 2026-07-08T03:35:00Z

## Scope

Promote Context Engineering from project-local scripts to a Hermes edge CLI surface without touching the runtime prompt or core agent loop.

## Commands

```bash
hermes context packet lint <packet.json>
hermes context eval run --root <context-engineering-project-root>
```

## Boundary

- Local-only readback / validation surface.
- No LLM call.
- No gateway delivery.
- No scheduler/cron action.
- No taskpool lifecycle mutation.
- No publish/deploy/push/destructive operation.
- No runtime prompt injection.

## Verification Readback

Executed from `/Users/charles/.hermes/hermes-agent`:

```text
hermes context packet lint /Users/charles/.hermes/workflows/projects/hermes-context-engineering-os/examples/sample-context-packet.json
PASS: /Users/charles/.hermes/workflows/projects/hermes-context-engineering-os/examples/sample-context-packet.json sources=2 evidence_ids=2 checks=2 closed_authority=4
```

```text
hermes context eval run --root /Users/charles/.hermes/workflows/projects/hermes-context-engineering-os
PASS_EXPECT local-foundation.json: exit=0
FAIL_EXPECT missing-do-not-save.json: exit=1
FAIL_EXPECT missing-readback.json: exit=1
FAIL_EXPECT unknown-evidence-id.json: exit=1

REGRESSION PASS checked=4
```

## Test Evidence

```text
./venv/bin/python -m pytest tests/hermes_cli/test_context_engineering_cmd.py -q
5 passed in 0.18s
```

```text
./venv/bin/python -m py_compile hermes_cli/context_engineering.py hermes_cli/subcommands/context.py hermes_cli/main.py
exit 0
```

## Implementation Files

- `/Users/charles/.hermes/hermes-agent/hermes_cli/context_engineering.py`
- `/Users/charles/.hermes/hermes-agent/hermes_cli/subcommands/context.py`
- `/Users/charles/.hermes/hermes-agent/tests/hermes_cli/test_context_engineering_cmd.py`

## Next Safe Slice

P2 can add a read-only dashboard/API projection over the same validator result. Keep it projection-only: no lifecycle writes, no runtime prompt changes, no automatic mission/taskpool advancement.
