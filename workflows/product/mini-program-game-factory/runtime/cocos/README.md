# Cocos 本地整合边界

本目录保存 Cocos Creator 3.8 系列的本地整合契约，不包含 Cocos Engine/Creator 二进制，也不是可玩的 Cocos 工程。

- `cocos-integration-profile.json`：固定源码身份、平台线索和默认关闭的 authority。
- `cocos-integration-packet.schema.json`：`WorkPackage → CocosIntegrationPacket` 的机器可读边界。
- `platform-port-contract.json`：微信/抖音共享接口与禁止所有权。

真实 Creator 版本、CLI、build target、开发者工具和真机能力必须由后续执行 receipt 更新，不能直接改写本 profile 为 PASS。
