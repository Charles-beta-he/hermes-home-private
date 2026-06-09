# Claude Code Dynamic Workflows — Hermes Taskpool Migration Review

**Date:** 2026-05-29
**Source:** https://claude.com/blog/introducing-dynamic-workflows-in-claude-code (published May 28, 2026)
**Task:** 2026-05-29-review-claude-code-动态工作流模式并评估-hermes-taskpool-可迁移性

## Executive Summary

Claude Code's dynamic workflows introduce a runtime-planned, parallel-subagent execution model with adversarial verification and iterative convergence. Hermes already has several overlapping primitives (taskpool dispatch, multimodel intervention, agent-team parallel, autorun), but lacks the **runtime-planned decomposition** and **adversarial refutation** layers. This review maps 5 concrete patterns to Hermes with feasibility scores.

## Pattern Mapping Table

### Pattern 1: Dynamic Runtime Decomposition (Plan → Subtask Fan-Out)

**Claude Code behavior:** When a workflow kicks off, Claude plans dynamically based on the prompt, breaks it into subtasks, and fans the work out across subagents running in parallel. The plan is generated at runtime, not pre-defined.

**Hermes equivalent:** `brain_task_dispatch_tick.py --parallel-autorun` + `auto-split-non-convergence` for evolution tasks. Hermes decomposes tasks into convergence axes at claim time, but the decomposition is **static** (frontmatter `auto_subtask_axis`) rather than runtime-planned from the task objective.

**Gap:** Hermes has no runtime planner that inspects a P1 task and generates subtask decomposition on the fly. Current decomposition is either manual (user adds subtasks) or triggered by multimodel FAIL taxonomy (`auto-split-non-convergence`), which is reactive rather than proactive.

**Impact class:** taskpool/brain/control-plane
**Feasibility score:** 4/10 — Requires a new "planner" step in the dispatch tick that can call an LLM to decompose a complex task into bounded subtasks before claiming. Significant architecture change; would need fail-closed guardrails to prevent runaway decomposition.

**Recommendation:** Do NOT adopt wholesale. Hermes's manual/semi-auto decomposition is safer for governance. Consider a bounded "decomposition assist" advisory step that suggests axes for human review, not auto-creation.

---

### Pattern 2: Adversarial Verification Agents

**Claude Code behavior:** Agents address the problem from independent angles, other agents try to refute what they found, and the run keeps iterating until the answers converge. This is how workflows reach results a single pass can't.

**Hermes equivalent:** `multimodel-intervention-step` with multiple models (Claude, GPT-5.5, Gemini, DeepSeek, MiMo) voting on task completion. The `truth_gate` and `agreement_above_threshold` logic serve a similar convergence function. However, Hermes's multimodel is **certification-focused** (PASS/FAIL/CONTINUE_LOOP) rather than **adversarial-refutation-focused**.

**Gap:** Hermes multimodel panel evaluates evidence and votes, but does not actively try to **break** or **refute** the implementation. The closest is `amend` votes (0.7 weight), but these are advisory rather than adversarial.

