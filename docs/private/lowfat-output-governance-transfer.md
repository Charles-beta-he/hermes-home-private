# lowfat Output Governance — Transferable Patterns

## Quick Reference

**Source:** zdk/lowfat (Rust, Apache-2.0, v0.6.8)
**Evaluation date:** 2026-06-06
**Full evaluation:** /Users/charles/.hermes/evidence/envelopes/49db96f18211/lowfat-hermes-evaluation.md

## Key Transferable Patterns

### 1. Token-Budget Truncation (HIGH priority)
Replace byte-based limits with token-based. Add `estimate_tokens()` to
tool_output_limits.py. Use char/4 heuristic or tiktoken.

### 2. Command-Specific Filters (HIGH priority)
Add `tool_output.filters` to config.yaml. Per-command regex keep/drop rules.
Targets: git, kubectl, npm, docker, pytest.

### 3. Savings Telemetry (MEDIUM priority)
Log per-tool-call (tool_name, tokens_in, tokens_out, truncated, savings_pct).
Surface in `/stats` CLI command.

### 4. Conditional Routing (MEDIUM priority)
Exit != 0 → pass through raw (conservative default).
Output > large_threshold → aggressive filters.
Output < small_threshold → passthrough.

## What NOT to Transfer
- Declarative filter DSL (high effort, Python+config sufficient)
- Structural pruning (niche, fragile to schema changes)

## Implementation Order
Phase 1: Token budgets (1-2 days, biggest ROI)
Phase 2: Command filters (2-3 days)
Phase 3: Telemetry (1 day)
Phase 4: Conditional routing (1 day)

## Expected Impact
Phase 1 alone: 15-30% savings
All phases: 40-60% savings on typical workloads
