**独立对抗审查完成（精确提交 0747403e）**

**Verdict: APPROVE（无 P0/P1/P2 material findings）**

### 审查执行（严格只读不可变快照）
- 首尾验证 commit/tree/父提交：0747403e84e6bf98b4683f2b8901c166ee804357（tree 7dd6e9a6...）← 1246033a4...
- 仅使用 `git archive 7dd6e9a6...` + `git show` 提取到 `/tmp/review-0747403e-proper`（零工作树/索引/外部系统修改）
- 目标目录全覆盖：`workflows/product/mini-program-game-factory/07-build/*` + `source-registry.json` + `model-routing.json` + `evidence/*` + `capability-graph.json`
- 运行仓库原有测试（68 passed）
- 编写并在 `/tmp` 执行 7 个完整负例（覆盖用户指定所有对抗向量）

### 核心机制审查结果
- **evidence-state-machine**（hot_game_observatory.py + market_loop_gate.py + work_package_compiler.py + direct_capture_intake.py）：
  - 7 天新鲜度 + `_source_within_days` + `fresh_direct_rank` + `direct_gameplay` 三重 gate
  - `_independent_lineages` 使用 Union-Find（independence_key + evidence_digest 联合）
  - `_digest_file`：`os.lstat` + `O_NOFOLLOW` + before/after `_stable_identity`（dev/ino/size/mtime_ns）
  - content_review：human + reviewer_id + classification + reviewed_at≤7d + review_digest==media_digest 严格匹配
- **来源/媒体真实性边界**：
  - source-registry.json 作为 SSOT，`_canonical_source_registry` + source_type/evidence_level 强制映射
  - direct 必须 registry_source_key 绑定 + 主体绑定 + 摘要校验
  - 媒体复用/旧媒体/自报 fresh 全部阻断
- **权限隔离**：
  - 所有 receipt/gate 硬编码 `authority: {may_freeze_kernel:false, may_compile_work_package:false, may_submit_platform:false, may_publish:false, may_enter_credentials:false, may_pay:false}`
  - `authority_boundary` 字符串显式声明边界
  - capability-graph 明确市场证据仅到 `kernel_hypothesis`

### 负例测试结果（/tmp/neg-tests/neg_test_adversarial.py）
全部 PASS（按设计阻断）：
- old_media_self_reported_fresh
- media_reuse_across_lineages（同 digest → lineages=0）
- spoof_source_type_evidence_level
- symlink_or_toctou_attempt
- content_review_spoof
- market_gate_perm_boundary
- receipt_digest_vs_snapshot

### 创建的文件（仅 /tmp，只读）
- `/tmp/review-0747403e-proper/...`（精确 tree 不可变提取）
- `/tmp/neg-tests/neg_test_adversarial.py`
- `/tmp/review-verdict-0747403e.md`（完整中文报告）

### 说明
- 无 material findings（file:line + 可执行复现 + 观察 + 最小修复 均为 0）
- 该 APPROVE **仅证明本提交在 evidence-state-machine、来源/媒体真实性边界、权限隔离上的对抗鲁棒性**；**明确不证明任何市场真实热门程度**，不构成外部数据背书。
- 审查全程符合“不可变快照 + /tmp 负例 + 零修改”要求。

审查结束。