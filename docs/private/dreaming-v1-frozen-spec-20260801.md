# Hermes Dreaming v1 — Frozen Architecture & Loop Contract

freeze_status: APPROVED
approved_by: user
approved_at_utc: 2026-08-01T05:19:32Z
source_report_sha256: b9c15c967494ef60391aec806d9df352f929ef947d2d9de3354826f684cd9d90
implementation_base_head: 9e22bade18f29f6699af5d240a4436c388f59e6a
fresh_fetched_origin_master: 52a83af9858b49de015164379a3bf59cbac68168
branch: claude/dreaming-loop-20260801
risk_class: local_reversible

## Goal

把夜间任务从“直接修改 active skill 的单脚本”收敛为可解释、候选态优先、独立晋升、可回滚的 Dreaming 控制环：

`trigger → lease/idempotency → ownership preflight → selection attempt → candidate-only generation → evaluation → pending promotion/reject → receipts → readback`

## Frozen invariants

1. `~/.hermes/state` 只存数据；可执行逻辑必须 Git 追踪、可测试、可审查。
2. cron 只触发，不成为第二状态机。
3. background/nightly 不得直接写 `~/.hermes/skills/**`；只能产生 candidate。
4. active skill 仅可由独立 promotion gate 写入；必须 baseline hash、回归证据、ownership guard、atomic replace、写后 readback、rollback digest 全部通过。
5. `last_attempt_at` 与 `last_advanced_at` 分离；无推进也必须更新尝试状态，并进入 cooldown/no-progress demotion。
6. generator 能力与 evaluator 要求必须一致；unsupported finding 必须显式分类，不得无限重试。
7. `job_success`、`effective_audit`、`candidate_generated`、`state_advanced`、`promoted` 分开表达。
8. 所有阶段产生 typed receipt；`no_state_change` 必须落到明确 reason taxonomy。
9. owner/profile/path/symlink 任一不满足时 fail-closed；EUID 0 + 非 root HERMES_HOME 硬拒绝 mutation。
10. 多模型意见不是晋升权限，也不是事实认证。

## Non-goals / current hard boundaries

- 本轮不批量修复现存 root-owned 文件；这需要单独、精确、可回滚的权限修复授权。
- 不 push、不 deploy、不改外部系统。
- 不把 advancement rate 当单一优化目标。
- 不追认 2026-07-30/31 exact root writer。
- 不允许 background 自动 promotion。

## Implementation loops

### Loop A — Transitional safety and observability (current slice)

- RED/GREEN：stage receipt schema 与 reason taxonomy。
- RED/GREEN：selector attempt state、cooldown、no-progress demotion、deterministic diversity；旧 selector 保留 shadow projection 便于对照。
- RED/GREEN：generator/evaluator vocabulary 对齐与 satisfiability 分类。
- RED/GREEN：candidate-only generation，证明 active SKILL.md bytes 不变。
- RED/GREEN：ownership preflight/post-readback gate，覆盖 root/non-root、symlink escape、owner mismatch、unreadable target。
- no-agent wrapper 只根据 typed receipt 判定，不再解析人类输出作为主事实。

### Loop B — Runtime integration

- 将 cron 收缩为 `hermes dreaming run --trigger cron --idempotency-key ...`。
- 引入 ephemeral lease、crash recovery、重复 idempotency key 的幂等 readback。
- 迁入 Hermes 主仓库 `agent/dreaming/` 和 `tests/dreaming/`；过渡脚本只做代理。

### Loop C — Event store and governed promotion

- SQLite/WAL event store 成为 SSOT；JSONL 仅兼容导出。
- 独立 evaluator/consolidator/promotion receipts。
- foreground/profile-owned promotion gate；高风险 skill 保留人工门禁。

## Acceptance matrix for Loop A

| Claim | Required evidence |
|---|---|
| repeated no-change target no longer permanently dominates | deterministic selector tests with timestamps/cooldown and multi-target fixture |
| every attempt advances attempt metadata | DB/state readback after accepted, rejected, unsupported outcomes |
| generator can satisfy its own structural evaluator | focused RED→GREEN tests for `示例` and `约束` vocabulary |
| nightly cannot mutate active skill | byte hash before/after integration test; candidate exists under isolated HERMES_HOME |
| bad ownership/path fails closed | negative tests; zero active/candidate residual write before authorization boundary |
| health semantics are typed | wrapper tests consume receipt and distinguish candidate/reject/promotion/error |
| no regression | focused pytest, py_compile, relevant script suite |
| independent review | Codex verdict bound to frozen diff digest |

## Rollback

All implementation remains on `claude/dreaming-loop-20260801`. Before any runtime cutover, restore the prior cron target and script bytes from base HEAD `9e22bade18f29f6699af5d240a4436c388f59e6a`. Candidate/state additions are quarantinable data and must never be required to restore active skills.

## Converge rule

No loop is DONE until every material claim above has code/test/readback evidence. Any ownership ambiguity, active-write residue, stale-digest review, or missing runtime readback closes as HOLD/BLOCKED rather than success.
