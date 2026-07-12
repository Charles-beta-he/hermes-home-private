**Hermes Portfolio P0 复审(仅基于所列证据,未执行工具)**

**1. 系统审核**
四项验证链一致:P0_STATIC_PASS(语法+registry JSON 合法)→ doctor ok/0 错 0 警 → strict_verify ok 且 doctor_ok=True → semantic_audit ok、16 维度 100% 覆盖、0 findings。修复范围守住:只动 metadata/profile/registry/audit 脚本,不碰项目代码、不外发、不 push。结论:声明层自洽,无内部矛盾。

**2. 架构审核**
关键改进是把"验证状态"从二值改为诚实分级:无证据 validated 降级为 ledgered-needs-evidence / needs-current-mission-readback,且保留 previous_status,可追溯、可回升,不销毁历史。persona-wake-stage 保持 claim-unverified 并加 known_gap_not_validated,把已知缺口显式建模而非静默 PASS——这是正确的语义:审计器报告缺口,不掩盖缺口。semantic_audit 强制每维度有 readback/verdict/gaps/next action,补上了"覆盖率≠健康"这一结构性漏洞。空 current_components 用组件补齐或 exemption 二选一处理,合理。

**3. 多角度审核**
- 诚实性:降级而非补造证据,方向对。
- 循环风险:audit 脚本与 metadata 同批人改,存在"审计器为过审而写"的自证嫌疑;但 findings=[] 配合显式降级(降级本身就是承认问题),证据倾向诚实而非粉饰。
- 弱点:semantic_audit 校验的是"字段存在且填写",不能验证 readback 内容真实新鲜;exemption 若滥用会变成新的静默通道,需留痕审批。
- 证据边界:我只见汇总数字,未见 16 维度原始输出。

**4. WARN → PASS 判定**
**PASS(限定域)**:declared coverage 与 metadata truthfulness 两项达标——覆盖 100%、无假 validated claim、缺口显式化。明确不代表:生产健康、降级项功能可用、readback 内容真实性。三个 ledgered-* 项目本质是"诚实的未验证",PASS 的是账本,不是系统。

**5. 剩余边界 / 下一步**
- P1:为三个降级项目补真实证据(local slice 复验、current mission readback),回升状态。
- persona-wake-stage:找回或重建缺失文件,消掉 known_gap。
- 给 exemption 加审批/过期机制,防语义漂移。
- semantic_audit 加 readback 时效戳校验(过期即 WARN)。
- 后续由独立审阅方跑一次 audit,消解自证嫌疑。
