---
type: backlog
layer: L3
status: active
created: 2026-05-06T18:07:23+08:00
project: local-brain-mempalace-derived
---

# P9 - Implementation Backlog

## P0 — 本轮必须完成

### P0.1 Artifact contract

Create project, P10 strategy, P9 backlog, executable playbook, review/provenance note, task proof ledger, evolution note, and atoms.

Acceptance checks:

- `python3 ~/.hermes/scripts/local_brain_mempalace_selfcheck.py --json`
- required files all exist。

### P0.2 Deterministic verification

Run local-first gates. This explicitly includes brainctl sync / reindex / search.

Acceptance checks:

- `python3 ~/.hermes/scripts/brainctl.py --json sync`
- `python3 ~/.hermes/scripts/brainctl.py --json reindex`
- `python3 ~/.hermes/scripts/brainctl.py --json search "MemPalace派生索引 P10 source of truth" --limit 8`
- structural audit stop gates: empty_dirs=[], top_level_no_index=[], parent_no_direct_md_top=[], broken_wikilinks_count=0, secret_pattern_hits=0。

### P0.3 Caveat governance

Record that four-model discussion was attempted but not fully certified.

Acceptance checks:

- review note contains `not_certified`。
- review note contains issue_ledger。
- review note states model agreement is not evidence。

## P1 — 低风险实验

### P1.1 Isolated MemPalace sample benchmark

Copy a tiny non-sensitive sample out of the vault and compare search quality.

Acceptance checks:

- Commands use `--palace /tmp/...` before subcommand。
- Commands include `--no-llm`。
- No file is written into `/Users/charles/Documents/brain` by MemPalace。

### P1.2 Chinese / bilingual query benchmark

Compare current `brainctl search` vs isolated embedding search with Chinese and mixed-language queries.

Acceptance checks:

- Query set and results written to `60-reviews/`。
- No promotion unless precision improves without recall/evidence loss。

## P2 — 未来 Hermes-native 工程化

### P2.1 `brainctl derived-index`

Implement rebuildable closet/tunnel/temporal-fact tables under `~/.hermes/memory/`。

Acceptance checks:

- Markdown remains canonical。
- derived index can be deleted and rebuilt。
- every derived fact has source file/block pointer。

### P2.2 Expiry and ghost-memory guard

Add valid_from/valid_to/source/confidence for mutable facts.

Acceptance checks:

- Preferences/project/task facts can expire or supersede。
- stale facts are never promoted to long-term memory without current evidence。

## Execution order

P0.1 → P0.2 → P0.3 → P10 review。Only after P0 passes may P1 experiments start。
