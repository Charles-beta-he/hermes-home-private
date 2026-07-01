# 关键 Pitfalls

Extracted from `/Users/charles/.hermes/skills/software-development/multi-model-architecture/SKILL.md` on 2026-07-01T08:55:33.664327+00:00 by generic core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

## 关键 Pitfalls

1. Patch ID 必须确定性: sha1(file|op|body), 不含 model_name
2. Claude -p JSON nesting: wrapper→result→fence→inner JSON (双反序列化)
3. state.json 紧凑 (2-3KB): >4KB 分散注意力
4. Provider diversity: select_pair 必须不同 provider
5. Backfill 不改 is_synthetic: 保护 real-only 口径
6. YAML 重复 key: 最后出现覆盖 → grep 重复项
7. Memory 满: 压缩/删除过时条目, 合并重复
8. agent_protocol seq 计数器: 必须是 per-chain_id 而非 per-(chain_id, agent_id) — 否则不同 agent 在同一 chain 中 seq 都从 1 开始，无法排序。
9. agent_protocol envelope.chain_id: wrap() 中 auto-gen 的 chain_id 必须写入 envelope 块——仅当 explicitly passed 才写入的 bug 导致后续消费者丢失链式追溯。
10. model-router cold start: 只有所有候选都 cold 时才强制 epsilon=1；若 gpt-5.5 等 warm model 已有足够 trace，保留 ε-greedy，否则会因新增 cold 候选随机绕开 Codex 主力。
11. select_pair reviewer narrowing: select_model 必须支持 candidate_override；否则 reviewer 过滤 diverse_reviewers 后又被 pricing candidate_groups 覆盖，可能选回 producer 本身。
12. consult_models.py 真多模型落地: 非 shadow 模式必须通过模型专属 adapter 调用（Claude→claude-cli；Codex/MiMo→hermes chat --provider openai-codex/xiaomi），不能再用 Claude prompt 冒充所有 planner。用 `HERMES_MULTI_BRAIN_OFFLINE=1` 只做 adapter dry-run。
13. ensemble-vote execute=True 也要做 provider-aware 调用：从 pricing.models 解析 provider 后传 `hermes chat --provider`；Hermes stdout 可能带 `session_id:` 前缀，解析 verdict 时要从 stdout 中提取 JSON object，不能直接 `json.loads(stdout)`。
14. cross-patch.py 双模式: `execute` = orchestration framework (`actual_model_calls=false`); `run` = script_actual (真实 producer/reviewer), 默认 dry-run, `--apply` 才写文件, `--verify` 失败回滚。`--apply` 无 `--verify` 时 fail closed (返回 rejected), 除非显式 `--force-no-verify`。
15. provider 可用性检查: `_model_available()` 必须查三层 (shell env → .env file → CLI auth)。只查 shell env 会漏掉 .env 中的 XIAOMI_API_KEY 和 Claude CLI session。结果写入 `state/unavailable_providers.jsonl` 做审计。
16. cross-patch 安全测试必须覆盖: 非唯一匹配拒绝、--apply 无 verify 拒绝、verify pass 写入、verify failure 回滚、cost tracking。5 个测试是最低要求。
17. pricing.py promo TTL: promotion 在 7 天内到期时必须 log warning, 否则会静默回归到全价 (如 DeepSeek 2.5x 折扣到期后 4x 涨价)。
18. model-router select_model 输出应包含 `unavailable_candidates` 字段, 供可观测性追踪。
19. score_provider 短路: health=0 直接返回 0, 不计算其他维度 (避免给不可用 provider 高分)。
20. get_best_provider 兜底: 全部评分=0 时 fallback 到 get_available_providers (紧急模式)。
21. 动态降级注入: synthetic fallback entry 的 model 字段用 provider 名 (非具体模型名), 由 resolve_provider_client 解析。
22. reliability 维度: cost 权重从 0.20 降到 0.10, 避免便宜但幻觉重的模型 (如 DeepSeek V4) 过度受益。hallucination_rate > 0.5 时 reliability 归零。
23. get_dynamic_reliability 永远不超过 baseline: min(dynamic, baseline), 防止正向漂移。
