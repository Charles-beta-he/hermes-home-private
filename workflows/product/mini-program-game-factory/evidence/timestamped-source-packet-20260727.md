# Cocos Creator / Platform Adapter Timestamped Source Packet

- captured_at_utc: `2026-07-27T04:57:50Z`
- scope: `workflows/product/mini-program-game-factory/**`
- authority: local evidence only; no Creator, SDK, DevTools, credential, upload, review, publish, payment, or Git push authority

## Objective

Bind the deterministic Creator project candidate, exact Creator editor/build identity fields, official CLI success semantics, and local `wx`/`tt` adapter candidates without promoting fixture or fake-SDK evidence into external execution claims.

## Source facts and boundaries

1. Official Cocos Creator 3.8 command-line build documentation:
   `https://docs.cocos.com/creator/3.8/manual/en/editor/publish/publish-in-command-line.html`
2. Machine-readable source record:
   `evidence/cocos-creator-cli-source.json`
3. The documented successful Creator CLI build exit code is integer `36`; exit code `0` is rejected by the local handoff verifier.
4. `cocos/cocos-engine` commit/package evidence is runtime-engine evidence, not local Creator editor executable identity.
5. Project `serialization_creator_version=3.8.0` is a fixed serialization reference, not a claim about an installed editor patch.
6. Fake-SDK adapter tests establish only local interface contracts. They do not establish official SDK compatibility, authenticated identity, DevTools/device behavior, or platform acceptance.

## Design and gate readback

- Design/workflow contract: `06-planning/cocos-integration-workflow.md`
- Capability graph: `capability-graph.json`
- Converge matrix: `evidence/converge-matrix.md`
- Platform contract: `runtime/cocos/platform-port-contract.json`
- Delivery gate: `07-build/cocos_delivery_gate.py`
- Blocked non-executing preflight: `evidence/cocos-build-preflight-blocked.json`
- Shipping boundary: `08-shipping/shipping-packet.md`

Current blocked preflight readback:

```text
closure_state=build_preflight_blocked
command=null
creator_cli_unavailable
creator_editor_version_unverified
appid_required
creator_build_config_export_required
build_authority_closed
```

## Local verification snapshot

```text
Python unittest: 103/103 PASS
Node tests: 17/17 PASS
Node smoke: PASS
Python compile: 17/17 PASS
JSON parse: 56/56 PASS
generated project TypeScript compile: PASS
git diff --check: PASS
scoped secret scan: PASS
project files: 19
project_digest=85f89ef57b6d8431a4de3e4d686318dd441dcb8fdbeb456b796b7a82cb0179e8
```

These results bind the current local staged slice only until a successor commit/tree and immutable archive are created and reverified.

## Rollback and post-action readback

Before commit, unstage only this project with:

```text
git reset --staged -- workflows/product/mini-program-game-factory
```

After a future local successor commit, use `git revert <exact-commit>` if rollback is required. No push is authorized. Post-action verification must read back exact commit/tree, scoped tree listing digest, immutable archive digest/parity, archive regression, and two independent verdicts bound to the same identity.
