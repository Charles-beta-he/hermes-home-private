# WeChat Exporter Reference Review / Capability Spec

- Source: `https://github.com/robbin/wechat-exporter`
- Pinned commit: `c491e4648ddd36bb6fd1d13b78207d08d033c493`
- Pinned tree: `b64966b591f8c4de2e9b8baece9f8a595c034363`
- Review date: 2026-07-28
- Status: doctor_capability_installed_upstream_independently_rejected_export_blocked

## Spec Gate

### Goal

Give Hermes a local, user-controlled macOS capability to assess readiness and, only after explicit human authorization at each sensitive boundary, help export the user's own WeChat contacts and chat history into local plaintext SQLite databases.

### Non-goals

- No silent access to WeChat data, account directories, chat content, contacts, encryption keys, Keychain, or process memory.
- No automatic `sudo`, password entry, Full Disk Access approval, WeChat re-signing, LLDB attachment, or memory scanning.
- No default MCP registration, background indexing, remote upload, telemetry, cloud processing, or external delivery.
- No bypass of macOS privacy controls, WeChat security controls, organization policy, law, or third-party rights.
- No claim of compatibility beyond versions actually probed.

### Source facts

- The upstream repository contains only `README.md` and `SKILL.md`; it is an orchestration recipe rather than a self-contained implementation. Its README links to an MIT `LICENSE`, but the pinned tree contains no `LICENSE` file, so copying its text/code carries a license-evidence gap.
- Upstream `SKILL.md:67-93` installs Homebrew/Python dependencies, clones one repository, downloads four files from another repository's moving `main`, compiles C, and registers an MCP server.
- `SKILL.md:115-136` instructs re-signing `/Applications/WeChat.app` with `sudo codesign` and running a memory key scanner with `sudo`.
- `SKILL.md:140-169` identifies an account directory, writes paths to `config.json`, and decrypts databases.
- `SKILL.md:258-314` asks the agent to patch dependency source code manually.
- Local readback: `/Applications/WeChat.app` exists at version `4.1.11`; Homebrew and Apple clang are present; `sqlcipher` is not currently installed; system `python3` is 3.9.6.
- Referenced bulk-export dependency `ylytdeng/wechat-decrypt` could not be cloned: GitHub returned HTTP 403 and a DMCA takedown notice. This source path is closed; no mirror search or bypass is permitted.
- Pinned `cocohahaha/wechat-decrypt-macos@316f8474c43dd064e575169ad84b96b8aac3282a` explicitly says automatic extraction is not working on WeChat 4.1.11 (`README.md:16-30`). This exactly matches the installed local WeChat version.
- The pinned extractor reads the WeChat database header (`extract_key.py:109-116`), scans process memory via Mach APIs (`145-218`, `274-326`), then prints the recovered key to stdout (`329-343`). Direct agent execution is prohibited.
- Its installer installs Homebrew/Python dependencies and automatically registers a user-scope Claude MCP server (`install.sh:26-56`); its setup script kills WeChat, re-signs it, repeatedly runs a sudo memory scan, and writes a predictable `/tmp/wx_extract.log` (`setup_key.sh:22-56`). These are not safe defaults.
- Its MCP server enumerates account databases and reads a plaintext key (`server.py:91-118`), then exposes list/read/recent/search/summary tools that return identifiers and message content (`server.py:362-703`). This is a broad privacy surface and remains default-off.

### Business and safety rules

1. Capability installation is separate from exporting real data.
2. Default mode is `doctor/readiness` and must not enumerate account identities or read message databases.
3. Every privileged or privacy-sensitive phase needs a fresh, exact human action: app re-sign, process-memory key extraction, source-data read, decryption, plaintext query, MCP exposure.
4. Hermes never reads, prints, stores in chat, or requests paste-back of encryption keys or `all_keys.json` contents.
5. Dependencies must be pinned to immutable commits and verified before execution; moving `main` downloads are forbidden.
6. Plaintext outputs must use a user-private directory with directory mode `0700` and file mode `0600`; no world/group-readable output.
7. Network access is closed during data discovery, key extraction, decryption, and querying. Any dependency fetch is a separate preparatory phase before real data handling.
8. MCP is default-off and cannot be exposed beyond loopback/user scope without a separate authorization and access-control review.
9. Every run produces a redacted receipt containing versions, counts, paths represented safely, and exit state—but never keys or message/contact content.
10. A WeChat update invalidates prior compatibility and key-extraction evidence; readiness falls back to `needs_review`.

### Negative acceptance cases

- Missing or unpinned dependency source blocks installation.
- Missing Full Disk Access or human privilege action returns a typed blocked state; no workaround is attempted.
- No real data path is opened during doctor/readiness.
- Key material is never included in tool output, logs, receipts, or model context.
- A symlinked output root, group/world-readable output, or path escaping the approved root is rejected.
- MCP registration is absent after ordinary capability installation.
- No network connection is made while processing real data.

### Evidence required

- Exact upstream commit/tree and source line review.
- Static network/command/permission/data-flow inventory of upstream and pinned dependencies.
- Hermes skill readback plus trigger/negative-trigger checks.
- Non-destructive doctor smoke proving no access to real WeChat account/chat data.
- Tests for command construction, path containment, permissions, redaction, no-network phases, and human-gate refusal.
- Independent review before enabling a real export path.

