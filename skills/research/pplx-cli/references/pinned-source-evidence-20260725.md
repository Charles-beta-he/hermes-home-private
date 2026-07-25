# Pinned source and runtime evidence — 2026-07-25

- **Scope:** source-specific evidence for the `pplx-cli` Wrapper.
- **Applicability:** verifying the installed v0.2.2 candidate and calibrating trust claims.
- **Anti-condition:** do not reuse these hashes for later releases.
- **Falsifier:** any release/tag/asset drift requires a new evidence record.

## Official Agent Skill

- Repository: `https://github.com/perplexityai/api-platform-developers`
- Commit: `906630d8b9787b29afd693699fe34c1b86adf2de`
- File: `skills/pplx-cli/SKILL.md`
- File SHA-256: `d5e1f66eb1defa4dec1ceab91debf4ece6c14da5de44b7ebf4b12db60e059703`
- Repository license: Apache-2.0

## CLI distribution

- Repository: `https://github.com/perplexityai/perplexity-cli`
- Release: `v0.2.2`
- Release commit: `62db7273ae14be73f3b00743752e8340ef40467a`
- Runtime version: `2026.07.23.1784814721+8fdc4c2`
- macOS arm64 asset SHA-256: `e976478fcfec51f36f5b0f28d6477ea042323294284e06b02a2e9b1b339c1773`
- Installer SHA-256: `a9d22373f2b5cf018e998c7727b1ad41ebf8583c3d2e787bc2c9aaab06d388c4`

The distribution repository exposed installer scripts and prebuilt binaries but no implementation source or LICENSE file at this tag. Therefore:

- release identity and observable CLI behavior were verified;
- implementation security was not source-audited;
- the skill's Apache-2.0 license must not be projected onto the separate binary distribution;
- redistribution rights for the CLI binary were not established.

## Local verification

- Downloaded asset hash matched GitHub release metadata.
- `file`: Mach-O 64-bit executable arm64.
- `pplx --version`: PASS.
- `pplx --help`: PASS in isolated no-key HOME.
- no-auth negative probe: exit 1, stdout empty, typed `AUTHENTICATION` JSON on stderr.
- macOS code signature: ad-hoc/linker signed; no TeamIdentifier.
- Gatekeeper assessment: rejected.

A matching checksum proves exact release bytes, not malware absence or Apple notarization.

## Independent verifier and remediation

- Review handle: `deleg_c6d4a8cf`
- Verdict: `CONDITIONAL_PASS`
  - adapted Skill installation: conditional pass;
  - fixed-tag, independently hashed, unauthenticated local binary installation: conditional pass;
  - search/fetch without authentication: fail;
  - source audit and redistribution rights: not proven.
- Post-review hardening:
  - removed moving `latest | sh` as a valid pinned-install path;
  - added endpoint/key/install-override fail-closed guards;
  - narrowed JSON stdout/stderr claims to business commands and verified auth failure only;
  - added symlink/collision checks, same-directory temporary files, atomic rename, and rollback evidence;
  - published install receipt schema `hermes_pplx_install_receipt_v2` atomically with mode `0600`.
- Current installed binary SHA-256: `e976478fcfec51f36f5b0f28d6477ea042323294284e06b02a2e9b1b339c1773`.
- Current receipt SHA-256 after hardening: `0bd6c4282fa59e38687fe8f38825f0908397b486f3f6c1def8e779f50f1635bc`.

This clears the independent-review gate only for the scoped, unauthenticated local installation. Runtime API usability and source-level trust remain unverified.
