# Agent Eval + Dynamic Workflow long-term stable plan — 2026-06-09

schema: hermes_self_optimization_plan_v1
id: agent-eval-dynamic-workflow-longterm-20260609
status: multimodel_advisory_synthesized_and_landed
created_at: 2026-06-09 20:23:28 CST
source_request: 用户认可抖音图文分析后要求“多模型思考长期稳定最终方案”。

## Objective & cost

Objective:
- Turn the observed Agent Eval / Dynamic Workflow / Harness insight into a long-term stable Hermes architecture plan.
- Prefer a production-grade control-plane design over ad-hoc prompt additions.
- Preserve current working runtime while defining a staged path toward measurable agent reliability.

Cost function:
- Maximize reliability, repeatability, evidence grounding, and regression detection.
- Minimize blast radius, hidden state mutation, prompt bloat, workflow over-triggering, and taskpool noise.
- Keep user-visible execution fast for simple tasks while adding stronger gates for high-risk work.

Hard constraints:
- Do not directly mutate live taskpool/config/cron/gateway in this planning pass.
- Do not claim Anthropic/Claude official support unless verified from official docs/source.
- Treat the Douyin item as a trend signal, not source-of-truth technical evidence.
- Any future code landing must use scoped SSOT, focused tests, and scoped commit.

## Evidence from reviewed Douyin note

Canonical page observed: `https://www.douyin.com/note/7647228348100809819`.
Author: 斯塔克建造日记.
Caption: `Vibecoding+AgentEval.#真实生活分享计划 #vibecoding Harness还没玩转，又要研究新词汇。据说很多人vibecoding不行就是少了agent eval #harness #agent框架 #一人公司 #vibecoding大赏`.
Publish time observed: `2026-06-04 01:51:40`.
Page note: `作者声明：内容由 AI 生成`.
Visible engagement: likes 2323, comments 51, favorites 1558, shares 367.

Extracted concepts from the three images:
- Agent Eval evaluates the whole agent system, not only a model: `Model + Agent Framework + Tool + Workflow`.
- Eval loop: define task → run experiment → collect trajectory → inspect result → grader score → quantified feedback → continuous improvement.
- Grader tiers: Code Grader, LLM Grader, Human Grader.
- Dynamic Workflow / Harness claim: choose Direct / Plan / Research workflow by task complexity.
- Key thesis: vibecoding is not enough; reliability comes from harness + dynamic routing + eval.

## Current Hermes baseline already landed

- `objective-model-path-verification` skill exists.
- Runtime prompt gate commit in `/Users/charles/.hermes/hermes-agent`: `3b7fbae3a Add objective model path prompt gate`.
- Parent SSOT commit: `9a21da8 Land objective model path runtime gate`.
- The current gate is prompt-level and config-gated; it does not yet provide a full eval harness or dynamic workflow router.

## Candidate architecture directions

### A. Prompt-only incrementalism

Keep adding prompt guidance / skills.

Pros:
- Low risk and cheap.
- Easy to patch and roll back.

Cons:
- Not measurable.
- Cannot detect regressions reliably.
- Over time prompt bloat becomes a hidden tax.

Preliminary verdict: useful as a bootstrap, insufficient as the long-term stable solution.

### B. Agent Eval Harness as canonical reliability layer

Build a durable eval harness with case specs, trace capture, graders, run records, and regression reports.

Pros:
- Converts agent quality from subjective impressions into repeatable evidence.
- Lets Hermes test prompt/skill/runtime changes before and after updates.
- Supports Code/LLM/Human graders without making LLM judgment the only truth.

Cons:
- Requires schema discipline and case maintenance.
- Initial harness adds overhead and must start small.

Preliminary verdict: likely long-term foundation.

### C. Dynamic Workflow Router as execution control-plane

Route each task into Direct / Plan / Research / Implement / Incident / Review / Eval modes by objective, risk, uncertainty, and side effects.

Pros:
- Fast path stays fast; high-risk path gets gates.
- Matches Hermes user preference: default推进 but stop at real boundaries.
- Can integrate with objective-model-path gate.

Cons:
- Router mistakes are dangerous.
- Needs explicit observable decision records and override escapes.

Preliminary verdict: necessary, but should be layered after/with eval harness so routing quality is measurable.

### D. Taskpool-first governance

Every nontrivial workflow becomes taskpool tasks with lifecycle/evidence.

Pros:
- Durable ledger, dependencies, worker handoff.

Cons:
- Too heavy for live conversation.
- Risk of queue noise and hook side effects.

Preliminary verdict: use only for durable multi-session work; do not make it the default live-chat path.