## Risk Classification

Severity semantics: the three `P0` rows below are **capability/acceptance blockers** for the requested real-export claim, not evidence of malicious code. The independent source auditor found no proven active exfiltration, backdoor, or immediately exploitable security P0 in the pinned two-file repository; it classified the concrete security/privacy defects as P1 and returned an overall **REJECT** for direct adoption/execution.

| Severity | Finding | Consequence | Decision |
|---|---|---|---|
| P0 | Exact local WeChat 4.1.11 key extraction is explicitly unsupported by the pinned available implementation | Re-signing/scanning cannot produce a verified export and can damage app identity/login permissions | Do not execute |
| P0 | Referenced bulk-export implementation is unavailable under a GitHub DMCA takedown | Recipe cannot be reproduced from its declared sources | Fail closed; no mirror/bypass |
| P0 | Experimental extractor prints the recovered key to stdout | Secret would enter terminal/agent logs and model context | Direct agent execution prohibited |
| P1 | Moving raw `main` downloads and unpinned clone are compiled/executed | Supply-chain substitution risk | Require immutable pins and review |
| P1 | One-click installer mutates Homebrew/Python and auto-registers broad MCP tools | Hidden persistence and large privacy blast radius | Do not run; MCP default-off |
| P1 | Setup kills/re-signs the daily-use app and uses repeated `sudo` memory scans with a predictable `/tmp` log | Integrity, login, privacy, and secret-log risk | Separate human gates; current path closed |
| P1 | MCP tools return contact identifiers and message content broadly | Private data can be pulled into arbitrary model turns | Require allowlists, limits, local-only scope, and separate authorization |
| P2 | Recipe tree lacks the `LICENSE` file linked from README | Copying has incomplete license evidence | Reimplement guarded contract; do not copy |
| P2 | Local system Python is 3.9.6 while pinned query server requires 3.10+ | Installer/runtime mismatch | Dependency preparation remains closed |

## Independent Review

- Verdict on copying or executing the upstream recipe: **REJECT**.
- Bound source: commit `c491e4648ddd36bb6fd1d13b78207d08d033c493`, tree `b64966b591f8c4de2e9b8baece9f8a595c034363`.
- File digests: `README.md=4a81e97c9e00200f57f7a3c0a554b47694280e8a29a8fa079cad00c176bbc221`; `SKILL.md=1475823d7965d8c85c310c04e289dab310d5183041f41d9293e82104d401fe85`.
- Independent P1 classes: unpinned network-to-root supply chain; destructive app re-signing without restoration; persistent key/plaintext exposure; global MCP/model-context exposure; fixed-path overwrite/symlink risk; irreproducible version drift; incomplete license closure.
- No independent claim was made that the code is actively malicious. The reject verdict is based on reproducibility, authority, privacy, integrity, and licensing boundaries.
- Full independent evidence: `/Users/charles/.hermes/cache/delegation/subagent-summary-0-20260728_194605_670658.txt`.
- Independent safe-adaptation design agreed with the implemented default: readiness only, no real-data enumeration, no privileged execution, no key visibility, no MCP registration, and no network during sensitive phases. It proposed additional offline supply-chain/gate/receipt utilities for a future implementation slice; these are intentionally deferred while no compatible legal export implementation exists.

## Objective / Model / Path

### Objective and cost

Success is a safe local capability, not merely copying the upstream prompt. Minimize privacy leakage, supply-chain risk, app integrity changes, and accidental plaintext exposure.

### Situation model

The upstream project is a high-level recipe that composes two external repositories and privileged macOS operations. It does not vendor or pin the implementation it runs. The local machine has WeChat 4.1.11, Homebrew, and clang, but lacks `sqlcipher`.

### Candidate paths

- **A — Copy upstream `SKILL.md` directly:** fast, but executes moving remote code, mutates WeChat, registers MCP by default, and lacks privacy/readback gates. Rejected.
- **B — Install upstream dependencies immediately and attempt export:** produces capability quickly but crosses sudo, app-signing, process-memory, real-data, and plaintext gates before review. Rejected.
- **C — Build a Hermes-owned guarded wrapper:** pin and audit sources; install only the user-local capability now; default to read-only doctor; keep privileged/data phases human-gated and default-off. Selected.

### Chosen path

Create one user-local Hermes skill with an owned readiness script and explicit phase gates. Do not install third-party runtime dependencies or touch WeChat/data during this capability-installation slice. Add pinned-source manifests and tests first; real export remains a later exact human-gated operation.

## Converge Matrix

| Claim | Evidence | State |
|---|---|---|
| Upstream source accessible and pinned | Git HEAD/tree readback above | PASS |
| Local prerequisites identified without reading chats | app/version/tool readback | PASS |
| Upstream security/data-flow audited | source-line inventory plus independent pinned-source review | MAIN_REVIEW_PASS_UPSTREAM_REJECT |
| Independent direct-adoption verdict | pinned source auditor | REJECT_UPSTREAM |
| Guarded Hermes skill installed | `wechat-local-export` skill readback | PASS |
| Doctor performs zero real-data reads | 5 focused tests + live JSON smoke; `data_access_attempted=false` | PASS |
| Real export works on WeChat 4.1.11 | requires later human gates and real-data acceptance | NOT_CLAIMED |
