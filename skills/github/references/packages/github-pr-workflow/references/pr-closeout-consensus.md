# PR 前闭环共识（开发闭环后段）

适用场景：任何需要“提交 + push + PR + 合并前说明”的开发任务，尤其是双仓/前后端联动交付。

定位：这是 `development-closure-consensus` 的交付后段，不是闭环起点。若用户交付的是“检查任务闭环情况/全盘推进/收口”，应先解析项目画像并完成主链诊断、实现补齐与项目化验证，再进入本清单。

## 核心共识

1. 分支状态以远端事实为准，不以本地命名感觉为准。
   - 检查当前分支
   - 检查远端是否已有同名 head
   - 检查是否已有 open PR

2. rebase 基线以远端当前目标分支为准。
   - 先看现有 PR 的 base
   - 没有 PR 时再用明确的默认 base（如 origin/main）
   - 不要默认本地 main 就是真相

3. 任何基线变更都会使旧验证失效。
   - 只要 rebase/pull 过上游，就必须重跑 build/test/browser 验收

4. 上游暴露的断点若阻塞交付闭环，应做最小修复并恢复可交付性。
   - 不要用“这不是我这次改的”跳过真正阻塞 PR 的问题

5. 提交范围必须精确。
   - 优先 `git add <exact files>`
   - 避免在长生命周期脏工作区里 `git add -A`

6. 临时验证资产必须有归宿。
   - 要么纳入正式资产（可复用脚本/模板）
   - 要么 `.gitignore` / 不纳入提交

7. PR 是交付对象的一部分，不是 push 的附属物。
   - 创建 PR 时显式指定 `--base` / `--head`
   - 创建后反查方向
   - 补 body / labels / 联动说明

8. 先区分“没有 checks”还是“checks 失败”。
   - `no checks reported` 可能只是仓库没配 workflows
   - 不要误入“修 CI”循环

9. 多仓联动要显式写出依赖关系和建议合并顺序。
   - 谁依赖谁
   - 先合哪个
   - 后合的一边是否需要再 rebase / smoke

10. 已人工跑通的可重复闭环，应优先沉淀为复用资产。
   - 先更新现有 umbrella skill
   - 再考虑 references/scripts/templates
   - 高频后再升级为 pipeline

## 最小执行清单

- 确认是否新分支；如果当前 tracking branch 已被远端删除（`[gone]`），不要继续沿旧分支 push/开 PR：先 stash 精确改动，从 `origin/<base>` 新建语义化分支，再 pop、验证、提交
- 确认真实 remote base
- 对齐基线并处理 rebase 冲突/断点
- 重跑验证
- 精确提交
- push 并创建 PR
- 反查 PR base/head
- 检查 checks 是否存在
- 补 label/body/联动评论
- 给出 merge 顺序建议
