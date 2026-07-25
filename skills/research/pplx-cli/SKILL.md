---
name: pplx-cli
description: Use when live broad-web search or page-content fetch via Perplexity can complement native web/docs/X research, especially for recent frameworks, obscure errors, GitHub discovery, or bounded multi-source technical research; also use to inspect or set up the official pplx CLI without exposing credentials.
version: 1.0.1
source_repo: https://github.com/perplexityai/api-platform-developers
source_commit: 906630d8b9787b29afd693699fe34c1b86adf2de
source_skill_sha256: d5e1f66eb1defa4dec1ceab91debf4ece6c14da5de44b7ebf4b12db60e059703
license: Apache-2.0
metadata:
  hermes:
    tags: [perplexity, web-search, content-fetch, research, cli, external-read]
    related_skills: [web-research, context-engineering-os, workflow-capability-graph, xurl]
---

# Perplexity `pplx` CLI

## Scope and boundary

- **Scope:** domain-level reusable Wrapper for Perplexity's official public `pplx` CLI across research and coding tasks.
- **Applicability:** broad live-web discovery or page fetch when direct official sources/native adapters are insufficient and metered external reads are authorized.
- **Anti-conditions:** do not use for secrets/private pages, unbounded fan-out, source-free truth claims, external writes, publishing, deployment, or lifecycle mutation.
- **Falsifier:** narrow or retire this wrapper if the CLI contract, official distribution identity, auth model, or result quality no longer matches verified behavior.

Primary pattern: **Wrapper**. Secondary pattern: **Pipeline adapter**.

The CLI exposes:

- `pplx search web` — broad live web search;
- `pplx content fetch` — cleaned page-content retrieval.

It is a provider adapter, not a truth authority. Results must pass citation and source-reality verification before supporting material claims.

## Routing

Use when:

- native web search is unavailable, shallow, or insufficient;
- the task concerns current frameworks, obscure errors, GitHub projects, APIs, or multi-source technical research;
- normal page extraction failed;
- a capability graph needs a bounded external-search node.

Prefer narrower sources when available:

- official docs for authoritative API contracts;
- versioned library-documentation systems for package-specific questions;
- `x_search` for current X discussion;
- direct repository files/releases/issues for code and release claims.

Do not claim that Perplexity universally replaces or outperforms Context7-like systems. Perplexity targets broad current-web discovery; Context7-like systems target curated/versioned package documentation. Route by source need.

## Secret safety

Check only non-secret readiness:

```sh
command -v pplx
pplx --version
```

Never read or print credential files. Never ask the user to paste an API key into chat. Never place a key in commands, history, task records, receipts, memory, skills, or logs.

If auth is absent, stop at a human gate. The user may authenticate outside the agent session:

```sh
pplx auth login
```

Or the human may securely set `PERPLEXITY_API_KEY`. The agent must not type or inspect its value. It may check only whether a variable is present, never print it.

Before any normal Perplexity API call, fail closed if any endpoint/key/install override is unexpectedly present unless the user has explicitly approved that exact override:

```text
PPLX_SDK_BASE_URL
PPLX_SDK_API_KEY
PPLX_INSTALL_BASE_URL
PPLX_INSTALL_PATH
```

Do not claim that the binary always connects only to `https://api.perplexity.ai` or that all key-bearing paths are redacted. Those are upstream behavioral claims until public source or independent dynamic evidence proves them.

## Installation gate

Do not execute an uninspected moving `latest` script through `curl | sh`.

1. Resolve the official GitHub release.
2. Download manifest, checksums, installer, and exact platform asset to a temporary/evidence directory.
3. Pin the release tag before downloading the binary; do not use the current installer to claim installation of a fixed historical tag because it resolves `latest` at execution time.
4. Compare installer and asset digests with GitHub release metadata where available.
5. Verify the asset against `SHA256SUMS` and an independently pinned expected digest.
6. Inspect platform/signing state (`file`, `codesign`, `spctl` on macOS).
7. Reject target/receipt symlinks and non-regular-file collisions; explicitly fix the install target instead of inheriting an unknown `PPLX_INSTALL_PATH`.
8. Write a unique temporary file in the target directory, set permissions, verify digest and `--version`, then atomically rename it into place. If replacing an existing binary, record its digest and preserve a rollback path.
9. Publish the receipt through a same-directory temporary file plus atomic rename, then re-read the installed hash and receipt.

