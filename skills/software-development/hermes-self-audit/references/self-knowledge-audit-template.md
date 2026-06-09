# Self-Knowledge Audit Template

Multi-model dispatch template for periodic Hermes self-knowledge audits.

## Dispatch Pattern

Use `delegate_task` with 3 parallel subagents, each analyzing from a different angle:

### Model A: Architecture Analysis

Goal: "Analyze Hermes's self-knowledge architecture for coherence."

Focus areas:
- Memory audit (active vs stale vs duplicate)
- Rule coherence (norms consistency, gaps, conflicts)
- Structural assessment (brains, skills, cron, profiles)

Output format: JSON with `memory_audit[]`, `rule_coherence{}`, `structural_assessment{}`, `concrete_actions[]`

### Model B: Efficiency Analysis

Goal: "Analyze Hermes's internal architecture for efficiency and compression."

Focus areas:
- Memory compression (merge opportunities, char savings)
- Knowledge distribution (what belongs where: memory vs skills vs profiles)
- Automation gaps (recurring problems → cron jobs)
- Technical debt (broken, stale, needs cleanup)

Output format: JSON with `memory_compression{}`, `knowledge_distribution{}`, `automation_gaps[]`, `technical_debt[]`

### Model C: User Perspective

Goal: "Think from the user's perspective about what should change."

Focus areas:
- Memory priority (what matters most to the user)
- Skill cleanup (which skills are actually useful)
- Brain assessment (essential vs nice-to-have vs unused)
- Task pool health (user priorities, archive candidates)

Output format: JSON with `memory_priority{}`, `skill_cleanup{}`, `brain_assessment{}`, `task_pool_health{}`, `top_3_actions[]`

## Synthesis

After all 3 models return:

1. Identify consensus points (all 3 agree)
2. Identify disagreements (need human decision)
3. Create prioritized action plan: low effort + high impact first
4. Present to user for approval before executing

## Data to Collect Before Dispatch

```bash
# Memory
python3 ~/.hermes/scripts/brainctl.py --json memory list 2>/dev/null

# Skills
ls ~/.hermes/skills/ 2>/dev/null

# Brains
ls ~/.hermes/brains/ 2>/dev/null

# Cron
hermes cron list 2>/dev/null

# Project profiles
ls ~/.hermes/project-profiles/ 2>/dev/null

# Health check
python3 ~/.hermes/scripts/health-check.py --json

# Task pool
python3 ~/.hermes/scripts/brain_task_orchestrator.py eligibility-check --json 2>/dev/null
```

## Typical Findings (from 2026-05-29 audit)

| Dimension | Finding | Consensus |
|-----------|---------|-----------|
| Memory | 14 entries, 2195/2200 chars (99.8% full) | All 3 agree: compress to 7-10 entries |
| Skills | 128 directories, 20+ irrelevant | All 3 agree: archive ML/CV/audio skills |
| Brains | 15 overlays, 5 unused | All 3 agree: core 4 + on-demand 5 |
| Task pool | 414 files, 2 dispatchable | All 3 agree: archive 60-80 historical |
| Cron | 48 jobs, 5 in error | All 3 agree: consolidate to ~35 |

## Memory Compression Technique

From 14 entries → 7 entries (2195 → 880 chars):

| New Entry | Merged From | Content |
|-----------|-------------|---------|
| 开发SOP | 1+2 | Dev standards + Hermes governance |
| UVISA | 3+5 | Paths + rules + MCP RPC |
| 任务池 | 4+6+11 | Evolution + sync + routing + parallel |
| 多模型 | 7+10 | Real external models + canonical IDs |
| Brain体系 | 8+12 | brainctl + overlays + backup |
| 运维 | 9+13+14 | Dashboard + hardware |
| 项目清单 | new | Profiles + skills overview |
