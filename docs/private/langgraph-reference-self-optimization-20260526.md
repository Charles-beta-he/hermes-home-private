# LangGraph reference self-optimization for Hermes — 2026-05-26

Scope: analyze https://github.com/langchain-ai/langgraph as a reference repository for improving Hermes Agent itself. This note is evidence-grounded and intentionally does not propose rewriting Hermes on LangGraph.

Reference checkout:
- URL: https://github.com/langchain-ai/langgraph
- Local clone: `/Users/charles/.hermes/runs/langgraph`
- Commit inspected: `d1e2ff0`
- Evidence extraction: `/Users/charles/.hermes/runs/langgraph-reference-evidence-20260526.md`
- Multi-model tick: `/Users/charles/.hermes/tick-20260526-151123-095792-p10881-6ac3f8d6-68397ca1`

## Multi-model result status

True external multi-model orchestration was attempted with `consult_models.py` T2:
- attempted planners: `claude-opus-4-7`, `gpt-5.5`, `mimo-v2.5-pro`
- only Claude produced a substantive planner result before timeout; GPT and MiMo branches timed out
- discussion participants `claude-opus-4-7` and `gpt-5.5` both rejected/amended certification because the state file had factual claims but no orchestrator-visible `evidence_bundle.evidence` links
- certification status: not certified; useful outcome is a process improvement, not model-certified architecture approval

The key lesson is itself a Hermes improvement: for reference-repo self-optimization, raw excerpts in `context_json` are not enough for the truth gate. Claims must be supplied with explicit evidence records or fulfilled before ratification.

## Evidence-grounded LangGraph patterns

1. Durable long-running agent framing
   - Evidence: root README lines 37-43 describe durable execution, human-in-the-loop, memory, debugging/trace visibility, and deployment for long-running stateful agents.
   - Hermes transfer: keep durable continuation/relay/taskpool/gateway/background work as first-class control-plane concerns, not hidden prompt conventions.

2. Library boundary and blast-radius map
   - Evidence: `AGENTS.md` lines 19-55 splits the monorepo into checkpoint, checkpoint-postgres, checkpoint-sqlite, cli, langgraph, prebuilt, sdk-js, sdk-py, and gives dependency impact directions.
   - Hermes transfer: every Hermes subsystem changed by an optimization should be mapped to an impact class and verification surface before implementation: core loop, tools/gateway, taskpool/brain, scripts, skills/docs, tests/fixtures.

3. Compile-before-execute graph boundary
   - Evidence: `libs/langgraph/langgraph/graph/state.py` lines 130-144 document `StateGraph` as a builder that must be compiled before invoke/stream/ainvoke; lines 101-108 show node default policies for retry/cache/error_handler/timeout.
   - Hermes transfer: self-evolution tasks should separate proposal/build/configuration from executable state. A preflight/compile phase can catch missing schemas, invalid policies, or unsupported side effects before agent execution.

4. Structured checkpoint identity and channel versions
   - Evidence: `libs/checkpoint/langgraph/checkpoint/base/__init__.py` lines 92-123 define checkpoint id, timestamp, channel_values, channel_versions, versions_seen, and updated_channels; lines 176-207 describe checkpointers and thread_id usage.
   - Hermes transfer: continuation/taskpool/background-review packets should preserve explicit run/thread identity, parent relation, state channels, and versions. Avoid opaque text-only handoff when resuming long-running work.

5. Prebuilt reusable layers for tools and human interrupts
   - Evidence: `libs/prebuilt/README.md` lines 40-64 define `ToolNode` and `ValidationNode`; lines 87-116 show Agent Inbox / HumanInterrupt shape with action_request, config, description, and response handling.
   - Hermes transfer: external-control and dangerous action gates should expose typed action requests plus allowed response modes instead of ad-hoc confirmation prose.

## Do not cargo-cult

- Do not rewrite Hermes Agent around LangGraph just because LangGraph is graph-native. Hermes already has conversation loop, tools, cron, taskpool, gateway, skills, and profiles; replacing the runtime would be high blast radius.
- Do not import LangSmith/LangGraph deployment assumptions into local Hermes without separate product fit and credential/privacy review.
- Do not treat multi-model consensus as permission. The run here demonstrates the opposite: consensus blocked certification because evidence was not linked.
- Do not weaken Hermes proof gates to accept large `context_json` excerpts as evidence. Fix evidence packaging instead.

## Immediate Hermes optimization landed

Update the `hermes-agent` skill to require evidence-linked state creation for reference-repo self-optimization before multi-model ratification:
- if using `consult_models.py state`, pass `--evidence-json` records with claim ids and source line/file references, or run `fulfill-evidence` before `run --discussion`
- if fanout falls below `min_quorum`, report degraded/not-certified and land only low-risk docs/skills, not code changes
- if truth gate says unsupported, treat the main output as an evidence-packaging/process gap, not as certified architecture guidance

## Engineering candidates for later taskpool work

1. Evidence packer for reference repos
   - Target: `~/.hermes/scripts/consult_models.py state` or a helper script
   - Artifact: given a repo path and claims, create `evidence_json` records from file:line ranges
   - Verification: deterministic fixture where five claims move from unsupported to supported without changing claims
   - Risk: medium; touches multi-model truth-gate inputs, not runtime agent loop

2. Continuation packet schema hardening
   - Target: Hermes continuation/taskpool/background-review packet schema
   - Artifact: explicit channel/version/parent/run identity fields inspired by checkpoint schema
   - Verification: resume-from-interruption regression preserving parent chain and updated channel list
   - Risk: medium-high; needs migration and backward compatibility

3. Typed human action request envelope
   - Target: external-control / gateway action confirmation paths
   - Artifact: action_request + allowed_response_modes + description schema
   - Verification: existing confirmation tests plus a rejection/edit/accept matrix
   - Risk: medium; improves safety gates but affects UX

## Verification notes

Read-back / evidence commands used:
- `git -C ~/.hermes/runs/langgraph rev-parse --short HEAD` -> `d1e2ff0`
- `read_file` on LangGraph README, AGENTS, core README, prebuilt README, cli README
- `read_file` on `libs/langgraph/langgraph/graph/state.py`, `libs/langgraph/langgraph/types.py`, `libs/checkpoint/langgraph/checkpoint/base/__init__.py`
- `consult_models.py run ... --tier T2 --quorum 3 --discussion --keep --timeout 180` produced tick above; final status degraded/not-certified due planner timeouts and missing explicit evidence records

Reusable rule: reference-repo analysis should emit claim-linked evidence first, model opinions second, and scoped self-changes last.
