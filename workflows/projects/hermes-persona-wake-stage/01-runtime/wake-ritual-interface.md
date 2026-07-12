# Wake Ritual Interface

Status: local interface contract draft
Updated: 2026-07-07T15:08:00+08:00

## Minimal interface

- `wake_mode`: named mode/persona stage selected by explicit user action or configured local setting.
- `surface`: web, pwa, rn, desktop, telegram, or cli.
- `command_binding`: explicit command affordance; cannot imply execution authority.
- `evidence_ref`: local proof path or runtime readback for state-changing flows.

## Negative cases

- No default auto-speech.
- No hidden send.
- No background credential/payment entry.
- No production deploy from wake ritual.
