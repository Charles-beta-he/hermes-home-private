# 小程序游戏批量研发工厂

本地证据门禁驱动的小游戏研发工作区。

## 已落地

- `spec-packet.md`：目标、边界、规则与验收。
- `capability-graph.json`：玩法、内容、编译、实现、平台、发布能力图。
- `model-routing.json`：低成本/标准/高推理路由及升级规则。
- `04-prd/game-product-contract.md`：GameplayKernel、ContentPack、平台和商业化分层契约。
- `06-planning/research-development-flow.md`：从玩法假设到发布观察的研发流程。
- `07-build/work_package_compiler.py`：确定性单候选编译器。
- `07-build/batch_compile.py`：批次隔离编译器。

## 运行

```bash
cd /Users/charles/.hermes/workflows/product/mini-program-game-factory/07-build
python3 -m unittest -v test_batch_compile.py test_work_package_compiler.py
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

当前最高证据状态：`local_contract_verified`。未证明 Cocos 运行时、平台 SDK、审核、留存、收入或玩法乐趣。
