# Feynman reference review → Hermes absorption gap analysis

Date: 2026-05-31
Task: `2026-05-30-feynman-开源-ai-研究代理架构分析与-hermes-吸收评估`
Reference boundary: Feynman is a reference architecture only. This note does not integrate Pi, Astro, alphaXiv, Feynman runtime packages, or Feynman-specific agent names into Hermes.

## Source pin

- Repository: https://github.com/companion-inc/feynman
- Local review checkout: `/Users/charles/.hermes/runs/feynman-reference-review-20260530`
- Commit reviewed: `51236f6ae60a2894f9987465f431e9fe7c1a777a`
- Repo instructions read: `AGENTS.md`
- Hermes target constraints read: `/Users/charles/.hermes/AGENTS.md`, `/Users/charles/.hermes/hermes-agent/AGENTS.md`, task note `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-30-feynman-开源-ai-研究代理架构分析与-hermes-吸收评估.md`

## Executive summary

Feynman’s transferable value is not its TypeScript/Pi runtime. The useful pattern is a research-run evidence spine:

1. A plan artifact is created first and maintained as external working memory.
2. Subagents write intermediate artifacts to disk instead of returning large inline payloads.
3. A verifier stage anchors claims to sources and removes unsupported claims.
4. A provenance sidecar is delivered next to the final artifact.
5. A workspace changelog records long-running/resumable research state.
6. Skill packages are shipped as installable artifacts, but Hermes should only absorb this as a governed skill/template intake pattern, not a blind installer.

The minimal landed slice is a Hermes-local scaffold script:

- `/Users/charles/.hermes/scripts/research_artifact_scaffold.py`

It creates the same durable skeleton for Hermes research/evolution tasks: `outputs/.plans/<slug>.md`, `outputs/.drafts/<slug>-draft.md`, `outputs/<slug>.provenance.md`, and `CHANGELOG.md` under a caller-chosen workspace. It deliberately does not mutate task lifecycle state or assert proof.

## Evidence map from Feynman

| Pattern | Source evidence | What it proves | Hermes absorption decision |
|---|---|---|---|
| Repo-level artifact contract | `AGENTS.md` says research outputs go in `outputs/`, drafts in `papers/`, session logs in `notes/`, plan artifacts in `outputs/.plans/`, and `CHANGELOG.md` is the workspace lab notebook. | Feynman makes filesystem artifacts the continuity layer. | Adopt as research/evolution artifact scaffold, scoped per run/workspace. |
| Plan artifact as external working memory | `AGENTS.md` says long-running workflows should treat plan artifacts as externalized working memory; `prompts/deepresearch.md` requires creating `outputs/.plans/<slug>.md` immediately with key questions, evidence needed, task ledger, verification log, decision log. | Planning state is not hidden in chat context. | Adopt for Hermes long-running research tasks and evolution tasks. |
| File-based subagent handoff | `AGENTS.md` says intermediate research artifacts are written to disk by subagents and read by the lead agent; `prompts/deepresearch.md` assigns researcher output files and says parent reads output files. | Parent/subagent boundary is artifact-first. | Adopt as a Hermes template for delegated research; do not require Feynman’s Pi subagent tool. |
| Verifier as explicit claim gate | `.feynman/agents/verifier.md` requires anchoring every factual claim to sources, verifying URLs, removing unsupported claims, and rejecting fake certainty. | Verification is a named stage, not ad hoc cleanup. | Adopt as a checklist in provenance sidecars and taskpool proof review. |
| Provenance sidecar | `AGENTS.md` requires `.provenance.md` sidecars for `/deepresearch` and `/lit`; `prompts/deepresearch.md` defines sidecar fields: date, rounds, sources consulted/accepted/rejected, verification state, plan, research files. | Final artifact and evidence accounting are delivered together. | Adopt for Hermes research artifacts, but keep taskpool Proof Log as lifecycle SSOT. |
| Workspace changelog | `AGENTS.md` defines `CHANGELOG.md` as lab notebook and says append after meaningful progress, failures, verification, or blockers. | Long-running continuity is chronological and inspectable. | Adopt only for substantial/resumable workspaces, not trivial one-shots. |
| Skill installation | `README.md` and `scripts/install/install-skills.sh` install bundled `skills/`, `prompts/`, `AGENTS.md`, and `CONTRIBUTING.md` into Codex/repo/OpenCode targets. `src/bootstrap/sync.ts` syncs managed themes, agents, and skills with hashes and skips user-modified targets. | Skills are packaged as portable resources with overwrite safety. | Hermes should absorb the governed package-intake/manifest idea, not remote curl installers or blind overwrites. |

## Hermes current-state comparison

