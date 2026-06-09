---
title: "铁板架构: 32→5 cron jobs 整合"
priority: P1
lane: work
status: done
created_at: 2026-05-11T01:30:00+08:00
ratification: 4_model_certified (Claude+GPT+DeepSeek+MiMo)
source: complex-giant-systems + GenericAgent analysis
---

# 铁板架构: 32→5 Cron Jobs 整合

## 多模型认证: 4/4 通过

## 目标
将 32 个独立 cron job 整合为 5 层统一调度，消除冗余，补齐缺口。

## 5 层架构

### Layer 1: Ops (every 30min)
整合: pipeline_tick + controller + executor + bridge + orchestrator selfcheck
脚本: iron_plate_ops.py --tick
消除: R1 (orchestrator selfcheck 重复)

### Layer 2: Health (every 6h)
整合: V(x) + self-scan + smoke + usage + memory selfcheck
脚本: iron_plate_health.py
消除: R2 (进化监控重叠), R4 (smoke重叠)

### Layer 3: Evolve (daily 02:00)
整合: skill-steward + self-improvement + pa-evolution + failure-taxonomy + planner-triage
脚本: iron_plate_evolve.py
消除: R3 (失败分析重叠), G8 (PA进化孤立)

### Layer 4: Watchdog (every 10min)
整合: cron-health + missed-run + trace-ratio + dead-man-switch
脚本: iron_plate_watchdog.py
补齐: G3 (dead man's switch)

### Layer 5: Report (daily 08:00)
整合: daily-digest + GC + eval-audit + canary
脚本: iron_plate_report.py
补齐: G2 (集中仪表盘), G10 (统一日志)

## 需修复
- G1: 6个job的script参数空格bug → wrapper脚本
- G5: 依赖排序 (Layer 1 先于 Layer 2)
- G7: retry/escalation (失败自动重试)
- G6: model规格统一

## 从 GenericAgent 采纳
1. 5层记忆密度分层 (L0-L4)
2. 任务后SOP/skill结晶
3. 文件IPC子代理隔离

## 验证标准
- [ ] 32→5 cron jobs
- [ ] 0 冗余
- [ ] 0 报错
- [ ] V(x) >= 0.95
- [ ] 4/4 模型认证

## Second-pass absorption closure (2026-05-20)

### Canonical source
- Local source: this note plus `06-治理与评审/reviews/2026-05-19-prior-external-analysis-quality-audit.md`, which flagged missing source/stop-condition for the historical “32→5 cron jobs” consolidation idea.
- External/conceptual source: `complex-giant-systems + GenericAgent analysis` as recorded in frontmatter; there is no single stable upstream repository or paper URL attached to this note, so the local analysis note is the canonical source of record.

### Decision
- Decision: `reject` the historical 32→5 bulk cron consolidation as a direct implementation target; `monitor` the smaller control-plane health ideas.
- Rationale: current Hermes no longer exposes the historical 32 live cron jobs through the `cronjob` tool (`cronjob list` returned `count: 0`), while health/coverage is now measured through `v_state.py`, `kanban_coverage.py`, scheduler/kanban tools, and targeted selfcheck scripts. Recreating five monolithic `iron_plate_*.py` jobs would be a stale architecture migration without a live source set.

### Landing surface
- Brain/task note: this section is the canonical closure for the old iron-plate consolidation proposal.
- Current operational surfaces: `cronjob list`, `/Users/charles/.hermes/scripts/v_state.py`, `/Users/charles/.hermes/scripts/kanban_coverage.py`, `cron-missed-run-guard.py`, `skill-steward.py`, and Hermes/kanban selfchecks. These absorb the useful monitoring intent without collapsing unrelated jobs into five mega-jobs.

### Verification evidence
- `cronjob(action="list")` returned `success=true`, `count=0`, `jobs=[]` in this worker run.
- `python3 /Users/charles/.hermes/scripts/v_state.py --json` exited `0` with `V=0.64`, `grade=DEGRADED`, `cron=1.0`, `kanban=1.0`, and bottleneck `orchestrator`; this proves current diagnosis is componentized rather than a missing cron-consolidation pass.
- File search under `/Users/charles/.hermes/scripts` found no `iron_plate_*.py` scripts; this is expected after rejecting direct consolidation.

### Stop-condition / anti-drift boundary
- Stop when source, decision, landing, verification, and this boundary are present; do not keep this historical proposal open solely because the original 32→5 checklist remains unchecked.
- Anti-drift: do not create five new consolidated cron wrappers unless a fresh live inventory shows duplicated active jobs and a bounded migration plan proves each wrapper has owner, schedule, failure semantics, and rollback evidence.