## Multimodel review question

Please evaluate the long-term stable architecture for Hermes to absorb Agent Eval + Dynamic Workflow + Harness ideas.

Required output from each model:
1. Proposed final architecture in 5-8 components.
2. Recommended staged rollout: 0-2 weeks, 1-2 months, 3-6 months.
3. Main risks and failure modes.
4. Verification/eval strategy.
5. What NOT to do.
6. Any disagreement with the preliminary verdicts above.

Scoring lens:
- Long-term stability.
- Low blast radius.
- Measurable reliability improvement.
- Compatibility with Hermes existing skills/taskpool/gateway/runtime.
- Resistance to prompt bloat, eval theater, and taskpool noise.

## Multimodel review execution

Primary `consult_models.py run` attempts:
- T2 discussion with 5 planners (`claude-opus-4-7`, `gpt-5.5`, `mimo-v2.5-pro`, `deepseek-v4-pro`, `gemini-3.1-pro-preview`) was attempted but terminated with exit `-15` during consensus and left no tick artifact under `~/.hermes/tick-*`.
- T1 discussion with 4 planners was attempted but also terminated with exit `-15` before durable discussion artifacts were written.

Fallback execution used direct provider calls through `hermes chat --source tool --ignore-rules` with a shared reviewer prompt:
- Claude route attempted via `claude-code / claude-opus-4-7`, but the CLI reported primary auth fallback and answered via `google-gemini-cli / gemini-3.1-pro-preview`. Treat as Gemini-family perspective, not Claude certification.
- GPT route: `openai-codex / gpt-5.5`, output saved to `/Users/charles/.hermes/runs/agent-eval-dynamic-workflow-20260609/model_outputs/gpt.txt`.
- DeepSeek route: `deepseek / deepseek-v4-pro`, retried with `--max-turns 3`, output saved to `deepseek_retry.txt`.
- MiMo route: `xiaomi / mimo-v2.5-pro`, output was summary-like and included implementation-path claims; only claims later verified by filesystem search are used.
- Gemini route: `google-gemini-cli / gemini-3.1-pro-preview`, output saved to `gemini.txt`.

Grounding caveat:
- This is a multi-view advisory, not full `consult_models.py` ratification certification, because the formal discussion artifact failed to materialize.
- However, GPT, Gemini, DeepSeek, and the Claude-fallback/Gemini response converged strongly on the same architecture: off-hot-path trajectory capture, isolated eval harness, hybrid graders, shadow router, feedback/skill ratchet, sandboxing, and regression database.

Additional filesystem verification:
- `/Users/charles/.hermes/hermes-agent/agent/trajectory.py` exists.
- `/Users/charles/.hermes/hermes-agent/agent/task_router.py` exists.
- No `/Users/charles/.hermes/**/eval_harness.py` was found.
- No existing `/Users/charles/.hermes/evals` entry was found by `search_files`; therefore any claim that eval seed files already exist is not accepted as evidence.

## Final synthesis — stable long-term architecture

Name: **Hermes Agent Reliability Harness**.

Principle: **hot path minimal, reliability logic off-path first, then shadow, then gated enforcement**.

Final components:

1. **Eval Case Registry**
   - Versioned cases under a future `~/.hermes/evals/cases/` or repo-owned test fixture path.
   - Each case declares task input, context, allowed tools, forbidden side effects, expected artifacts, workflow label, risk level, grader set, and acceptance criteria.

2. **Trajectory / Evidence Recorder**
   - Non-blocking structured capture of router decision, loaded skills, tool calls, tool summaries, objective gate trigger, diffs/tests/logs, final response, side effects, and boundary stops.
   - Must be redacted, compact, hashable, and replay-oriented.
   - Start with offline/session-log extraction before adding live hooks.

3. **Isolated Eval Harness Core**
   - Independent CLI/script, not gateway hot path.
   - Runs cases in sandbox/worktree/virtualized state where file writes, terminal calls, memory writes, send_message, taskpool mutations, and cron creation are blocked or redirected unless explicitly allowed.

4. **Hybrid Grader Suite**
   - Code/Tool Grader first for deterministic facts: exit code, schema, file existence, tests, diff shape, HTTP status, tool-call contract.
   - LLM Grader only for semantic quality, evidence sufficiency, hallucination, workflow fit, and user-communication quality; must use rubrics.
   - Human Grader / spot-check for high-risk, product/UX, memory/skill/runtime changes, and LLM disagreement.

