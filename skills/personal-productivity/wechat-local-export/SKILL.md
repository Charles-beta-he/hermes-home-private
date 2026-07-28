---
name: wechat-local-export
"description": "Use when the user asks Hermes to assess, prepare, export, decrypt, refresh, or query their own macOS WeChat contacts or chat history. Starts with a zero-data-access doctor and enforces separate human gates for app re-signing, process-memory access, decryption, plaintext queries, and MCP exposure. Do not use for third-party data, remote accounts, WeChat media, or bypassing access controls."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [wechat, macos, privacy, local-data, export]
    related_skills: [hermes-agent, native-mcp]
---

# WeChat Local Export

## Scope and Applicability

**Scope:** user-local, macOS-only capability for data belonging to the user on a device they control.

**Applicability:** readiness assessment and explicitly authorized local export/query phases for macOS WeChat.

**Anti-conditions:** do not apply to another person's account, device, backup, or process; remote/cloud accounts; credential or session-token extraction; WeChat media analysis; bypassing operating-system privacy controls, organization policy, law, or third-party rights.

**Falsifier:** if the exact installed WeChat version lacks a legally available, pinned, synthetic-tested implementation, real export remains blocked even when generic SQLCipher tests pass.

## Overview

This skill is a guarded entry contract, not permission to read WeChat data. Default behavior is `doctor` only. Doctor checks application/tool versions without enumerating account directories, opening databases, reading process memory, or writing files.

The source-specific compatibility/security review is a scoped evidence artifact, not a global rule. Before evaluating whether a real export path may open, locate the current task-scoped review evidence; if it is absent, stale, unavailable, or not bound to the exact application/source versions, fail closed.

## Triggers and Counter-Triggers

Positive triggers:

- “导出我的微信联系人/聊天记录”
- “检查这台 Mac 能不能解密微信数据”
- “更新本地微信导出”
- “查询我已经明确授权的本地微信明文备份”

Counter-triggers:

- WeChat Channels/video/media → use a media workflow.
- Generic macOS permissions → use an Apple/macOS workflow.
- Remote access or data belonging to others → refuse the access path.

## Mandatory Phase Gates

Authorization for one phase never opens the next.

| Phase | Default | Required exact gate |
|---|---|---|
| Doctor/readiness | Open | None; zero real-data access |
| Dependency preparation | Closed | Exact versions, hashes, and install target |
| WeChat app re-sign | Closed | Human confirms exact app/version and accepts integrity/login/permission impact |
| Process-memory key extraction | Closed | Human runs exact privileged command; Hermes never types a password |
| Source database read | Closed | Exact local root and read-only scope |
| Plaintext export | Closed | Exact output root, permissions, retention, and rollback |
| Plaintext query | Closed | Exact purpose/scope; redact unrelated content |
| MCP registration | Closed | Separate authorization; local user scope only |
| External delivery | Closed | Separate exact target and payload gate |

## Default Doctor

Run only the bundled read-only script:

```bash
python3 ~/.hermes/skills/personal-productivity/wechat-local-export/scripts/wechat_export_doctor.py --json
```

Doctor must report `data_access_attempted: false`. It must not access WeChat account/container paths, enumerate accounts, read databases, inspect process memory, request Full Disk Access, or write a receipt.

`ready_for_export: false` is an honest blocked state, not permission to fetch arbitrary alternatives.

## Secret and Privacy Safety

- Never read, print, summarize, paste, upload, or place key files, raw SQLCipher keys, or process-memory bytes into model context.
- Never ask the user to paste a key into chat.
- If a reviewed local tool later accepts a key file, the file stays outside source repositories, is user-owned and mode `0600`, and is passed by path without echoing its contents.
- Plaintext output roots must be non-symlink directories under an exact approved path, mode `0700`; database files must be `0600`.
- Network access is closed during source discovery, key handling, decryption, and querying.
- Receipts contain versions, counts, digests, and redacted paths only—never keys, identifiers, contact names, or message text.

## Dependency Policy

- Pin Git sources to immutable commits and record tree hashes.
- Never execute moving-branch raw downloads, unpinned clones, or broad one-click installers.
- Separate network-fetch preparation from real-data processing.
- Review installers before use and do not automatically register MCP.
- Do not seek mirrors or bypass a source takedown; mark that implementation path blocked.

## Real Export Gate

Do not claim real export capability until all are true:

1. A legally available, pinned, reviewed implementation supports the exact installed WeChat version.
2. A synthetic database test proves decryption/export without real user data.
3. Key handling passes no-stdout/no-log/no-model-context tests.
4. Output containment, symlink rejection, `0700/0600`, rollback, and no-network tests pass.
5. The user supplies exact human authorization for each app/data/key phase.
6. A real-data smoke runs under user observation and receives separate acceptance.

Until then, report `doctor_available / export_blocked`, not “ready”.

## Definition of Done

- [ ] **Outcome:** doctor capability is installed and its current state is reported without claiming real export when compatibility is blocked.
- [ ] **Process:** every privileged, secret, source-data, plaintext, MCP, and external-delivery boundary remains separately gated.
- [ ] **Style:** receipts and user reports are structured, redacted, and distinguish `doctor_available` from `export_ready`.
- [ ] **Efficiency:** readiness uses one bounded doctor call and does not enumerate private data or retry unsupported extraction paths.

## Common Pitfalls

1. Treating “I want this capability” as authorization to re-sign WeChat or read chats immediately.
2. Executing moving remote code or one-click installers.
3. Printing a key because an upstream script does so.
4. Registering a broad MCP server by default.
5. Claiming WeChat compatibility from a standard SQLCipher self-test.
6. Confusing successful skill installation with successful real-data export.

## Verification Checklist

- [ ] Doctor readback contains `data_access_attempted: false`.
- [ ] Exact application version and source versions are recorded in scoped evidence.
- [ ] No account directory, database, key, memory, or chat content was read during readiness.
- [ ] No dependency, MCP registration, app signature, permission, or data file changed without its own exact gate.
- [ ] Any real-export claim has synthetic proof plus human-observed acceptance.
