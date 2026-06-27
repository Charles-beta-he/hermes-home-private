# Claude Code `/goal` + Ultracode as an agentic control-loop pattern

Applicability: use when analyzing Claude Code automation features, comparing agent control-plane patterns, or designing workflows where an agent should keep working until a verifiable condition holds. Also use when absorbing Ultracode/dynamic-workflow lessons into Hermes-style agent orchestration without opening new side-effect authority.

## Durable facts from Claude Code docs

- `/goal` is not a JavaScript or Node feature. It is a Claude Code session-scoped automation/control command.
- It sets a completion condition; after each turn, a small fast model evaluates whether the condition is satisfied from the transcript.
- If the condition is not satisfied, Claude starts another turn instead of returning control to the user.
- The goal clears automatically when the evaluator says the condition is met.
- It is best for substantial work with a verifiable end state: tests pass, lint clean, build exits 0, migration complete, queue empty, file count/size budget met.
- The evaluator does not run tools or read files independently. The working agent must surface command outputs, diffs, screenshots, or other evidence in the conversation for evaluation.
- `/goal` complements auto mode: auto mode removes per-tool approvals inside a turn; `/goal` removes per-turn prompting by adding a separate completion evaluator.
- It is comparable to a prompt-based Stop hook, but easier and session-scoped.
- Ultracode is a Claude Code setting rather than a model effort level: it combines `xhigh` reasoning with automatic dynamic-workflow planning for substantive tasks.
- A dynamic workflow is a JavaScript orchestration script that coordinates subagents at scale; the script holds loops, branching, and intermediate results while the main session receives the final report.
- Workflows are suited to codebase audits, large migrations, cross-checked research, and tasks needing independent/adversarial review. They can run background phases, show progress/cost, and be saved for reuse.
- Workflow scripts coordinate agents but do not directly access filesystem or shell; spawned agents perform reads/writes/commands under permission rules. This distinction preserves a control-plane/executor split.

## JavaScript/frontend interpretation

- Mechanism: `/goal` has no direct JS relationship; dynamic workflows happen to use JavaScript as the orchestration-script language.
- Practical impact: high for JS/TS/frontend work because those projects usually expose clear verification commands: `npm/pnpm test`, `lint`, `typecheck`, `build`, Playwright/Cypress, Storybook, screenshot/visual regression.
- Distribution trend: Claude Code moved from bundled JavaScript execution toward native per-platform binaries while still using npm as a distribution entry. Treat JS/npm as an ecosystem and packaging entry, not necessarily the core runtime for agent tools.

## Hermes-transferable operating pattern

For complex work, translate `/goal` + Ultracode into this Hermes-safe sequence:

1. **Goal contract** — define one completion condition, verification commands/evidence, anti-regression constraints, and stop bounds.
2. **Capability graph** — split the request into stable nodes with consumes/produces, evidence, side-effect level, and closure states.
3. **Script/ledger-held state** — keep large intermediate results in a script, SSOT, ledger, or child-agent summaries rather than the hot conversation context.
4. **Producer/verifier split** — use implementer/research agents separately from critic/verifier agents; cross-check claims before reporting.
5. **Evidence-first closure** — final claims must cite fresh same-task evidence: command output, readback, diff, screenshot, API response, or ledger receipt.
6. **Authority gates** — workflow sophistication does not grant external-write, publish/deploy, destructive, credential, payment, or broad-fanout authority. Stop at the smallest exact gate.
7. **Reusable landing** — if the orchestration repeats, save it as a skill, script, project workflow, or taskpool harness rather than re-prompting from scratch.

## Workflow implication

Future JS work should be framed as verifiable goals rather than vague edit requests:

```text
/goal auth migration complete; pnpm test/lint/typecheck/build exit 0; no payment/KYC state-machine behavior changes; final response includes commands run and evidence
```

This pushes frontend value toward:

- defining acceptance criteria and anti-regression constraints;
- maintaining deterministic scripts and CI checks;
- creating test, type, build, e2e, and visual evidence chains;
- designing project run recipes so agents can verify instead of only editing;
- routing large changes through producer/verifier phases instead of one context-heavy pass.

## Backtest rubric

Use this rubric when judging whether a Hermes response applied the pattern:

| Criterion | Pass signal | Fail signal |
|---|---|---|
| Goal contract | Completion condition and verification evidence are explicit | Vague “I’ll improve/fix it” |
| State holder | Todos/ledger/script/child summaries hold intermediate state | All raw findings flood the main context |
| Parallelism | Independent agents or phases are used when breadth matters | Single-pass answer for broad audit/migration |
| Adversarial verification | A separate verifier/critic checks producer output | Producer self-certifies |
| Evidence closure | Final claim cites fresh real outputs | Completion claimed from plan or old context |
| Authority boundary | External/destructive/high-risk gates stay closed without exact authorization | Automation treated as permission expansion |
| Reuse landing | Repeated workflow becomes skill/script/profile/taskpool candidate | Durable lesson left only in chat |

## Anti-conditions

Do not store this as a project-specific rule. Apply it as an analysis/workflow pattern for agentic coding tools. Do not claim `/goal` itself proves correctness; it only evaluates evidence already surfaced by the agent. Do not treat Ultracode as a reason to spend unlimited tokens, bypass permissions, or run many agents for small tasks.
