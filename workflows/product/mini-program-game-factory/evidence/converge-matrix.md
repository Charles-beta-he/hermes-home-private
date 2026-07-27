# Converge Matrix

| Spec / acceptance claim | Artifact evidence | Test/readback evidence | Status | Remaining gap |
|---|---|---|---|---|
| 助手通过持续外部观测而非模型记忆识别热门玩法 | `source-registry.json`, `hot-game-observatory.md`, observation schema | snapshot source refs parse PASS | PASS（机制层） | 仍需周期性真实输入 |
| 实时热门不能由旧文章或单一来源自证 | freshness/independence/direct-play rules | observatory negative tests PASS | PASS | 无 7 天内客户端榜单证据 |
| 首批市场样本保持证据边界 | 2026-07-26 snapshot | receipt: verified 0 / recent 2 / stale 1 | PASS（诚实状态） | 缺直接榜单与试玩录屏 |
| 未验证市场线索不能进入玩法内核研发 | `hot_game_observatory.py`, `direct_capture_intake.py`, `market_loop_gate.py`, hypothesis candidates, capability graph, `h4-local-verification-certificate.json` | commit `0747403e84e6bf98b4683f2b8901c166ee804357` / tree `7dd6e9a6ea82b538f084d7d6a56fb51ac23b6f02` immutable-archive 68/68 PASS；两路独立 APPROVE 且无 material findings；receipt digest 绑定 snapshot/hypotheses/canonical routing；直接媒体需稳定摘要/大小、榜单与试玩摘要隔离、7 天内试玩时间及摘要绑定人工分类；所有来源绑定 canonical registry；候选必须显式 proposed changes 并扫描三类字段；真实 receipt: accepted 0 / rejected 2；所有高权限 false | PASS（本地契约已认证） | 不证明市场真实热门；人工复核者身份尚无密码学认证；获得 `verified_current_hot` 后仍需规格、模拟、golden、人工试玩 |
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
| 未有 promotion receipt 的任意模型产物仅为 candidate | `accuracy_contract`, authority flags | low-cost 与 standard candidate-only tests PASS | PASS | promotion receipt 尚未实现，故不能自动提升 |
| 发布/送审/凭证/支付保持关闭 | authority fields | fresh CLI readback all false | PASS | 精确授权前持续关闭 |
| Cocos 只消费摘要有效的引擎中立 WorkPackage | `cocos_work_package_adapter.py`, profile, packet schema | tampered digest 与错误引擎/版本负例 PASS | PASS（本地 mutable slice） | 尚未绑定新 commit/tree 独立认证 |
| Cocos candidate 物料化确定且不打开权限 | `evidence/cocos-sample-candidate/` | 4/4 文件 SHA-256、manifest digest readback PASS；Cocos adapter tests PASS | PASS（本地候选） | 不证明 Creator 工程或运行时 |
| GameplayKernel 和 LocalPlatformStub 可脱离 Creator 运行且不伪造官方能力 | `runtime/cocos/runtime-core/`, `evidence/cocos-node-runtime-smoke.json` | Node 24.14.0 strict build；10/10 tests PASS；固定 seed/input `state_sha256=6d45b138...`；`official_sdk=false`、`rewardGranted=false` | PASS（Node runtime） | 不证明 Creator runtime 或官方 SDK |
| Creator 3.8 project candidate 确定、文件闭包完整且可静态编译 | `cocos_project_generator.py`, `evidence/cocos-creator-project-candidate/` | 18-file manifest、`project_digest=54198717...`、重复生成等价、CLI verify、generated TypeScript compile、tamper/symlink negatives PASS | PASS（import candidate） | Creator import/preview/build 未执行 |
| Build preflight 缺前提时不执行、不泄漏 AppID、不生成命令 | `cocos_delivery_gate.py`, `evidence/cocos-build-preflight-blocked.json` | exit 2；5 个精确 blocker；`command=null`；fake executable 未执行；version/config/AppID/authority/symlink negatives PASS | PASS（fail-closed preflight） | 需 Creator、AppID、editor-exported config、exact build grant |
| DevTools handoff 只接受 digest-bound 人工/设备事实且不开放后续权限 | `cocos_delivery_gate.py`, `devtools-handoff-template.json` | strict fields、artifact digest、platform target、device readback、unknown field、symlink、authority、external-stage negatives PASS | PASS（verifier contract） | 无真实 build artifact、DevTools 或设备 receipt |
| Cocos Creator 构建、DevTools、真机与平台发布分阶段 | C1–C10 workflow、CapabilityGraph、handoff template | Creator build/DevTools/device/upload/review/publish 仍 blocked；所有 Cocos/platform authority false | PASS（边界） | 需 exact Creator、官方 SDK/target、平台和人工证据 |
| 玩法乐趣、留存、收入 | 风险与指标契约 | 无真实用户/平台证据 | BLOCKED | 需可玩版本、人工试玩和上线数据 |

## Closure

- Highest evidenced state: `creator_project_candidate_materialized` (Node runtime smoke and fail-closed build preflight are also evidenced; current mutable local slice)
- Current mutable-slice regression: Python unittest `98/98 PASS`; Node tests `10/10 PASS`; Python compile `17/17 PASS`; JSON parse `39/39 PASS`; deterministic project digest and 18-file set PASS
- Highest certified state: `local_contract_verified`
- Highest market state: `recent_market_lead`
- Workflow state: `blocked_at_fresh_market_creator_devtools_device_and_external_authority`
- External side effects: closed
- Cocos integration candidate: `evidence/cocos-sample-candidate/candidate-manifest.json`
- Cocos project candidate: `evidence/cocos-creator-project-candidate/project-manifest.json` (`project_digest=54198717068524d21f2935fca3d7a4ac0efafa3097dfce2f7d79abd77d95e268`)
- Node runtime receipt: `evidence/cocos-node-runtime-smoke.json`
- Build preflight receipt: `evidence/cocos-build-preflight-blocked.json` (`command=null`)
- H4 local verification certificate: `evidence/h4-local-verification-certificate.json` (only the earlier reviewed tree; market and current Cocos slice certification remain blocked)
