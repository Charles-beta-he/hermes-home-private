# Routing Evals v1.0.0

Use these prompts to check whether `root-cause-ownership-council` should load.

## Positive prompts

1. "同一个软键盘问题已经修了几次又引入新问题，先别改，找根因和最终方案。"
2. "这个 PR 同时改了 service worker、release manifest、update banner，帮我做多 agent 会审。"
3. "notification/SSE/WebPush 开关反复修，帮我拆 owner contract 和回归矩阵。"
4. "api interceptor、auth store、页面 toast 都在处理错误，现在有失败测试，先分析控制权。"
5. "用多模型角色化审查这个高风险 diff，不要投票，要证据和反证。"

## Neighbor prompts

These should load a neighboring skill instead or only use this skill if repeated/high-risk signals appear.

1. "帮我 review 这个 20 行 PR 有没有安全和性能问题。" -> `multi-agent-code-review` or normal review.
2. "按这个已批准方案实现三个独立小任务。" -> `subagent-driven-development` / `test-driven-development`.
3. "这个按钮颜色和设计稿不一致，直接修样式。" -> UI/design skills, not council unless repeated layout ownership exists.
4. "帮我写一个普通功能实现计划。" -> `writing-plans` or `spec-stateful-sdd-workflow`.

## Forbidden / no-load prompts

1. "解释一下什么是 service worker。" -> general answer.
2. "把 README 里的错别字改掉。" -> no council.
3. "生成一个一次性 demo 页面，不需要测试。" -> no council unless user asks for high-risk/product verification.
4. "今天几点？" -> time tool, no council.

## Expected behavior

When the skill loads, the first output should not be a code patch. It should establish:

- stop triggers;
- state variables;
- owner table skeleton;
- evidence/falsifier needs;
- minimal implementation boundary only after gates pass.
