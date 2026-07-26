# Converge Matrix

| Spec / acceptance claim | Artifact evidence | Test/readback evidence | Status | Remaining gap |
|---|---|---|---|---|
| 助手通过持续外部观测而非模型记忆识别热门玩法 | `source-registry.json`, `hot-game-observatory.md`, observation schema | snapshot source refs parse PASS | PASS（机制层） | 仍需周期性真实输入 |
| 实时热门不能由旧文章或单一来源自证 | freshness/independence/direct-play rules | observatory negative tests PASS | PASS | 无 7 天内客户端榜单证据 |
| 首批市场样本保持证据边界 | 2026-07-26 snapshot | receipt: verified 0 / recent 2 / stale 1 | PASS（诚实状态） | 缺直接榜单与试玩录屏 |
| 未验证市场线索不能进入玩法内核研发 | `market_loop_gate.py`, hypothesis candidates, capability graph | 全量 54 项测试 PASS；异步旧提交审查的 P1/P2 已在当前树逐项复核；receipt digest 绑定 snapshot/hypotheses/routing；本地媒体稳定性、摘要、大小与非空机制读回；相同原始 lineage 及任意已声明相同媒体摘要均归并；状态清单和机制必填字段有一致性测试；真实 receipt: accepted 0 / rejected 2；freeze/compile authority false | PASS | 获得 `verified_current_hot` 后仍需规格、模拟、golden、人工试玩 |
| 玩法、内容、平台、商业化边界独立 | `game-product-contract.md`, `capability-graph.json` | JSON parse PASS | PASS（规格层） | 运行时实现未做 |
| 低风险内容任务路由 low_cost | `model-routing.json`, `route_task` | `test_routes_allowlisted_content_generation_to_low_cost` PASS | PASS | 真实 provider 调用未做 |
| protected surface 自动升级 | `protected_surfaces`, `route_task` | protected change test PASS | PASS | 无 |
| 低置信度自动升级 | `confidence_below: 0.85` | low confidence test PASS | PASS | 阈值需未来数据校准 |
| 未知平台契约 fail closed | `unknown_platform_contract: blocked` | platform blocked test PASS | PASS | 官方平台契约待读取 |
| 内容不能覆盖玩法字段 | `_validate_content` | malicious override test PASS | PASS | 无 |
| 关卡参数必须在玩法允许范围内 | `tunable_parameters` | out-of-bounds test PASS | PASS | 可解性模拟待 R0 |
| 相同输入确定性编译 | canonical JSON + SHA-256 | deterministic tests PASS | PASS | 运行时随机性待 R0 |
| 换内容不改玩法摘要 | kernel/content 分离摘要 | content-swap test PASS | PASS | 运行时同 seed 重放待 R0 |
| 批量失败隔离 | `compile_batch` | accepted 2 / rejected 1 | PASS | 大批量性能未测 |
| 低成本产物仅为 candidate | `accuracy_contract`, authority flags | candidate-only test/readback PASS | PASS | 无 |
| 发布/送审/凭证/支付保持关闭 | authority fields | fresh CLI readback all false | PASS | 精确授权前持续关闭 |
| 玩法乐趣、留存、收入 | 风险与指标契约 | 无真实用户/平台证据 | BLOCKED | 需可玩版本、人工试玩和上线数据 |

## Closure

- Highest evidenced state: `local_contract_verified`
- Highest market state: `recent_market_lead`
- Workflow state: `blocked_at_fresh_market_runtime_and_platform_evidence`
- External side effects: closed
