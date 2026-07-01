# Numeric Guardrails (4-Model Certified)

Extracted from `/Users/charles/.hermes/skills/autonomous-ai-agents/hermes-pipeline/SKILL.md` on 2026-07-01T08:56:29.614759+00:00 during full core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

## Numeric Guardrails (4-Model Certified)

When using hermes-pipeline for autonomous/long-running execution, enforce these numeric bounds:

| Parameter | Default | Configurable | Purpose |
|-----------|---------|-------------|---------|
| appetite_timeout | 30min | 15/60/120min per task type | Shape Up time budget per task |
| max_retry | 3 | - | After 3 failures: escalate + block |
| human_escape | 2 block OR 3 crash | - | Auto-pause pipeline + notify user |
| max_runtime | 3600s/task | - | Single task max execution time |
| lease_ttl | 900s | - | Worker claim validity |
| heartbeat_interval | 120s | - | Worker heartbeat frequency |
| state_source | SQLite envelope bus | - | Single source of truth, cron triggers tick only |
| OKR↔proof | sha256 artifact | - | Each KR must link to envelope DONE proof |

These guardrails were 4-model certified (Claude + GPT-5.5 + DeepSeek + MiMo) on 2026-05-10. See `references/numeric-guardrails.md` in the multi-model-thinking skill for the full ratification artifact path.
