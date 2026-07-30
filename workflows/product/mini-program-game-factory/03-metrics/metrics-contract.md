# 指标契约

## 本地研发指标（当前可读）

- `batch_accept_rate`：通过静态门禁的候选数 / 总候选数。
- `escalation_rate`：升级到 standard/high_reasoning/blocked 的任务比例。
- `protected_surface_violation_count`：内容尝试覆盖玩法/商业化/平台字段次数，目标为 0 个进入 accepted。
- `deterministic_replay_pass_rate`：相同输入编译摘要一致的比例，目标 100%。
- `gate_escape_count`：门禁失败却进入可构建状态的次数，目标 0。
- `high_cost_call_share`：高成本模型调用占比；只能在质量门禁稳定后优化，不能作为正确性前置目标。

## 未来真实产品指标

- 新手关完成率、首局时长、关卡失败原因；
- D1/D7 留存；
- 主动辅助请求率；
- 广告请求→完成→奖励幂等闭环；
- 崩溃、卡顿、启动时间与包体。

## 边界

当前没有真实玩家、平台或广告数据。任何留存、收入或审核通过率均为 `missing_instrumentation`，不得填充模拟值冒充事实。
