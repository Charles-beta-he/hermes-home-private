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
- `07-build/cocos_work_package_adapter.py`：校验上游摘要并生成本地、candidate-only 的 Cocos Creator 3.8 integration packet 与物料化 manifest；不调用 Creator。
- `runtime/cocos/`：固定 Cocos 来源身份、integration schema、纯 TypeScript GameplayKernel/ContentPack/PlatformPort、fail-closed LocalPlatformStub，以及本地 contract-tested 的 `wx`/`tt` official adapter candidates；后者不等于官方 SDK E2E。
- `07-build/cocos_project_generator.py`：从已验证 candidate 和 Node-tested sources 确定性生成、摘要验证 Creator 3.8 project candidate；不调用 Creator。
- `07-build/cocos_delivery_gate.py`：非执行 build preflight 与严格 DevTools handoff verifier；缺 CLI/version/AppID/exported config/authority 时不生成命令。
- `evidence/cocos-node-runtime-smoke.json`：固定 seed/input 的 Node runtime readback，明确 `official_sdk=false`。
- `evidence/cocos-build-preflight-blocked.json`：当前真实缺失前提和 `command=null` 的 fail-closed receipt。
- `06-planning/cocos-integration-workflow.md`：C1–C10 的 Cocos、平台构建、DevTools、真机和发布证据阶段。
- `08-shipping/devtools-handoff-template.json`：默认 blocked、无 AppID/凭据的开发者工具交接模板。
- `07-build/batch_compile.py`：批次隔离编译器。
- `07-build/hot_game_observatory.py`：热度新鲜度、主体绑定、证据 lineage、直接媒体摘要读回、摘要绑定人工分类复核和榜单/试玩媒体角色隔离门禁；仅有远端 URL 或未复核的直接证据不会晋级 `verified_current_hot`。
- `07-build/direct_capture_intake.py`：把本地榜单/试玩媒体绑定为绝对路径、SHA-256 和字节数，摘要不匹配时 fail closed；intake 后仍需人工填写摘要绑定的 `content_review`，模型不得代填。
- `07-build/market_loop_gate.py`：将已验证市场观察转换为抽象 `kernel_hypothesis` 候选；要求显式 `proposed_changes`，并扫描候选变化、抽象机制及差异化描述中的保护面；不开放内核冻结、工作包编译或发布。
- `evidence/market-kernel-hypotheses-2026-07-26.json`：首批抽象机制候选，明确排除不可复制表达。
- `evidence/market-loop-receipt-2026-07-26.json`：市场→研发 loop 的确定性门禁读回。
- `evidence/source-packet.json`：三条真实来源 URL、发布时间/访问时间与 snapshot/receipt 摘要的本地证据包。
- `evidence/timestamped-source.json`：市场快照、评估时点和 receipt 的时间绑定；明确不将间接材料升级为客户端直接证据。
- `evidence/direct-capture-intake-template.json`：用户提供榜单截图/录屏和试玩证据时的导入模板。
- `07-build/reference_ad_experiment.py`：用户授权 reference-ad 的 candidate-only 实验通道校验器/receipt 构建器；绑定本地媒体 SHA-256（拒绝符号链接与摘要不匹配）、强制 `verified_current_hot=false` 与 `rank_claimed=false`、要求可见事实/推断/未知与 clean-room 可复用/不可复制边界、两关 warm-up + skill-gate；该通道永远不能满足 `verified-current-hot` market-to-kernel 门禁，不开放内核冻结、Cocos 构建、送审或发布。
- `experiments/stack-path-runner/`：原创两关浏览器 vertical slice「叠桥冲刺」（依赖为零的 ESM 确定性内核 + Canvas UI）；仅为本地 candidate 实验，不含来源素材，不等于 Cocos/抖音运行时验证。

## 运行

```bash
cd /Users/charles/.hermes/workflows/product/mini-program-game-factory/07-build
python3 -m unittest -v test_batch_compile.py test_work_package_compiler.py
python3 -m unittest -v test_direct_capture_intake.py test_hot_game_observatory.py test_market_loop_gate.py
python3 direct_capture_intake.py \
  ../evidence/direct-capture-draft.json \
  --output ../evidence/direct-capture-bound.json
python3 hot_game_observatory.py \
  ../evidence/hot-game-snapshot-2026-07-26.json \
  --as-of 2026-07-26T12:00:00+08:00 \
  --output ../evidence/hot-game-receipt-2026-07-26.json
python3 market_loop_gate.py \
  --snapshot ../evidence/hot-game-snapshot-2026-07-26.json \
  --hypotheses ../evidence/market-kernel-hypotheses-2026-07-26.json \
  --routing ../model-routing.json \
  --as-of 2026-07-26T12:00:00+08:00 \
  --output ../evidence/market-loop-receipt-2026-07-26.json
python3 work_package_compiler.py \
  --seed sample-seed.json \
  --routing ../model-routing.json \
  --output ../evidence/sample-work-package.json
python3 cocos_work_package_adapter.py \
  --work-package ../evidence/sample-work-package.json \
  --profile ../runtime/cocos/cocos-integration-profile.json \
  --output-root ../evidence/cocos-local-candidate
python3 cocos_project_generator.py \
  --verify ../evidence/cocos-creator-project-candidate
python3 cocos_delivery_gate.py preflight \
  --project ../evidence/cocos-creator-project-candidate \
  --platform douyin

export PATH="$HOME/.nvm/versions/node/v24.14.0/bin:$PATH"
cd ../runtime/cocos/runtime-core
npm test
npm run smoke
```

Reference-ad 实验通道与原创浏览器 vertical slice：

```bash
cd 07-build
python3 -m unittest -v test_reference_ad_experiment.py
python3 reference_ad_experiment.py \
  --observation ../evidence/ad-tests/2026-07-30-douyin-7665976730670091561/reference-ad-observation.json \
  --mechanic-card ../evidence/ad-tests/2026-07-30-douyin-7665976730670091561/mechanic-card.json \
  --output ../evidence/ad-tests/2026-07-30-douyin-7665976730670091561/reference-ad-experiment-receipt.json

export PATH="$HOME/.nvm/versions/node/v24.14.0/bin:$PATH"
cd ../experiments/stack-path-runner
node --test
```

Cocos 适配器的输出是本地候选 bundle。输出根目录必须尚不存在；它不会调用 Cocos Creator、平台 SDK 或开发者工具，也不会打开构建、真机、送审或发布权限。

批次输入是 seed 对象数组：

```bash
python3 batch_compile.py \
  --batch sample-batch.json \
  --routing ../model-routing.json \
  --output ../evidence/sample-batch-receipt.json
```

## 正确性边界

低成本模型输出始终是 candidate。通过相同的 schema、protected-surface、参数边界、rights、golden、运行时与人工门禁之前，不获得合并、送审或发布权限。

当前最高工程证据状态：`creator_project_candidate_materialized`，并行证明了 `official_platform_adapter_contract_tested`（仅 fake-SDK 本地契约，不是官方 SDK E2E）；两者均属于本地 mutable slice，尚未获得新 commit/tree 独立认证。当前最高市场状态：`recent_market_lead`，没有游戏满足 `verified_current_hot`。已证明摘要绑定的 Cocos 3.8 integration packet、Node GameplayKernel smoke、LocalPlatformStub、wx/tt adapter candidate 契约和包含 adapter source 的 19-file Creator import candidate；当前 preflight 以 exit 2、`command=null` 精确阻塞于 Creator CLI/version、AppID、editor-exported config 和 build authority。未证明 Creator 已导入/构建、官方平台 SDK E2E、开发者工具、真机、审核、留存、收入或玩法乐趣。
