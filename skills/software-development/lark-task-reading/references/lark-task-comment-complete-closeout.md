# Lark Task Comment and Complete Closeout

Use this reference when a Lark/Feishu task is ready for delivery and the user asks to comment, close, complete, click complete, or follow the established Lark closeout flow.

This is a closeout reference under `lark-task-reading`, not a separate routing skill. Load it only after a concrete Lark/Feishu task or GUID/URL is in scope and closeout/writeback is intended.

## When to Use

Use for:
- A user says a Lark/Feishu task is fixed and asks to write back evidence.
- A user provides a Lark todo/task URL and asks to comment, complete, close, or submit the task.
- A task implementation is done and needs Lark evidence/comment/completion readback.
- The user says future Lark tasks should follow this closeout flow.

Do not use for:
- Merely listing or reading Lark tasks without writeback intent.
- Generic code fix or repository work with no Lark task boundary.
- Taskpool cleanup/quarantine work that does not mutate live Lark.
- Final Lark completion when required remote or online acceptance is still pending.

## Task Identification

1. If the user provides a Lark todo/task URL, use the `guid` query parameter as the live task identifier.
2. Do not use display IDs such as `t104312` as the API task GUID.
3. If no GUID/task can be identified, continue only the otherwise-scoped local work and report that Lark closeout is blocked by missing task identity.
4. Before writeback, read the live task when possible and confirm it is the intended target.

## Closeout Gates

Do not mark a Lark task complete merely because code was edited.

Minimum gates before final Lark completion:

1. Implementation is actually done for the task scope.
2. Relevant checks pass: focused tests, typecheck, lint, build, browser/Playwright, or fullstack checks according to project risk.
3. Required repository/release state is satisfied for the project flow.
4. If online/remote acceptance is required, it has completed or the user explicitly waived it for this task.
5. Evidence comment or attachment writeback succeeds.
6. A readback confirms the comment/attachment and final completion state.

If any gate is missing, report the exact blocker instead of completing the task. Use explicit closeout vocabulary such as `local_closed_remote_deferred_by_user`, `lark_writeback_blocked_token_expired`, or `remote_acceptance_pending` when applicable.

## Implementation and Verification Flow

When the request is about fixing and closing a Lark task:

1. Identify the Lark task GUID and title.
2. Read project instructions and relevant code before editing.
3. Implement the fix without violating project red lines.
4. Run self-checks appropriate to the change and project.
5. Prepare concise evidence: changed files, test commands/results, shareable repository or deployment handles if available, residual risk.
6. Write a Lark comment or update task evidence only after checks pass and the comment is safe for external reviewers.
7. Read back the written comment/evidence.
8. Complete the task only after the closeout gates are satisfied.
9. Read back completion status.
10. If the user also requested repository submission, follow the repository submit workflow with scoped staging, review, and project branch rules.

## Safe Lark Comment Format

Keep comments concise and reviewer-facing. Do not paste raw logs or local-only evidence.

Suggested structure:

```text
📱 类型：<frontend UI / backend / fullstack / docs / test / infra / other>

🔎 原因：<root cause or observed gap>

🛠️ 修复路径：
1. <main change>
2. <main change>

✅ 是否修复完成：已完成。 或 未完成，阻塞于 <reason>。

🧪 自检结果：
- <command/check>: PASS
- <command/check>: PASS

📎 关键文件/证据：<repo-relative files, shareable review/deploy/evidence handles>
```

Type icon guidance:
- `📱` frontend UI / mobile app
- `🧩` fullstack / integration
- `🛠️` backend / service
- `🧪` tests / verification
- `📄` docs / copy / requirements
- `⚙️` tooling / infra / CI
- `🚧` blocker / not completed

## Evidence Hygiene

External Lark comments must not include:
- local addresses: `localhost`, `127.0.0.1`, file URLs;
- local-only paths: `/Users/...`, `/tmp/...`, local screenshot/report paths;
- tokens, cookies, OTPs, passwords, raw terminal logs, private dashboard URLs;
- unsupported claims such as “线上已验证” without actual remote/readback evidence.

Prefer externally meaningful evidence:
- repo-relative file paths;
- shareable repository, review, release, deployment, Drive, Doc, or Lark attachment handles;
- concise command names and PASS/FAIL status.

If screenshots are required, upload only task-relevant screenshots as Lark attachments or provide a shared evidence link. Do not dump an entire local regression directory into every task.

## API / CLI Writeback Requirements

Before relying on a CLI command, confirm it is available and that it uses the correct Larksuite endpoint shape. Do not silently skip writeback because a CLI binary is missing; search known local locations or fall back to the verified API/helper path.

For Larksuite international task comments, prefer the flat comments endpoint documented in `references/lark-task-api-v2-update-and-closeout.md`:

```text
POST /task/v2/comments
body: {"resource_id": "<guid>", "resource_type": "task", "content": "<evidence>"}
readback: GET /task/v2/comments?resource_id=<guid>&resource_type=task&page_size=50
```

Task description update uses `PATCH /task/v2/tasks/{guid}` with wrapped body:

```json
{
  "task": {"description": "evidence text"},
  "update_fields": ["description"]
}
```

If a local `lark-cli task +comment` or `+complete` path is used, treat it as a convenience wrapper, not proof by itself. Always perform readback from the live API/UI/helper after comment and completion.

## Completion Readback

After marking complete, verify one of:
- task status is `done`;
- `completed_at` is non-zero;
- task UI/helper readback shows completed state.

If completion requires an additional OAuth scope, request only the minimal required scope, complete the auth flow, then retry and read back. If auth cannot be completed in-session, provide the prepared comment text and exact blocker.

## Repository Submit Interaction

If the user also says “提交代码” or asks for repository submission:

1. Finish Lark evidence/comment gates in the order required by the project. Some project flows require repository and release evidence before final Lark completion.
2. Pull/fetch the target branch according to project rules.
3. Stage only task-scoped files; avoid broad staging in dirty worktrees.
4. Run `git diff --cached --check` and any targeted checks needed after final edits.
5. Submit repository changes only when authorized/requested.
6. Include the shareable repository/release handle in Lark evidence when applicable.

For UVISA flows, respect the project profile and closeout references: local implementation proof is often only a sendback gate; final Lark completion waits for online UI acceptance evidence unless explicitly waived.

## Common Pitfalls

1. Completing a Lark task after local tests but before required online acceptance.
2. Using display ID (`t123456`) instead of GUID for API writeback.
3. Writing a long dense comment that Lark renders as one unreadable paragraph.
4. Pasting local paths or localhost evidence into external-facing comments.
5. Treating CLI command success as enough without API/UI readback.
6. Losing closeout budget to optional documentation before repository, comment, and completion gates.
7. Failing to distinguish “implementation sendback” from “final task closeout”.

## Verification Checklist

- [ ] Concrete Lark task GUID/URL/title is identified and matches the intended target.
- [ ] Relevant project checks passed or blocker is explicitly recorded.
- [ ] Comment/evidence contains no secrets, local-only paths, raw logs, or unsupported remote claims.
- [ ] Comment/attachment/description writeback succeeded and was read back.
- [ ] Completion happened only after required acceptance gates were satisfied.
- [ ] Completion status was read back from live Lark/API/UI/helper.
- [ ] Repository submission, if requested, followed scoped project branch rules and produced verifiable handles.
