# Shipping Packet

当前状态：`blocked_at_creator_devtools_device_and_external_authority`。

## 已验证的本地能力

- Cocos Creator 3.8 integration profile 与摘要绑定 candidate bundle；
- 纯 TypeScript GameplayKernel、ContentPack normalization、LocalPlatformStub 与 fake-SDK contract-tested 的 `wx`/`tt` adapter candidates（不等于官方 SDK E2E）；
- 固定 seed/input 的 Node runtime smoke：`evidence/cocos-node-runtime-smoke.json`；
- 19-file deterministic Creator import candidate（含 official adapter candidate source）：`evidence/cocos-creator-project-candidate/project-manifest.json`；
- 非执行 build preflight 与严格 handoff verifier；
- 当前 blocked receipt：`evidence/cocos-build-preflight-blocked.json`；
- 与 verifier 字段收敛、默认 blocked 的 `devtools-handoff-template.json`。

`ready_to_build` 只表示 preflight 的本地前提齐全，并不表示 Creator 已被调用。当前 receipt 为 `build_preflight_blocked`、`command=null`。

## 缺少且不得推定

- 可调用的 exact Cocos Creator 3.8.x CLI 与真实 patch-version readback（project candidate 的 `3.8.0` 只表示固定序列化参考版本，不等于本机 editor patch）；
- Creator 成功导入/反序列化当前 project candidate；
- 从 Creator Build 面板导出的平台 config；
- 真实微信/抖音 AppID；
- Creator build 官方 success exit code `36`、平台产物路径/大小/SHA-256；
- 当前官方平台 SDK adapter 的 runtime receipt；
- DevTools 导入、模拟器、真机和人工试玩 readback；
- upload、review、publish、rollback receipt。

## 当前精确阻塞

```text
creator_cli_unavailable
creator_editor_version_unverified
appid_required
creator_build_config_export_required
build_authority_closed
```

## Handoff verifier 边界

只有严格字段、project digest、`serialization_creator_version`、exact `creator_editor_version_readback`、同一 editor patch 的 Creator executable/config 绝对路径与 SHA-256 build binding、platform target、artifact digest、Creator build、DevTools import、simulator compile 和 real-device preview 的供应方 readback 全部匹配时，verifier 才返回 `devtools_handoff_receipt_integrity_verified`。该状态只证明 receipt 结构、绑定、当前文件摘要、产物完整性及供应方声明一致，不代表 verifier 独立观察过 Creator、DevTools、模拟器或真机执行。任何未知字段、版本绑定错配、相对路径、symlink、摘要篡改、平台错配、缺失/false readback、开放 authority 或已开始的 upload/review/publish/rollback 都 fail closed。

权限：`may_build_cocos=false`、`may_invoke_devtools=false`、`may_enter_credentials=false`、`may_preview_device=false`、`may_submit_platform=false`、`may_publish=false`、`may_pay=false`。
