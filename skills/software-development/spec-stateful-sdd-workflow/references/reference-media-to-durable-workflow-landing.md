# Reference-media to durable workflow landing ladder

Scope: class-level workflow for absorbing an external media/article/repository lead into an agent or project workflow. Applicability: use when the user approves turning a source into durable behavior, governance, or implementation. Anti-conditions: do not use for trivial summaries, hidden/paywalled claims without direct evidence, secrets/credentials, destructive actions, external publication, or one-off task progress.

## Lesson

Do not stop at a skill or template update when the requested target is durable behavior or workflow governance. A skill patch is only one safe rung. Continue through the next safe durable layers until a real boundary blocks progress.

## Default ladder

1. Evidence boundary
   - Capture public preview / source metadata.
   - Verify any named external artifact directly.
   - Label hidden/app-gated media as unavailable.

2. SSOT boundary
   - Create or update one canonical review/absorption note.
   - Keep source facts, claims, decisions, red lines, and acceptance criteria in that artifact.
   - Derived skills, task records, runtime changes, and chat summaries should point back to this SSOT.

3. Skill/template boundary
   - Patch the class-level skill or add a reference/template/script.
   - Keep session-specific detail in `references/`; reusable starter artifacts in `templates/`; deterministic probes in `scripts/`.

4. Task-tracking boundary
   - If runtime, task lifecycle, local knowledge, scheduler, or self-architecture work remains, create a governed follow-up card with acceptance criteria and red lines.
   - Runtime/system-prompt changes should normally require focused tests, prompt readback, and certification/gate status.

5. Local reversible implementation boundary
   - Implement only the smallest safe slice: local docs/schema/doctor, config-gated prompt guidance, or read-only projection.
   - Verify with tests/readback and make a scoped commit when editing a source checkout.

6. Runtime/system prompt boundary
   - Treat system-prompt changes as global behavior changes.
   - Preserve prompt-cache invariants: no mid-session mutation, no large template injection, no duplicate guidance.
   - Prefer extending an existing compact guidance block over adding another broad prompt block.
   - Cover enabled, disabled, and no-tools paths in tests.

7. Scheduler boundary
   - Do not create a scheduled job just because an idea is important.
   - Scheduling is appropriate only for recurring watchdogs, reconciliation, stale-knowledge checks, or maintenance loops.
   - Prefer local/no-agent/silent receipts unless the user explicitly supplies a delivery target.

## Decision rule

- If the next rung is local, reversible, and evidence-producing, continue.
- Stop only at exact authority, destructive, external side effect, credential, production, or certification gates.
- If a certification gate fails or is advisory-only, record implementation evidence but do not mark lifecycle `done`.

## Example pattern classes

Spec-first source:
- Skill/template: Spec Brief + Converge Matrix.
- Runtime: compact objective/planning guidance extended with Spec Gate behavior.
- Task record: runtime prompt card requiring tests and prompt readback.

Living-knowledge source:
- SSOT: verified source review note.
- Local reversible implementation: markdown/JSON knowledge-node schema plus doctor/readback script.
- Scheduler later only after schema/idempotency/receipts exist and a stale-check loop is actually needed.