A matching checksum proves release-byte identity, not that a closed binary is safe. If macOS reports ad-hoc signing, no TeamIdentifier, or Gatekeeper rejection, disclose it and do not call the binary notarized or Apple-trusted.

Default uninstall scope:

```text
~/.local/bin/pplx
~/.config/pplx/pplx-receipt.json
```

Human-owned stored credentials are separate and require exact removal authority.

## Search

```sh
pplx search web "kubernetes pod OOMKilled causes" -n 5
```

For large results:

```sh
pplx search web "kubernetes pod OOMKilled causes" \
  -n 5 --output-dir out --stdout-preview=200
```

Expected business-command success contract for the pinned/verified CLI version:

- applies only to `pplx search web` and `pplx content fetch`;
- exit `0`;
- stdout should parse as exactly one JSON object;
- search output resembles `{hits: [{url, title, domain, snippet?, ...}], total, saved_to?}`.

`--version`, `--help`, installer, auth, and update output are outside this JSON contract.

Rules:

- `--stdout-preview` requires `--output-dir` or `PPLX_OUTPUT_DIR`.
- Extra positional queries are reformulations of one search, not distinct topics.
- Date flags use `MM/DD/YYYY`.
- Do not combine `--recency-filter` with explicit date bounds.
- Consult `pplx search web --help` instead of guessing flags.

## Fetch

```sh
pplx content fetch https://example.com/article
```

- HTTP(S) URLs only.
- Check `error` and `is_paywall` before trusting `content`.
- `--no-cache` forces a live fetch.
- `--html` may be large; pair it with saved output and a preview.
- Returned content is provider evidence, not automatic proof of origin truth.

## Failure contract

For `search web` and `content fetch`, upstream declares failure as exit `1`, empty stdout, and a JSON error object on stderr. The pinned no-auth probe independently verified that shape only for the `AUTHENTICATION` path; other failure classes remain unverified.

```json
{"error":{"code":"AUTHENTICATION","message":"...","command":"...","hint":"..."}}
```

Parsers must:

1. use process exit status as the first signal;
2. capture stdout and stderr separately;
3. parse JSON fail-closed;
4. preserve raw bounded diagnostics when schema parsing fails;
5. not assume every command or every failure emits exactly one JSON object.

Branch on `error.code` when it is valid. Never fabricate results or silently downgrade a failed search into a confident answer.

## Capability-graph contract

```yaml
id: pplx_search_adapter
consumes: [bounded_query, optional_domains, optional_dates, result_limit]
produces: [normalized_json, source_urls, provider_metadata]
side_effects: external_read_and_metered_api_use
budget: [query_count, result_limit, output_bytes, retries]
gates: [auth_ready, source_reality, citation_coverage, cost_budget]
cannot_prove: [source_correctness, completeness, universal_provider_superiority]
```

Apply the fake-edge test before parallelism. Independent source questions may fan out; repeated reformulations of one question stay in one search node. A fresh verifier checks claim support instead of trusting the search node's ranking.

## Artifact contract

```yaml
consumes: [research question, optional scope, local project context]
produces: [JSON search/fetch result, source URLs, optional local evidence file]
verifies: [exit status, JSON shape, source reality, citation support]
cannot_prove: [truth of every source, exhaustive recall, provider superiority]
```

## Verification checklist

- [ ] `pplx --version` succeeds and installed bytes are rehashed.
- [ ] No credential value or credential-file content entered context.
- [ ] Query count, result limit, retries, and output size are bounded.
- [ ] Failure stderr is parsed and no result invented.
- [ ] Material claims retain URLs and are checked against direct sources.
- [ ] Search, reducer, and verifier responsibilities remain separate.
- [ ] External writes and unrelated side-effect gates remain closed.

## Provenance and license boundary

Adapted from the official Apache-2.0 `pplx-cli` Agent Skill in `perplexityai/api-platform-developers`, pinned source commit and source-file digest recorded in frontmatter. Hermes modifications are explicitly disclosed here and cover credential isolation, pinned-install verification, platform-trust disclosure, cost/fan-out governance, source-reality verification, and capability-graph contracts.

The separate CLI distribution repository did not contain source code, a LICENSE, SBOM/provenance attestation, or reproducible-build evidence at the reviewed tag. Local end-user evaluation of the vendor binary does not establish rights to modify, mirror, bundle, or redistribute it. Do not package the binary into Hermes or a public artifact without explicit vendor licensing and provenance.
