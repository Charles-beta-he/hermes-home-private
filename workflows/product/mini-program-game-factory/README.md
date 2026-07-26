# 小程序游戏批量研发工厂

本地证据门禁驱动的小游戏研发工作区。

## 已落地

- `spec-packet.md`：目标、边界、规则与验收。
- `capability-graph.json`：玩法、内容、编译、实现、平台、发布能力图。
- `01-discovery/hot-game-observatory.md`：热门玩法来源、证据状态机和人工采集方法。
- `source-registry.json`：平台榜单、试玩、官方案例和第三方数据源的采集频率与边界。
- `hot-game-observation-schema.json`：市场快照及机制卡约束。
- `model-routing.json`：低成本/标准/高推理路由及升级规则。
- `04-prd/game-product-contract.md`：GameplayKernel、ContentPack、平台和商业化分层契约。
- `06-planning/research-development-flow.md`：从玩法假设到发布观察的研发流程。
- `07-build/work_package_compiler.py`：确定性单候选编译器。
- `07-build/batch_compile.py`：批次隔离编译器。
- `07-build/hot_game_observatory.py`：热度新鲜度、独立来源和直接试玩门禁。
- `evidence/direct-capture-intake-template.json`：用户提供榜单截图/录屏和试玩证据时的导入模板。

## 运行

```bash
cd /Users/charles/.hermes/workflows/product/mini-program-game-factory/07-build
python3 -m unittest -v test_batch_compile.py test_work_package_compiler.py
python3 -m unittest -v test_hot_game_observatory.py
python3 hot_game_observatory.py \
  ../evidence/hot-game-snapshot-2026-07-26.json \
  --as-of 2026-07-26T12:00:00+08:00 \
  --output ../evidence/hot-game-receipt-2026-07-26.json
python3 work_package_compiler.py \
  --seed sample-seed.json \
  --routing ../model-routing.json \
  --output ../evidence/sample-work-package.json
```

批次输入是 seed 对象数组：

```bash
python3 batch_compile.py \
  --batch sample-batch.json \
  --routing ../model-routing.json \
  --output ../evidence/sample-batch-receipt.json
```

## 正确性边界

低成本模型输出始终是 candidate。通过相同的 schema、protected-surface、参数边界、rights、golden、运行时与人工门禁之前，不获得合并、送审或发布权限。

当前最高工程证据状态：`local_contract_verified`。当前最高市场状态：`recent_market_lead`，没有游戏满足 `verified_current_hot`。未证明 Cocos 运行时、平台 SDK、审核、留存、收入或玩法乐趣。
