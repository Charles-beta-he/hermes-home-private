---
name: hermes-self-audit
description: "Use when periodic self-knowledge audit for Hermes Agent — memory compression, skill cleanup, brain assessment, health monitoring. Use when memory is near-full, skills feel stale, or you need to assess Hermes's internal architecture coherence."
triggers:
  - "memory near full"
  - "skills stale"
  - "self audit"
  - "self knowledge"
  - "architecture review"
  - "memory compression"
  - "skill cleanup"
  - "brain assessment"
  - "health check"
  - "infrastructure health"
  - "拒绝自嗨"
  - "honest assessment"
  - "self-hype"
  - "真实评分"
  - "自检流程"
  - "动态自检"
  - "自我评分"
---

# Hermes Self-Audit

## Overview

Periodic self-knowledge audit for Hermes Agent — memory compression, skill cleanup, brain assessment, health monitoring. Use when memory is near-full, skills feel stale, or you need to assess Hermes's internal architecture coherence. This skill is maintained as a `reviewer`-shaped contract: it should guide evidence-grounded review, audit, critique, certification, or quality-gate work without stealing adjacent workflows or relying on unstated assumptions.

## When to Use

Use this skill when the user's request matches `hermes-self-audit` and requires evidence-grounded review, audit, critique, certification, or quality-gate work.

Do not use it for:
- generic one-off questions that do not need this workflow;
- neighboring specialist workflows with a narrower matching skill;
- durable memory or project-profile writes unless this skill explicitly governs that landing zone.

Methodology for periodic self-knowledge audits of Hermes Agent's internal architecture: memory, skills, brains, cron, task pool.

## When to Run

- Memory at 90%+ capacity (check: `python3 ~/.hermes/scripts/health-check.py --json`)
- Skill count exceeds 60 (check: `ls ~/.hermes/skills/ | wc -l`)
- Task pool dispatchable count drops to 0 while total > 50
- User reports "same problems repeating" or "can't find anything"
- After major infrastructure changes (new brain, new skill category, new cron)

## Self-Audit Methodology

### Step 1: Gather Current State

```bash
# Memory status
python3 ~/.hermes/scripts/brainctl.py --json memory list 2>/dev/null

# Skill count
ls ~/.hermes/skills/ | wc -l

# Brain overlays
ls ~/.hermes/brains/ | head -20

# Cron jobs
hermes cron list 2>/dev/null | head -50

# Health check
python3 ~/.hermes/scripts/health-check.py --json

# Task pool state
python3 ~/.hermes/scripts/brain_task_orchestrator.py eligibility-check --json 2>/dev/null
```

### Step 2: Multi-Model Analysis (Recommended)

Dispatch to 3 models in parallel for independent perspectives:

- **Model A (Architecture)**: Memory audit, rule coherence, structural assessment
- **Model B (Efficiency)**: Memory compression, knowledge distribution, automation gaps
- **Model C (User Perspective)**: Memory priority, skill cleanup, task pool health

Each model returns structured JSON. Synthesize consensus points.

### Step 3: Memory Compression

Target: keep under 1800/2200 chars (80% headroom for growth).

Compression rules:
1. Merge entries with same domain (e.g., all task pool entries → one)
2. Move procedural knowledge to skills (commands, configs, workflows)
3. Move project-specific knowledge to project profiles
4. Drop entries with <1 reference in last 10 sessions (use session_search)
5. Abbreviate: use `§` as entry separator, avoid full sentences

Entry format: `主题: 关键词1; 关键词2; 关键词3。§`

### Step 4b: Source Leak Detection

Hermes's own source checkout lives at `~/.hermes/hermes-agent/`. Sometimes the agent creates `.hermes/` directories *inside* the source repo (e.g., during plan writes or test runs), which pollutes the checkout and can confuse git.

```bash
# Check for .hermes inside the source repo
find ~/.hermes/hermes-agent -name ".hermes" -type d 2>/dev/null

# If found, move contents to proper ~/.hermes/ location, then remove the nested dir
```

This is distinct from the normal `~/.hermes/` directory — it's specifically about `.hermes` appearing inside `~/.hermes/hermes-agent/`.

### Step 5: Skill Cleanup

Criteria for archiving:
- No trigger in last 30 sessions
- Irrelevant to user's career goals
- Superseded by a newer skill
- Experimental/prototype that never matured

