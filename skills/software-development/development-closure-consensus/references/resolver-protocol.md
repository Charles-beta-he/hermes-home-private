# Closure Resolver Protocol

This protocol defines how an agent should respond when a user asks for task closure checking, full-cycle delivery, or all-in closeout.

## Trigger detection

Enter closure resolver mode for prompts like:

- 检查 X 任务闭环情况
- 看这条链路是否闭环
- 全盘推进
- 收口
- 继续推进到完成
- 验证主链并提交/开 PR

Do not wait until PR time. The closure starts at the user's handoff.

## Resolver sequence

### 0. Classify the request

Identify:

- project name or inferable workspace
- task source: Lark, GitHub issue, PRD, user message, local branch, code diff
- closure scope: inspect-only, implement-and-verify, submit PR, merge support, learning writeback
- risk level: low, normal, high, production-affecting

### 1. Locate project profile first

Search order:

1. explicit project profile path from memory/config
2. `~/.hermes/project-profiles/<project>.json`
3. repo `AGENTS.md` / `CLAUDE.md` / `.cursorrules`
4. project docs/scripts/package/build files
5. live code evidence if no profile exists

If no profile exists, create a minimal working profile from live evidence before deep execution, or explicitly mark the profile gap.

### 2. Compile project closure consensus

Combine:

- public closure principles
- project facts
- task/domain-specific truth sources
- current repo/branch state

Produce a working execution consensus with:

- best-fix-point rules
- red lines
- validation gates
- delivery gates
- learning writeback rules

### 3. Diagnose before implementation

For task closure checking, first answer:

- What is the main chain?
- What evidence currently exists?
- Which part is unclosed: product, frontend, backend, contract, data, infrastructure, validation, delivery, or documentation?
- What is the smallest durable fix point that closes the main chain without regressing project red lines?

### 4. Execute stage-gated closure

Do not skip verification or delivery gates:

1. source/truth inspection
2. implementation or configuration changes
3. validation evidence
4. rebase/base alignment if committing/PRing
5. precise commit scope
6. PR metadata/dependency/merge-order closeout when applicable
7. learning writeback

### 5. Handle PR tail through github-pr-workflow

When the task reaches commit/PR stage, load/use `github-pr-workflow` and its `references/pr-closeout-consensus.md` tail rules:

- verify fresh branch against remote
- verify true remote base
- rebase and rerun validation
- precise `git add`
- explicit PR base/head
- distinguish no CI from failed CI
- state cross-repo dependency and merge order

### 6. Writeback classification

After a closure is proven:

| Finding type | Destination |
| --- | --- |
| Cross-project closure principle | A / this skill / shared reference |
| Project-specific durable fact | project profile / project AGENTS.md |
| Deterministic repeated command sequence | script/template/pipeline |
| Non-trivial technical decision | ADR / PR note |
| Temporary task progress | session/task notes only, not memory/profile |

## Minimal terminal report format

```text
Closure Resolver Report
Project profile: found | missing | synthesized
Compiled consensus: fresh | regenerated | stale-with-assumptions
Main chain: ...
Best fix point: ...
Evidence gates: ...
Delivery gates: ...
Writeback needed: public | project | script | ADR | none
Next action: ...
```

## Failure modes

1. **Profile skipped** — agent applies generic closure and misses project red lines.
2. **C treated as truth** — compiled project consensus drifts after public/project updates.
3. **Evidence borrowed from before rebase** — old validation no longer proves current branch.
4. **PR tail mistaken for whole closure** — implementation and main-chain verification are underdone.
5. **Learning not classified** — useful durable lessons become stale memory or are lost in chat.
