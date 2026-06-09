# UVISA Unified Iceberg + Multimodel Consensus

## Architecture

Three-layer classification for all UVISA Lark tasks (admin + C端 unified):

```
Layer 1: Deterministic iceberg analysis (free, instant)
  ↓ confidence=low / tier=M / scope=inferred
Layer 2: Multimodel consensus (2-3 real models via delegate_task)
  ↓ all tasks now classified
Layer 3: Control plane integration (dispatch score + preflight + work contract + dashboard)
```

## Layer 1: Unified deterministic classifier

**Script:** `~/.hermes/scripts/uvisa_lark_unified_classifier.py`
```bash
python3 ~/.hermes/scripts/uvisa_lark_unified_classifier.py \
  --input ~/.hermes/evidence/lark-sync/uvisa-app-2.0/live-tasks.json \
  --write-back --json
```

Replaces both `uvisa-admin-lark-fasttrack-closeout.py` (admin regex matrix) and `uvisa_c端_lark_classifier.py` (C端-only) with a single unified system. Semantic signal extraction with weight-based decision tree. No regex matching.

## Layer 2: Multimodel consensus

**Script:** `~/.hermes/scripts/uvisa_lark_multimodel_classifier.py`

### Running

```bash
# Dry-run: output review queue
python3 ~/.hermes/scripts/uvisa_lark_multimodel_classifier.py \
  --input ~/.hermes/evidence/lark-sync/uvisa-app-2.0/live-tasks.json \
  --dry-run --max-tasks 10 --json

# With write-back (after agent-side model calls)
python3 ~/.hermes/scripts/uvisa_lark_multimodel_classifier.py \
  --input ~/.hermes/evidence/lark-sync/uvisa-app-2.0/live-tasks.json \
  --max-tasks 10 --write-back
```

### CRITICAL: Model calling pattern

The script CANNOT call models directly from Python:

```python
# WRONG — consult_models.py requires state_file subcommand
subprocess.run(["consult_models.py", "--model", "gpt-5.5", "--prompt", "..."])
# → "error: argument cmd: invalid choice: 'gpt-5.5'"
```

```python
# CORRECT — use agent's delegate_task for real model calls
# Step 1: Script outputs review queue (--dry-run)
# Step 2: Agent calls delegate_task with empty toolsets
delegate_task(tasks=[
    {"goal": "Classify these 3 tasks as S0/S1/F/L/R/B/M ...", "toolsets": []},
    {"goal": "Classify these 3 tasks as S0/S1/F/L/R/B/M ...", "toolsets": []},
])
# Step 3: Agent aggregates votes, writes back
```

`consult_models.py` usage: `consult_models.py run <state_file> --tier T0 --quorum 3`
It's a full discussion/ratification system, not a simple model call proxy.

### Vote aggregation

```python
# Majority vote with defensive None handling
agreement_val = consensus.get("agreement") or 0  # None when no votes
# agreement = matching_votes / total_votes
# ≥67% = high agreement, use consensus tier
# <67% = low agreement, keep deterministic tier
```

### Pitfall: agreement can be None

When all model calls fail (empty votes), `consensus.get("agreement")` returns None.
Format string `f"{agreement_val:.0%}"` will crash on None.
Always: `agreement_val = consensus.get("agreement") or 0`

### Write-back format

```yaml
iceberg_tier: S0
iceberg_scope: simple_ui
iceberg_domain: asset
iceberg_confidence: multimodel_consensus
iceberg_multimodel_consensus: agreement=100%; deterministic=M; final=S0; models=mimo-v2.5-pro×2
```

## Layer 3: Control plane integration

Integrated into `brain_task_orchestrator.py`:

- **Dispatch score**: S0=+12, S1=+10, F=+8, L=-3, B=-15
- **Preflight gate**: lane=work + project but missing `source_weighting_policy_ref` → blocked
- **Work contract**: `uvisa_lark_work_contract.py` — L auto-adds `A-backend-contract`, B adds `A-human-confirmation`
- **Dashboard**: `brain_task_orchestrator.py dashboard --write` shows Iceberg Tier Distribution

## 2026-05-28 first run results

### Layer 1 output
| Tier | Count | Meaning |
|---|---|---|
| F | 22 | Frontend logic |
| L | 18 | Requires backend |
| M | 3 | Needs triage |
| S0/S1 | 0 | No simple UI tasks in C端 |

### Layer 2 multimodel consensus (3 tasks → 2 models)
| GUID | Deterministic | Consensus | Reasoning |
|---|---|---|---|
| 87bf89dc | M | S0 | 盈亏符号条件渲染 |
| f9806285 | M | S0 | 按design token实现弹窗 |
| 6906ef6e | M | S1 | 通知列表按交易类型分类 |

### Final distribution
S0=2, S1=1, F=19, L=17, B=0, M=0

## Why this replaces the old approach

| Dimension | Old admin regex matrix | Old C端 iceberg | New unified + multimodel |
|---|---|---|---|
| Scope | admin only | C端 only | admin + C端 unified |
| Method | regex keyword match | semantic weight tree | semantic + model consensus |
| Accuracy | 90% C端 misclassified as L | F=22, L=18 | F=19, L=17, S0=2, S1=1 |
| Low-confidence handling | none | none | 3-model majority vote |
| Cost | free | free | free for high-confidence, model calls for low |
