# Experience Ratchet Public-Consensus Review — 2026-06-07

This file is the human-reviewed evidence packet for public-consensus Experience Ratchet proposals. The user explicitly approved full advancement after receiving the current evolution-direction summary (`认可，全盘推进直至边界或需要人工介入`).

## Scope and boundary

- Landing zone: public_consensus
- Review mode: human-approved bounded promotion of proposal state only.
- This packet does not directly edit Hermes core code, provider routing, memory contents, external systems, credentials, or runtime permissions.
- Each claim keeps its falsifier; promotion means the consensus is accepted as a durable governance principle, not that every future task may skip local evidence.

## Reviewed claims

### agentmemory-1b5ce49966a9 — memory supersession/versioning

Claim: Memory supersession/versioning is safer than overwriting memories because it preserves auditability and rollback paths.

Consensus interpretation:
- Durable memory changes should preserve provenance and revocation paths where possible.
- Overwrite is acceptable only when replacing a compact declarative fact with a clearly superseding one; source context should remain recoverable through session/proposal logs.

Falsifier preserved: if superseded content cannot be traced to source observations, do not promote it beyond normalized.

### bytebot-0bb88eef12ce — NEEDS_HELP / NEEDS_REVIEW fail-closed states

Claim: NEEDS_HELP/NEEDS_REVIEW style task states are reusable for fail-closed human takeover instead of pretending autonomous completion.

Consensus interpretation:
- Review/help states are safety states, not completion states.
- They should block false closure and preserve the reason/evidence needed for a human or later worker to resume.

Falsifier preserved: if the state is used to mark work done without reviewer evidence, revoke the pattern.

### hermes-agent-1f92f1efa412 — goal calibration before side effects

Claim: Ambiguous human-language tasks should pass through an internal goal-calibration gate that produces a TaskContract before side effects; ask the user only when competing targets change the work.

Consensus interpretation:
- Low-stakes ambiguity should be resolved internally with explicit assumptions.
- Ask only when ambiguity changes target, authority, side effects, or acceptance evidence.
- Over-questioning is a throughput regression.

Falsifier preserved: if calibration is applied as mandatory user questioning for trivial deterministic commands, narrow the rule.

### hermes-upstream-ratchet-3e3fa53b5dd1 — upstream ratchet synchronization

Claim: Upstream synchronization must be ratchet-style: detect, review, stage, verify, then promote; never auto-pull into private/main.

Consensus interpretation:
- Local/private overlays require staged sync and verification packets.
- Automatic upstream merge into private/main remains forbidden without semantic review and verification.

Falsifier preserved: if semantic review or verification packet is missing, promotion must stay blocked.

### openclaw-wrong-source-ad275766a45a — wrong-source hypothesis retention

Claim: Wrong-source repository hypotheses must be retained as superseded/revoked evidence instead of silently overwritten.

Consensus interpretation:
- Corrected research/source hypotheses should retain the rejected path as evidence to prevent repeated mistakes.
- If corrected source cannot be verified, both hypotheses remain challenged.

Falsifier preserved: if corrected source cannot be verified, keep both hypotheses challenged rather than promoting either.

## Verification

- User authorization: `认可，全盘推进直至边界或需要人工介入` after summary of current evolution directions.
- Promotion is limited to Experience Ratchet atom status and this evidence packet.
- Required command after transitions: `python3 ~/.hermes/scripts/experience-ratchet-maze.py validate`.