Criteria for keeping:
- User triggers it weekly+
- Prevents high-frequency errors
- Directly serves active projects
- Cross-session procedural value

## Health Check Infrastructure

### Current: Modular Self-Diagnostic System (`~/.hermes/diagnostics/`)

Replaced the monolithic `health-check.py` with a modular, registry-driven system.

```bash
python3 ~/.hermes/diagnostics/runner.py              # Full check, terminal
python3 ~/.hermes/diagnostics/runner.py --json        # JSON output
python3 ~/.hermes/diagnostics/runner.py --mode status # One-liner for hermes status
python3 ~/.hermes/diagnostics/runner.py --fix         # Apply SAFE auto-fixes
python3 ~/.hermes/diagnostics/runner.py --fix --confirm # SAFE + MODERATE fixes
```

Architecture:
```
~/.hermes/diagnostics/
├── runner.py              # Core runner (parallel, hot-reload registry)
├── check-registry.json    # Check definitions (enabled/weight/severity/tier)
├── check_base.py          # Shared utilities for check scripts
├── trend.py               # Trend tracking + degradation detection
├── checks/                # Independent check scripts (add/remove freely)
│   ├── kanban-integrity.py
│   ├── codex-auth.py
│   ├── priority-mode.py
│   ├── task-file-bloat.py
│   ├── cron-health.py
│   ├── memory-usage.py
│   ├── log-file-size.py
│   ├── disk-space.py
│   ├── kanban-sync.py
│   └── taskpool-schema.py
└── fixes/                 # Auto-fix scripts (3-tier safety)
    ├── reindex-kanban.py      # SAFE
    ├── reset-priority-mode.py # SAFE
    └── rotate-logs.py         # SAFE
```

Adding a new check: write script in `checks/`, add entry to `check-registry.json`, done.
Registry is re-read every run (hot-reload) — no restart needed.

See `references/modular-diagnostics.md` for full architecture details.

### Legacy: Health Check Script (`~/.hermes/scripts/health-check.py`)

Older monolithic pattern. Still exists but superseded by the diagnostics runner.
See `references/health-check-pattern.md` for the legacy pattern documentation.

## Known Issue Registry Format

```markdown
## Issue N: <Name>

- **Severity**: CRITICAL|HIGH|MEDIUM
- **Symptom**: <what the user sees>
- **Detect**: <shell command that outputs ISSUE or OK>
- **Fix**: <exact command to fix>
- **Last seen**: <date>
- **Fix count**: <how many times fixed>
```

## Anti-Self-Hype Methodology

**Core principle**: Every claim of "done" must have verifiable evidence. If you can't prove it works, it doesn't work.

### Honest Scoring Framework

When assessing architecture, code quality, or system readiness, use this scoring scale:

| Score | Meaning | Evidence Required |
|-------|---------|-------------------|
| 1-3 | Broken/Missing | Component doesn't exist or crashes |
| 4-5 | Partial/Unstable | Exists but untested, unverified, or disconnected |
| 6-7 | Functional | Tested, integrated, but has known gaps |
| 8-9 | Production-ready | Full test coverage, documented, battle-tested |
| 10 | Exemplary | Industry benchmark quality |

**Scoring rules:**
- Start at 5 (assume average), then adjust up/down with evidence
- Never score above 6 without test coverage > 50%
- Never score above 8 without integration tests + documentation
- Never score 10 — there's always room for improvement
- Each score must cite specific evidence (test results, metrics, user feedback)

### Self-Hype Detection Checklist

Before claiming "complete" or "done", run this checklist:

```text
□ Is there a test that proves it works?
□ Can someone else reproduce the result?
□ Is the documentation accurate?
□ Have I actually run the code (not just written it)?
□ Am I inflating the version number?
□ Am I counting files created as "progress"?
□ Would I trust this in production?
□ Did I verify on the target environment (not just my dev machine)?
```

If any answer is "no", the work is NOT done.

### Common Self-Hype Patterns to Avoid

| Pattern | Symptom | Fix |
|---------|---------|-----|
| Version inflation | Bumping major version for minor changes | Version follows semver strictly |
| File count progress | "Created 10 files" as achievement | Count working features, not files |
| Architecture worship | Beautiful diagrams ≠ working system | Require end-to-end test |
| Premature completion | "All tests pass" when no tests exist | Verify test existence before claiming |
| Echo chamber validation | Only checking your own work | Use external verification |

