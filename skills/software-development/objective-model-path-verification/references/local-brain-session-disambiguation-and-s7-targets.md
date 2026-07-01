# Local-brain session disambiguation and S7 exact-target boundary

Use when the user asks about a recent “本地大脑 / local brain” conversation or asks to advance local-brain safety gates into real side effects.

## Session recall pitfall

Do not assume “本地大脑安全门” means taskpool `human_escape_guard` or ordinary taskpool health. In this user’s Hermes setup, “本地大脑” may refer to several distinct threads:

- `brainctl` local-brain search/evidence retrieval and indexing.
- Local-brain auto-constraint / BrainConstraintGate / side-effect-gates control plane.
- Agent OS / autonomous-runtime-governance safety boundaries.
- Taskpool/local-brain dispatch health.

When the user says “刚才有一个本地大脑…会话” or corrects “我说的是本地大脑相关的会话”, search session history for the exact term `"本地大脑"` first, then inspect the likely CLI session rather than only context-card writer sessions. Use the kickoff and final bookends to identify whether the target was search/indexing, side-effect gates, or taskpool.

## Minimum disambiguation evidence

Before reporting progress, identify:

1. session id and title;
2. the user kickoff message;
3. the last concrete implementation/result message;
4. changed files or receipts, if present;
5. explicit remaining boundary.

If multiple hits exist, summarize the top candidates and say which one you selected and why.

## S7 exact-target boundary

When the user asks to proceed with real external dispatch, publish/deploy/push, destructive operation, or credential/payment input, broad language such as “任意目标” is not an executable AuthorityGrant.

Required before execution:

- external dispatch: exact platform, target, payload, payload hash or exact text, and readback/receipt path;
- publish/deploy/push: exact repo path, remote, branch, commit/files, rollback ref, and post-action readback;
- destructive: exact resource path, backup path, restore command, and readback; no broad globs or project/home roots;
- credential/payment: service/action/human input point/non-sensitive readback. The agent must not type or store secrets.

Safe default if exact targets are missing: generate or update a local pending authorization packet and stop at the smallest human gate. Do not silently downgrade this to a fake completion, and do not perform canary external actions unless the canary target is itself exact and authorized.
