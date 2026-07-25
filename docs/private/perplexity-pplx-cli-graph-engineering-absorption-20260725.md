# Perplexity `pplx` CLI + Graph Engineering absorption SSOT

- Status: adapted Hermes skill installed and CLI binary installed locally; runtime search is not yet authenticated or API-smoked
- Captured: 2026-07-25
- Authority: user authorized joint absorption of the Graph Engineering pattern and the official Perplexity `pplx-cli` skill

## Objective

Add Perplexity web search as a **pluggable external-read CapabilityNode** for Hermes research/coding graphs, without treating one provider as truth authority, leaking credentials, or allowing search breadth to create uncontrolled fan-out.

## Canonical sources

### Skill repository

- URL: https://github.com/perplexityai/api-platform-developers
- Pinned commit: `906630d8b9787b29afd693699fe34c1b86adf2de`
- Skill path: `skills/pplx-cli/SKILL.md`
- Skill SHA-256: `d5e1f66eb1defa4dec1ceab91debf4ece6c14da5de44b7ebf4b12db60e059703`
- Repository license: Apache-2.0

### CLI distribution repository

- URL: https://github.com/perplexityai/perplexity-cli
- Pinned release: `v0.2.2`
- Release commit: `62db7273ae14be73f3b00743752e8340ef40467a`
- Runtime version: `2026.07.23.1784814721+8fdc4c2`
- macOS arm64 asset SHA-256: `e976478fcfec51f36f5b0f28d6477ea042323294284e06b02a2e9b1b339c1773`
- Installer SHA-256: `a9d22373f2b5cf018e998c7727b1ad41ebf8583c3d2e787bc2c9aaab06d388c4`
- Distribution boundary: repository contains installer and prebuilt binaries, not implementation source; no LICENSE file was present at the pinned release. Personal local evaluation is distinct from redistribution or source audit.

## Verified source facts

1. The official skill exposes `pplx search web` and `pplx content fetch`.
2. Success contract: exit 0 and one JSON object on stdout.
3. Failure contract: exit 1, empty stdout, one JSON error object on stderr.
4. API key can be supplied by `PERPLEXITY_API_KEY` or interactive `pplx auth login`; environment takes precedence.
5. The installer downloads a platform asset, pins subsequent downloads to a resolved tag, verifies SHA-256, installs without sudo, and writes a local receipt.
6. The pinned macOS binary hash matched GitHub release metadata and ran `--version`/`--help` in an isolated no-key HOME.
7. The macOS binary is ad-hoc/linker signed, has no TeamIdentifier, and `spctl -a -t execute` returned `rejected`. This does not prove malware, but it blocks treating the artifact as notarized/trusted-by-Gatekeeper.

## Claim calibration

| Public claim | Decision |
|---|---|
| “Agent gains web search” | Conditional: skill + binary + valid API key + provider availability are all required. |
| “Wider/deeper than Context7” | Not established as a universal fact. Perplexity targets broad live web search; Context7 targets versioned library documentation. They are complementary adapters with different corpora and trust models. |
| “Best for latest frameworks/cold errors/complex research” | Plausible routing heuristic; requires citation/source-reality verification and cost limits. |
| “Install this Skill and it works” | Incomplete: the CLI binary and authentication are separate runtime prerequisites. |

## Capability graph landing

```text
objective
  -> query planner
  -> provider router
       -> pplx web-search adapter (external read, metered)
       -> native web/x/docs adapters
  -> deterministic result normalizer
  -> source-reality/citation gate
  -> local-code correlation
  -> independent verifier
  -> answer/evidence packet
```

### `pplx_search_adapter` contract

- Consumes: bounded query, optional domain/date scopes, result limit, output directory
- Produces: normalized JSON result plus source URLs and provider metadata
- Side effects: external read, metered API use, optional local JSON write
- Authority: no credential entry by the agent; no external write/publish
- Budget: explicit query count/result limit/token/output-size cap
- Failure: preserve typed stderr error; never synthesize fake results
- Cannot prove: source correctness, completeness, current page state after cache, or superiority over other search providers

## Governance rules

1. Use fake-edge testing before parallel search; independent queries may fan out, reformulations of one query remain one search node.
2. Search nodes never grade their own source quality.
3. Prefer provider diversity for high-impact claims; Perplexity is an adapter, not the truth authority.
4. Every material claim must retain URL/citation provenance and source-reality checks.
5. Keep credentials outside chat, memory, skills, receipts, and logs.
6. Do not read or print credential stores.
7. External search costs and retries must be budgeted; no unbounded Agent fleet.
8. Runtime activation remains distinct from skill installation.

## Review and installation state

- Adapted Hermes skill: installed and enabled at `research/pplx-cli`; local skill readback succeeded.
- Graph integration: class-level reference landed under `workflow-capability-graph/references/external-search-adapters-in-execution-graphs.md` and linked from the umbrella skill.
- CLI binary: installed at `~/.local/bin/pplx`; exact installed SHA-256 `e976478fcfec51f36f5b0f28d6477ea042323294284e06b02a2e9b1b339c1773`.
- Install receipt: `~/.config/pplx/pplx-receipt.json`; SHA-256 at installation readback `34eca407887c8828548d57918ec5cc4ab76b62741d0bfdb7ae2e6a34dc7d565a`.
- Version smoke: `pplx 2026.07.23.1784814721+8fdc4c2`.
- Negative auth smoke with isolated empty HOME/config: exit `1`, stdout `0` bytes, typed `AUTHENTICATION` JSON on stderr.
- Runtime trust boundary: exact release hash verified and isolated help/version smoke passed, but Gatekeeper trust/notarization is absent.
- Independent adversarial review: dispatched as `deleg_c6d4a8cf`; until it returns, the installed runtime remains degraded-review / not independently certified.
- Authentication/API smoke: blocked on human-owned Perplexity API credential; no key was requested, read, or entered.
- Rollback: remove only `~/.local/bin/pplx` and `~/.config/pplx/pplx-receipt.json`; any human-owned credential store remains out of scope.