## Dynamic Self-Check Flow

Automated self-check process that runs before any "completion" claim:

### Phase 1: Existence Check
```bash
# Does the code actually exist?
find . -name "*.py" -newer .git/HEAD -exec python3 -m py_compile {} \;

# Does it have tests?
find . -name "test_*.py" | wc -l
```

### Phase 2: Integration Check
```bash
# Can it run?
python3 -c "import module_name"

# Does it connect to dependencies?
curl -s http://localhost:PORT/health
```

### Phase 3: Evidence Check
```bash
# Run actual tests (not just syntax check)
python3 -m pytest tests/ -v --tb=short

# Check test coverage
python3 -m pytest --cov=module --cov-report=term-missing
```

### Phase 4: Honest Assessment
- Score each component using the Honest Scoring Framework
- List specific evidence for each score
- Identify what's actually missing (not what you plan to add)

### Phase 5: Report
Generate a report with:
- Component scores with evidence
- Gap analysis (what's missing vs what's claimed)
- Honest readiness assessment
- Specific next actions (not vague plans)

## Pitfalls

- Don't auto-fix health check findings — detect-only, report to human
- Don't compress memory below 7 entries — minimum viable context
- Don't archive skills that are in active cron job skill lists
- Don't delete brain overlays — mark as unused, let human decide
- Memory entries must be declarative facts, not instructions
- When in doubt about a skill's relevance, check `session_search` for usage patterns
- **Don't claim completion without evidence**: "All tests pass" requires actual tests. "Version 2.0.0" requires actual features. "Working" requires actual verification.
- **Don't count files as progress**: Creating 10 empty files is not 10x progress. Working features with tests are progress.
- **Don't self-validate**: Run external verification (tests, curl, screenshots). Your own judgment is biased.
- **Don't inflate scores**: A score of 8/10 requires production-grade evidence. If you can't prove it, score lower.

## Self-Improvement Pipeline Operations

This skill is also the umbrella for the former `hermes-self-improvement-pipeline` workflow. Use `references/hermes-self-improvement-pipeline.md` when the audit turns into operating or debugging `~/.hermes/scripts/self-improvement-pipeline.py`: ROI scoring, stuck counters, signal sources, benchmark regressions, and evolution action plans.

Default rule: self-improvement pipeline work is part of Hermes self-governance. Diagnose the pipeline as one feedback loop — signal sources → scoring → action plan → execution/verification — rather than keeping a separate one-session skill for each pipeline incident.

Key checks:
- pipeline JSON output has actionable items or a classified skip reason;
- stuck-counter and ROI caps are understood before lowering thresholds;
- benchmark runner stdout is not truncated before JSON parsing;
- cron schedules are staggered enough to avoid provider 429 bursts;
- generated action plans are verified by read-back, not assumed.

## Self-Healing Architecture Design

When designing new self-healing components or diagnosing infrastructure issues, use the academic-grounded framework in `references/self-healing-architecture.md`. It covers MAPE-K, Erlang Supervisor, Design by Contract, credit-based backpressure, and K8s probes — plus a design template, health score thresholds, and existing script inventory.

## References

- `references/health-check-pattern.md` — Health check script + audit log pattern
- `references/self-knowledge-audit-template.md` — Multi-model audit dispatch template
- `references/full-health-audit-8step.md` — Complete 8-step health audit procedure (state.db, memory, source leak, kanban, selfcheck, git, cron, profiles)
- `references/self-healing-architecture.md` — Academic frameworks (MAPE-K, Erlang, Meyer, Akidau) + design template for self-healing systems
- `references/anti-self-hype-checklist.md` — Honest scoring, self-hype detection, dynamic self-check flow
- `references/project-self-check-pipeline.md` — Project-level self-check template for non-Hermes projects
- `references/hermes-self-improvement-pipeline.md` — Self-improvement pipeline operations, ROI debugging, signal sources, benchmark regressions, and stuck-unblocking patterns

## Verification Checklist

- [ ] Preconditions, scope, and tool availability were checked before following this workflow.
- [ ] The key output artifacts, commands, or side effects were verified by read-back or direct inspection.
- [ ] Any remaining uncertainty, blocker, or human handoff was stated explicitly.
- [ ] Findings include evidence, severity/rubric calibration, and false-positive controls.