5. **Shadow Workflow Router**
   - Classifies Direct / Plan / Research / Objective-gated / Incident / Review / Eval.
   - Starts as shadow-only: logs predicted route and confidence but does not affect execution.
   - Later suggest-mode: exposes route recommendation and expected verification burden.
   - Only after regression evidence, limited enforce for low-risk paths.

6. **Feedback & Improvement Ledger**
   - Eval failures become structured records: failure type, evidence, root cause, suggested fix layer, before/after score, and whether a regression case should be added.
   - Does not directly mutate memory, skills, config, or taskpool.
   - Routes candidates to skill patch, runtime issue capture, docs/ADR, taskpool candidate, or discard.

7. **Regression Database / Dashboard**
   - Stores eval runs, case hashes, trajectory hashes, grader scores, routing decisions, baseline diffs, and drift alerts.
   - Enables post-update regression: prompt/skill/runtime changes must show no degradation on sacred core cases.

8. **Governed Experience Ratchet**
   - High-confidence repeated lessons can propose skill patches or runtime changes.
   - Human/scoped review remains required for durable behavior changes.
   - Never auto-writes global memory for task-local outcomes.

## Rollout plan

### 0–2 weeks — Foundation, no live behavior change

Deliverables:
- Create eval case schema and 10–20 seed cases from real Hermes task classes: media analysis, small code patch, Hermes self-update, research summary, skill patch, tool failure recovery.
- Implement/read-only extract of trajectory/evidence records from existing session/tool logs where available.
- Build deterministic Code/Tool Grader prototypes for 3–5 cases.
- Define sandbox policy and prohibited side effects.
- Add one local CLI smoke command such as `hermes-eval run --case <id> --dry-run` or a script prototype.

Gate to next phase:
- Harness can distinguish at least 3 intentionally broken cases from passing cases.
- No writes to real memory/taskpool/cron/send_message during eval.

### 1–2 months — Shadow routing and hybrid grading

Deliverables:
- Eval Harness can run 30–50 cases with run artifacts.
- Shadow Workflow Router records route/confidence for live or replayed tasks without affecting execution.
- LLM Grader with rubrics added for semantic cases; calibrated against human spot checks.
- Regression DB stores baseline and trend.
- Feedback ledger dedupes failures and proposes fix layer.

Gate to next phase:
- Router prediction accuracy and false-direct rate are known.
- LLM grader/human agreement is acceptable for non-deterministic tasks, or the rubric is revised.
- Core sacred case pass rate is stable.

### 3–6 months — Limited enforcement and self-improvement loop

Deliverables:
- Low-risk route enforcement for obvious Direct/Research cases, with escape hatch.
- Objective-gated tasks automatically require evidence spine before completion.
- Eval Harness becomes part of `post-update-check` / Hermes self-update regression gates.
- Experience Ratchet proposes skill patches from repeated eval findings.
- Dashboard/report summarizes regressions, drift, and improvement ROI.

Gate for runtime enforcement:
- Rollback switch exists.
- Case regressions are monitored.
- No high-severity taskpool/gateway/memory side effects in eval runs.

## Non-goals / what not to do

- Do not put eval/grader work in the synchronous Telegram/gateway hot path.
- Do not make LLM-as-judge the primary truth source.
- Do not auto-create taskpool tasks from every eval failure.
- Do not auto-patch skills/memory/config from grader output.
- Do not build a heavy router that consumes more effort than the task.
- Do not call social-media trend diagrams official technical evidence.
- Do not optimize for eval score without measuring real user/task outcomes.
- Do not route every simple task through Plan/Research.

## Key risks and mitigations

- **Eval theater**: require each score to link to evidence and an actionable fix layer; track whether fixes improve regression cases.
- **Prompt bloat**: keep router/eval off-path; runtime prompt gate stays compact.
- **State pollution**: sandbox all eval runs; default deny memory/taskpool/cron/send_message writes.
- **Router mistakes**: shadow first; false-direct is the critical metric; low confidence falls back to Plan/objective gate.
- **Taskpool noise**: ledger accumulates signals before taskpool candidate creation; dedupe before enqueue.
- **Grader drift**: human sampling and intentionally broken cases calibrate rubrics.
- **Provider/runtime fragility**: eval must degrade to advisory when multi-model quorum artifacts are missing.

## Final decision

Adopt **B + C in sequence**:

1. Build **Agent Eval Harness** first as the reliability foundation.
2. Run **Workflow Router** in shadow mode while harness gathers route-quality evidence.
3. Add **Feedback/Experience Ratchet** after graders and regression DB exist.
4. Only then allow narrow runtime enforcement.

This is the long-term stable path because it turns “vibecoding feels better/worse” into evidence-backed regression control without overloading the live conversation path or polluting taskpool.
