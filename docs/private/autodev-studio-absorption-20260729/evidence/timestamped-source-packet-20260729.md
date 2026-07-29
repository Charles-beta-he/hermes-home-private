# AutoDev Studio Timestamped Source Packet

- captured_at_utc: `2026-07-29T01:53:56Z`
- source_repo: `https://github.com/krishagarwal314/autodev-studio`
- source_commit: `6cef552bc69fba7876fe9813ab96fc001ab66970`
- source_tree: `f8379d001cc20ef2eacaa4c3b82ca684b0a384cb`
- local_checkout: `/Users/charles/.hermes/runs/autodev-studio-reference-review-20260729/source`
- local_target: `/Users/charles/.hermes/docs/private/autodev-studio-absorption-20260729/**`
- authority: external read, local documentation write, and read-only validation only

## Objective

Bind exact source identity, source-line claims, Hermes overlap, a candidate CapabilityGraph, and proposal-only experience atoms without installing or importing the upstream runtime into Hermes.

## Source facts and boundaries

1. `evidence/source-evidence.json` binds seven claims to exact source line-range SHA-256 hashes.
2. Source identity is a clean detached checkout of the commit/tree above.
3. The upstream `159 passed`, Ruff pass, and 41% coverage evidence describes the pinned upstream repository only; it does not certify Hermes integration or production readiness.
4. Existing Hermes `CompletionGate`, lane-specific `completion_gate_failures`, advisory-only separation, and taskpool certification gates mean this slice must not add a duplicate completion-gate runtime.
5. AutoDev Studio's fail-open `INCONCLUSIVE` fall-through and argv/token risk are retained as source findings, not copied behavior.

## Local verification snapshot

```text
scripts/verify_pack.py: ok=true, errors=[]
tests/test_verify_pack.py: 5/5 PASS
check_reference_absorption_pack.py: REFERENCE_ABSORPTION_PACK_OK
python py_compile: PASS
negative controls: claim hash tamper BLOCK; authority true BLOCK; missing gate outcomes BLOCK; unexpected promotion BLOCK
```

## Authority and negative requirements

The evidence manifest asserts `false` for runtime mutation, core mutation, taskpool write, scheduler write, external dispatch, publish/deploy/push, and credential entry. The graph authority boundary is closed. Proposal records remain `proposal_only`, with `promotion.performed=false`.

No install, upstream runtime import, runtime routing change, Hermes core mutation, task lifecycle write, cron write, external delivery, PR, push, publish, deploy, credential entry, payment, or destructive action is authorized or claimed.

## Rollback and post-action readback

Before a successful scoped commit, unstage only this absorption pack:

```text
git reset --staged -- docs/private/autodev-studio-absorption-20260729
```

After a future local commit, rollback is `git revert <exact-local-commit>`. No push is authorized. Post-action readback must bind the exact commit, commit tree, scoped file list, clean pack status, source identity, quote hashes, deterministic validators, and any independent review to that same identity.
