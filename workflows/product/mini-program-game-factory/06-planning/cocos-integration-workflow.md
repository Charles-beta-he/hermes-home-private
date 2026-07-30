# Cocos Engine 整合工作流

## 已选技术边界

- 唯一游戏制作运行时：Cocos Creator 3.8 系列。
- 上游 `WorkPackage` 保持引擎中立。
- `cocos_work_package_adapter.py` 只生成摘要绑定的本地候选包，不修改真实 Cocos 项目，也不调用 Creator 或平台 SDK。
- 微信与抖音共享 GameplayKernel、ContentPack 和 Presentation；PlatformAdapter、构建交接和发布证据分别维护。

## 阶段与门禁

| 阶段 | 输入 | 输出 | 必须证据 | 当前状态 |
|---|---|---|---|---|
| C1 profile frozen | Cocos 源码调研、用户技术选择 | `cocos-integration-profile.json` | 3.8 系列、固定 commit、MIT、authority=false | completed_contract_only |
| C2 integration planned | digest-valid WorkPackage + profile | `CocosIntegrationPacket` | 确定性摘要、candidate-only | implemented |
| C3 candidate materialized | integration packet | 本地 candidate bundle | 文件 SHA-256、manifest readback | implemented |
| C4 project candidate | verified candidate + Node-tested sources | 19-file Creator 3.8 import candidate，含 official adapter source | project manifest、deterministic regeneration、TypeScript compile | implemented_local_candidate；Creator import blocked |
| C5 playable loop | kernel/content | Node 中的固定 seed 单关卡闭环 | kernel/runtime tests、runtime smoke、state SHA-256 | implemented_node_only；Creator runtime 与人工试玩 blocked |
| C6 platform port | typed PlatformPort | LocalPlatformStub + `tt`/`wx` adapter candidates | stub 明示 official_sdk=false；adapter fake-SDK contract tests 覆盖 namespace、shape、login code、typed error 与广告完成回执 | local_contract_tested；official SDK/Creator/device E2E blocked |
| C7 deterministic build | project candidate + exact Creator/config/AppID/authority | preflight receipt 或平台构建产物 | 序列化参考与 editor patch 分离；executable/config SHA-256 绑定；非执行 preflight、命令绑定 configPath、官方 CLI success exit code `36`、产物摘要 | preflight implemented and currently blocked；build not executed |
| C8 DevTools/device | 构建产物 | 导入/模拟器/真机 receipt | 开发者工具和真机读回 | blocked |
| C9 upload/review | 人工授权、平台账号 | upload/review receipt | 精确外部授权、状态回读 | blocked |
| C10 publish/rollback | 审核通过、发布授权 | 线上版本/回滚 receipt | 发布版本回读、回滚路径 | blocked |

## 本地可执行入口

```bash
cd /Users/charles/.hermes/workflows/product/mini-program-game-factory/07-build
python3 cocos_work_package_adapter.py \
  --work-package ../evidence/sample-work-package.json \
  --profile ../runtime/cocos/cocos-integration-profile.json \
  --output-root ../evidence/cocos-sample-candidate

export PATH="$HOME/.nvm/versions/node/v24.14.0/bin:$PATH"
cd ../runtime/cocos/runtime-core
npm test
npm run smoke

cd ../../../07-build
python3 cocos_project_generator.py \
  --verify ../evidence/cocos-creator-project-candidate
python3 cocos_delivery_gate.py preflight \
  --project ../evidence/cocos-creator-project-candidate \
  --platform douyin
```

输出目录必须不存在，且不能是符号链接。工具生成：

- `input/work-package.json`
- `generated/gameplay-kernel.json`
- `generated/content-pack.json`
- `integration-packet.json`
- `candidate-manifest.json`

这些文件与后续 project candidate 证明本地候选输入、纯玩法运行时和 Creator 导入候选已确定性映射；不证明 Creator 已导入、预览、构建或平台可发布。

## 后续真实项目结构

当前 project candidate 已生成如下结构，但须由真实 Creator 导入后才能证明序列化兼容和运行：

```text
assets/game-factory/
  kernel/            # GameplayKernel 的 Cocos 实现；不含主题和平台 API
  content/           # ContentPack loader 与资源引用
  presentation/      # 场景、布局、动画、反馈、可访问性
  platform/
    port/             # PlatformPort 类型与 typed result
    douyin/           # tt.* 实现
    wechat/           # wx.* 实现
  telemetry/         # 无凭据、最小化事件
```

该结构已作为静态候选生成并通过 TypeScript compile；它不是 Creator 已验证的可玩工程。

## 负向边界

- Cocos profile 不能打开任何构建、DevTools、凭据、真机、送审、发布或支付权限。
- 未知 Creator CLI 和 target 保持 `null`/`pending`，不得凭经验硬编码。
- Project candidate 的 `serialization_creator_version=3.8.0` 只表示固定序列化参考；真实 editor 必须读回 exact `3.8.x` patch，二者不得混写。
- Preflight 必须记录 Creator executable 与 editor-exported config 的绝对路径和 SHA-256；handoff 必须将同一 editor patch 同时绑定到 build binding，并重新读回这些文件摘要。该 receipt 仍只是供应方声明完整性校验，不等于 verifier 独立观察了构建。
- PlatformAdapter 不拥有胜负、评分、随机种子或奖励事实；广告奖励只能由平台完成回调触发且幂等。
- 旧 `local_contract_verified` 证书不覆盖新增 Cocos 文件；新增切片必须独立测试和重新绑定精确 tree。
- `ready_to_build` 仅代表非执行 preflight 前提齐全；不代表 Creator 构建已运行。DevTools handoff verifier 只接受严格字段、产物摘要、平台/target/project 绑定、模拟器和真机人工 readback，且 upload/review/publish/rollback 必须仍为 `not_started`。
