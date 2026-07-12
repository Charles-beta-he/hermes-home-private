你是 Claude Fable 5。请对 Hermes Project Portfolio P0 修复后的结果做最终复审。只基于下列证据，不声称执行工具。

P0 修复范围：metadata/profile/registry/semantic-audit 脚本；不改项目代码；不外发；不 push/deploy；不改 work 项目代码。

修复动作摘要：
- 给空 current_components 的项目补 portfolio metadata 组件或 work-project exemption。
- 将 hermes-control-console、hermes-capability-model-router 的无证据 validated-local-slice 降为 ledgered-needs-evidence，并保留 previous_status。
- hermes-self-extension-os 降为 ledgered-needs-current-mission-readback，避免无当前 mission readback 的 validated claim。
- hermes-persona-wake-stage 保持 claim-unverified-files-missing，并加 audit_semantics known_gap_not_validated，避免假 PASS。
- 新增 portfolio_semantic_audit.py：每个维度必须有 current readback、verdict、known gaps、next action；100% coverage 不等于系统全健康。

验证：
- py_compile + registry JSON: P0_STATIC_PASS
- portfolio_doctor: ok=True, errors=0, warnings=0
- portfolio_strict_verify: ok=True, doctor_ok=True
- semantic_audit: ok=True, coverage_percent=100.0, dimensions=16, errors=0, warnings=0, findings=[]

请输出中文，800字以内：
1. 系统审核
2. 架构审核
3. 多角度审核
4. 是否从 WARN 转 PASS（仅限 declared coverage + metadata truthfulness，不代表生产健康）
5. 剩余边界/下一步。