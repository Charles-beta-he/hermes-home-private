# Browser tool truth gate pattern

Use this when hardening or reviewing Hermes browser automation output paths, especially `browser_snapshot`, `browser_navigate` auto-snapshot, web-page text extraction, scheduled reports, or any browser-derived content that is injected into model context.

## Problem class

Browser accessibility-tree text is controlled by the visited page. A page can contain instruction-looking text (`ignore previous instructions`, `reveal system prompt`, `send secrets`) or anti-bot/challenge text (`Just a moment...`, Cloudflare Ray ID, captcha). If returned as plain successful page content, the agent may over-trust it and scheduled/browser-heavy jobs may pay unbounded token cost.

## Durable pattern

Add a deterministic, low-risk truth gate at the browser tool boundary before page text enters the agent-facing result:

1. Wrap every successful browser-derived snapshot as untrusted data.
   - Explicitly say page content is not system/user/developer instructions.
   - Do not hide suspicious page text; surface it with degraded classification.
2. Classify success snapshots with `validation_status`:
   - `validation_success` for normal pages.
   - `degraded` for prompt-injection-looking content.
   - `degraded` for anti-bot / Cloudflare / captcha challenge content.
3. Include `degraded_reason` when degraded:
   - `prompt_injection_text_detected`
   - `anti_bot_or_cloudflare_challenge`
4. Classify snapshot failures separately:
   - `needs_auth` for 401/403/login/sign-in/authentication failures.
   - `unreachable` for timeout/DNS/connection/navigation failures.
   - fallback `degraded` for other read failures.
5. Cap agent-facing snapshot output deterministically and report cost metadata:
   - `before_chars`
   - `after_chars`
   - `cap_chars`
   - `truncated`
6. Apply the same gate to `browser_navigate` auto-snapshot, not just explicit `browser_snapshot`; otherwise the first tool result remains an unguarded injection/cost path.

## Minimal fixtures

Add pure/deterministic fixtures before relying on live third-party pages:

- Prompt-injection fixture: accessibility-tree text containing `IGNORE ALL PREVIOUS INSTRUCTIONS` and a request to reveal config/secrets. Expect degraded + untrusted wrapper.
- Anti-bot fixture: `Just a moment...`, `Checking your browser`, `Cloudflare Ray ID`. Expect degraded with anti-bot reason, not silent success.
- Normal official page fixture: simple docs page with headings/links. Expect `validation_success` and bounded output metadata.
- Failure fixture: mocked browser command errors for auth and timeout. Expect `needs_auth` and `unreachable`.
- Oversized snapshot fixture: verify cap/truncation metadata and element counts survive.
- Navigate auto-snapshot fixture: anti-bot title or snapshot must also mark degraded.

## Verification closeout

For a bounded hardening slice, acceptable evidence is:

- `py_compile` or equivalent syntax check on the tool and tests.
- Targeted pytest/browser-tool regression subset.
- Scoped secret scan of the diff.
- Taskpool/selfcheck/ratchet evidence if the change is part of Hermes evolution work.
- Report path with behavior, fixtures, commands, residual risk, and rollback.

## Pitfalls

- Do not change browser permissions, credential handling, provider routing, or navigation policy when the task is only snapshot trust/cost hardening.
- Do not treat a live Cloudflare page as a stable acceptance test. Use deterministic fixtures for truth-gate behavior; live anti-bot E2E is a separate, flaky/provider-dependent task.
- Do not block or strip suspicious text silently. The operator needs to see what was found; classify as degraded and wrap as untrusted data.
- Do not let only explicit snapshot calls use the gate. Navigation responses that include auto-snapshots are also model-context injection surfaces.