| Area | Current Hermes baseline | Gap vs Feynman | Recommended mainline path |
|---|---|---|---|
| Task proof | Hermes taskpool has Proof Log, `proof_artifacts`, `evidence_refs`, mission envelope, red lines, and `brain_task_orchestrator.py` as lifecycle SSOT. | Stronger lifecycle proof than Feynman, but research outputs do not always get sidecar provenance. | Add optional research artifact scaffold; do not weaken proof gates or replace taskpool proof. |
| Plan state | Hermes has task notes/workpads and handoff artifacts, but plan/update/provenance shape is not standardized for ad hoc research runs. | Feynman has a concrete per-run `outputs/.plans/<slug>.md` structure. | Use scaffold for evolution/reference-repo reviews and point task evidence at generated files. |
| Subagent orchestration | Hermes has `delegate_task`, Kanban workers, and agent-team controller; summaries may be inline. | Feynman’s discipline is that large subagent outputs are files, parent reads the files, and skipped tasks are recorded in the plan ledger. | For research/reference-review tasks, instruct subagents to write specific artifact files and return only handles. |
| Provenance | Hermes has proof refs and source-grounding norms; not every research artifact has a sidecar with source accounting. | Feynman sidecar shape makes accepted/rejected/blocked source status explicit. | Add `.provenance.md` sidecars for long-running research artifacts. |
| Skill package intake | Hermes skills are richer and profile-aware; installing external skills can affect runtime behavior. | Feynman installers are convenient but would bypass Hermes governance if copied directly. | Keep external skill intake behind review, manifest, diagnostics, and scoped skill creation. |

## Gap matrix

| External pattern | Hermes gap | Proposed local artifact/change | Acceptance criterion | Non-claim |
|---|---|---|---|---|
| Plan artifact first | No lightweight script/template to create a research plan/provenance skeleton under an arbitrary workspace. | Land `scripts/research_artifact_scaffold.py`. | Script creates plan, draft, provenance, changelog under a temp workspace and compiles. | Does not run research or certify claims. |
| Provenance sidecar | Sidecar shape not consistently attached to research deliverables. | Scaffold creates `outputs/<slug>.provenance.md` with source accounting and verification sections. | Read generated sidecar; it must say verification is BLOCKED until evidence is filled. | Does not replace taskpool Proof Log. |
| File-based subagent handoff | Delegated work can still overuse inline summaries. | Document artifact-first subagent handoff in this analysis and template. | Gap doc names exact file handles to require from subagents. | Does not change core delegate_task behavior. |
| Skill installation | No need for Feynman remote installer; Hermes has governed skill system. | Defer to existing Hermes skill governance; consider future manifest validator only if needed. | This task lands no blind installer. | Does not install Feynman skills globally. |

## Effectiveness benchmark

Benchmark shape: compare a Hermes research/evolution worker without the scaffold vs with the scaffold for a bounded reference-repo review.

| Dimension | Existing Hermes-only workflow | With landed scaffold | Expected effect |
|---|---|---|---|
| Startup artifacts | Worker must manually decide filenames; plan/provenance may remain in chat or task note. | One command deterministically creates plan, draft placeholder, provenance sidecar, changelog. | Lower omission risk for artifact proof. |
| Parent/subagent context load | Subagent summaries can become verbose unless explicitly constrained. | Plan file gives stable output filenames; subagents can return paths only. | Less context churn and clearer handoffs. |
| Proof closeout | Proof Log remains authoritative but may point to heterogeneous artifacts. | Proof Log can point to standard plan/provenance paths. | Easier deterministic verification. |
| Red-line safety | Taskpool gates already strong. | Scaffold has no lifecycle mutation and sidecar begins as `Verification: BLOCKED`. | Does not weaken taskpool proof/permission/mission gates. |
| Cost | Manual artifact setup per task. | One stdlib Python script call; no network/runtime dependency. | Faster bounded slice with low blast radius. |

Smoke benchmark result from this task:

- Command: `python3 /Users/charles/.hermes/scripts/research_artifact_scaffold.py "Feynman Hermes absorption benchmark" --root /tmp/agent-team-2026-05-30-f/scaffold-smoke`
- Expected/generated slug: `feynman-hermes-absorption-benchmark`
- Expected artifacts: `/tmp/agent-team-2026-05-30-f/scaffold-smoke/outputs/.plans/feynman-hermes-absorption-benchmark.md`, `/tmp/agent-team-2026-05-30-f/scaffold-smoke/outputs/.drafts/feynman-hermes-absorption-benchmark-draft.md`, `/tmp/agent-team-2026-05-30-f/scaffold-smoke/outputs/feynman-hermes-absorption-benchmark.provenance.md`, `/tmp/agent-team-2026-05-30-f/scaffold-smoke/CHANGELOG.md`

## Landed minimal slice

`/Users/charles/.hermes/scripts/research_artifact_scaffold.py` is a bounded slice because it:

- uses only Python stdlib;
- writes only caller-scoped workspace artifacts;
- creates no tasks, claims, lifecycle transitions, model calls, network calls, or installer side effects;
- initializes provenance as BLOCKED until real evidence is filled;
- can be verified with `py_compile` and a temp-workspace smoke run.

## Future candidates, intentionally not landed in this slice

1. Add a Hermes skill/reference for artifact-first research delegation after the scaffold has been used in at least one more task.
2. Add a validator that checks a final research artifact has a provenance sidecar and no `Verification: BLOCKED` before taskpool closeout.
3. Add a governed external-skill package manifest importer. This must preserve Hermes profile boundaries, provenance, and explicit user approval.
4. Add optional Kanban worker prompt text for research tasks: subagents return file paths, not large findings.

## Red-line review

- Taskpool proof gates: safe. This work adds docs and a scaffold only; it does not modify `brain_task_orchestrator.py`, lifecycle gates, or proof evaluation.
- Permission gates: safe. The script does not perform privileged actions or mutate runtime config.
- Mission-envelope gates: safe. The task note remains the task-local SSOT; this document is supporting evidence.
- Advisory/model opinions: safe. Prior advisory-only artifacts are cited only as task history, not implementation proof.
