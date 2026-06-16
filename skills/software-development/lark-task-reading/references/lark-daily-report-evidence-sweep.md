# Lark daily report evidence sweep

Use when drafting a Lark/Feishu daily report from repository work, especially after a long session where only the most recent PRs are salient.

## Applicability

- The user asks to整理今日改动 / 提交日报 / 填 Lark 汇报.
- Work landed through GitHub PRs or commits during the day.
- The report should reflect the whole working day, not just the current chat context.

## Anti-conditions

- Do not include unrelated commits by other authors unless they are coordination context or explicitly requested.
- Do not treat a local WIP branch as shipped work unless it has been merged/pushed or the report explicitly says local-only.
- Do not click the final submit button if the user asked to review/click it themselves.

## Procedure

1. Identify the report date and timezone. Prefer the user's local project timezone when known.
2. Fetch the target repo/branch before counting work.
3. Collect all same-day merged PRs and commits for the user/author, not only the most recent session PRs. Useful shapes:
   - `git log origin/<branch> --since='<date> 00:00' --until='<next-date> 00:00' --date=iso --pretty=format:'%h | %ad | %an | %s' --reverse`
   - `gh pr list --state merged --base <branch> --limit 50 --json number,title,mergedAt,mergeCommit,url`
4. Group the results by workstream, not by raw commit order:
   - UI/PWA/device compatibility
   - transaction/data correctness
   - release/runtime/tooling
   - bug fixes/regressions
   - verification/build evidence
5. Draft fields from evidence:
   - 今日工作完成情况: user-facing and engineering outcomes
   - 开发任务完成进度: PR numbers / merge commits / verification commands
   - Bug修复: concise bug categories
6. Keep public report text safe: no local paths, tokens, raw logs, or private dashboard/session details.
7. If using browser/computer control, stop at the final submit button when the user requested manual submission.

## Pitfall from practice

A common miss is drafting the report from only the last two PRs in the active chat. Always do a same-day author/merged-PR sweep first; otherwise the daily report can omit earlier morning/afternoon fixes that already landed in the target branch.
