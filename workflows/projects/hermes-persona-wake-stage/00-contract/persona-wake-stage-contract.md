# Hermes Persona Wake Stage Contract

Status: local contract restored draft
Updated: 2026-07-07T15:08:00+08:00

## Scope

Defines the local, cross-end contract for Hermes-facing wake ritual / persona stage surfaces. This is not a runtime deployment and does not authorize voice send, external send, default wake behavior, credential entry, or hidden automation.

## Invariants

- Core agent authority remains outside the visual/persona surface.
- Wake stage is presentation + explicit command binding only.
- Any external send, voice output, payment, credential, production deploy, or destructive operation requires separate exact authority.
- Surfaces must preserve mode identity and evidence/readback boundaries across Web/PWA/RN/Desktop/Telegram.
- No cross-project secret/auth/session-state merge.

## Required evidence before promoted/production status

1. Surface-specific runtime implementation readback.
2. UI/screenshot or CLI evidence for command binding.
3. Negative evidence that no default external send or credential path is enabled.
4. Portfolio semantic audit readback.
