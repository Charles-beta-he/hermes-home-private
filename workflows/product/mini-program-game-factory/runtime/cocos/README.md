# Cocos 本地整合边界

本目录保存 Cocos Creator 3.8 系列的本地整合契约，不包含 Cocos Engine/Creator 二进制，也不是可玩的 Cocos 工程。

- `cocos-integration-profile.json`：固定源码身份、平台线索和默认关闭的 authority。
- `cocos-integration-packet.schema.json`：`WorkPackage → CocosIntegrationPacket` 的机器可读边界。
- `platform-port-contract.json`：微信/抖音共享接口、禁止所有权与当前关闭的执行 authority。
- `runtime-core/src/official-platform-adapters.ts`：分别绑定 `wx`/`tt` 的本地 contract-tested adapter candidates；严格校验 SDK 形状，只返回一次性 login code，不把它冒充身份，且仅在广告关闭回执 `isEnded=true` 时授予奖励。

这些 adapter 仅由 fake SDK 单元测试验证；未执行官方 SDK、Creator、开发者工具或真机 E2E。

真实 Creator 版本、CLI、build target、开发者工具和真机能力必须由后续执行 receipt 更新，不能直接改写本 profile 为 PASS。