**Impact class:** taskpool/brain/control-plane, core agent loop
**Feasibility score:** 6/10 — The multimodel infrastructure already exists. Adding a "refutation" mode to the discussion protocol (one model tries to find bugs/counterexamples in another's output) is a bounded extension of the existing `consult_models.py` framework.

**Recommendation:** Consider adding an optional `adversarial_round` to multimodel intervention where one designated model attempts to refute the implementation evidence. Low blast radius if made opt-in per task.

---

### Pattern 3: Independent Result Verification Before Merge

**Claude Code behavior:** Results are checked before they're folded in. Independent verification on every finding so the report surfaces real issues. Two reviewers on each file.

**Hermes equivalent:** `proof-check`, `selfcheck`, `evidence-spine`, and the `completion_gate: project-evidence-review-done` pattern. The task closeout chain requires structured evidence (test/build/browser/curl/commit) before `done`.

**Gap:** Hermes verification is **post-hoc** (proof-check after close) rather than **in-flight** (verify each subtask result before merging into the parent). The `review` status acts as a gate, but subtask results are not independently verified before being backfilled into the parent.

**Impact class:** taskpool/brain/control-plane
**Feasibility score:** 7/10 — The `auto-subtask-sync` and `blocked-resolve-step` infrastructure already exists. Adding a verification step where each child's evidence is independently checked before parent backfill is a natural extension.

**Recommendation:** Adopt incrementally. Add a `child-evidence-verify` step in `auto-subtask-sync` that runs `proof-check` on each child before allowing parent backfill. This prevents unverified child evidence from contaminating the parent.

---

### Pattern 4: Checkpoint/Resume for Long-Running Work

**Claude Code behavior:** Progress is saved as the run goes, so a job that's interrupted picks up where it left off instead of starting over. Coordination happens outside the conversation.

**Hermes equivalent:** `checkpoint_states` in task frontmatter, `run_envelope_ref` for durable state, and the `continuation` / `auto-relay` system for budget exhaustion. The task note itself serves as a durable checkpoint.

**Gap:** Hermes checkpoints are **task-level** (status transitions), not **subtask-level** (individual subagent progress). If a parallel worker crashes mid-execution, the claimed task must be manually recovered. Claude Code's checkpoint is more granular — individual subagent progress persists independently.

**Impact class:** taskpool/brain/control-plane, agent-team-parallel
**Feasibility score:** 5/10 — The `agent_team_controller.py` worker job tracking already records per-worker state. Adding subtask-level checkpoint persistence would require changes to the worker execution model and durable state storage.

**Recommendation:** Incremental adoption. The existing worker job tracking (`~/.hermes/state/taskpool-workers/jobs/`) can be extended with per-subtask progress markers. Low priority compared to patterns 2 and 3.

---

### Pattern 5: Effort Level / Ultracode Mode

**Claude Code behavior:** A new setting called "ultracode" sets effort to xhigh, letting Claude decide automatically when to use a workflow. The effort menu controls whether dynamic workflows trigger.

**Hermes equivalent:** `priority_mode` (work-first, evolution-first), `permission_tier` (autonomous-execution, yolo-execution), and `max_authority` in task frontmatter. The `HERMES_LOCAL_BRAIN_AUTORUN` env vars control dispatch automation.

**Gap:** Hermes has no **dynamic effort escalation** — a task is either dispatched normally or requires explicit multimodel intervention. There's no "let the agent decide if this task needs parallel workflow" heuristic.

**Impact class:** taskpool/brain/control-plane
**Feasibility score:** 3/10 — Requires a task complexity classifier that decides at claim time whether to invoke parallel workflow. Risk of over-escalation (token waste) or under-escalation (missed parallelism).

**Recommendation:** Do NOT adopt. Hermes's explicit governance (frontmatter `requires_multimodel`, `permission_tier`) is safer than implicit effort escalation. The existing multimodel advisory system already provides a graduated path.

## Summary: What Hermes Should Actually Adopt

| Priority | Pattern | Action | Blast Radius |
|----------|---------|--------|--------------|
| HIGH | Adversarial Verification (P2) | Add optional `adversarial_round` to multimodel intervention | Low (opt-in) |
| HIGH | In-Flight Verification (P3) | Add `child-evidence-verify` to `auto-subtask-sync` | Low (natural extension) |
| MEDIUM | Checkpoint/Resume (P4) | Extend worker job tracking with subtask progress | Medium |
| LOW | Runtime Decomposition (P1) | Advisory-only decomposition suggest, not auto-create | High (if auto) |
| LOW | Effort Escalation (P5) | Do not adopt — explicit governance is safer | High |

## Gap Analysis: What Hermes Already Does Better

1. **Governance gates** — Claude Code's auto-workflow trigger has no equivalent of Hermes's `mission_envelope`, `permission_tier`, or `red_lines`. Hermes's fail-closed proof/permission model is more robust.
2. **Multi-model consensus** — Claude Code uses a single model (Claude) for planning and execution. Hermes's multimodel panel provides genuine cross-model verification.
3. **Task persistence** — Hermes's brain markdown + kanban DB dual-store is more durable than Claude Code's conversation-bound checkpoint.
4. **Audit trail** — Every Hermes state transition is recorded in the task note's Proof Log. Claude Code's workflow history is less structured.

## Implementation Feasibility Matrix

| Pattern | Hermes Primitive | Gap Size | Implementation Effort | Risk |
|---------|-----------------|----------|----------------------|------|
| Dynamic Decomposition | `auto-split-non-convergence` | Large | 2-3 weeks | High (runaway decomposition) |
| Adversarial Verification | `multimodel-intervention-step` | Medium | 1 week | Low (opt-in) |
| In-Flight Verification | `auto-subtask-sync` + `proof-check` | Small | 3-5 days | Low |
| Checkpoint/Resume | `agent_team_controller` jobs | Medium | 1-2 weeks | Medium |
| Effort Escalation | `priority_mode` + `permission_tier` | Large | 2+ weeks | High (token waste) |

## Evidence

- Source URL: https://claude.com/blog/introducing-dynamic-workflows-in-claude-code
- Publication date: May 28, 2026
- Key quote: "Dynamic workflows in Claude Code let Claude tackle the most challenging tasks by executing across 10s to 100s of parallel subagents, and checking its work before anything reaches you."
- Bun rewrite case study: 750,000 lines of Rust, 11 days, 99.8% test pass rate
- Hermes taskpool primitives verified: `brain_task_orchestrator.py`, `brain_task_dispatch_tick.py`, `agent_team_controller.py`, `consult_models.py`

## Verification Commands

```bash
# Verify Hermes taskpool infrastructure exists
python3 ~/.hermes/scripts/brain_task_orchestrator.py selfcheck --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py proof-check --json

# Verify multimodel intervention infrastructure
python3 ~/.hermes/scripts/brain_task_orchestrator.py multimodel-intervention-dry-run --json

# Verify agent-team parallel infrastructure
python3 ~/.hermes/scripts/agent_team_controller.py status --json 2>&1 || echo "agent_team_controller not available"
```
