# Codex agent loop vs. agent control plane

Scope: class-level comparison of focused coding-agent inner loops and general autonomous-agent control planes. This is not a project status record and does not authorize implementation or runtime mutation.

Applicability:
- A user asks to analyze OpenAI's **“Unrolling the Codex agent loop”** or compare a focused coding-agent harness with Hermes or another general autonomous-agent system.
- The analysis concerns prompt-prefix caching, tool dispatch, context compaction, sandbox ownership, turn termination, or control-plane/executor boundaries.

Anti-conditions:
- Do not treat this article as a complete description of every Codex product surface; its scope is the Codex harness and inner agent loop.
- Do not infer current runtime behavior from article prose alone when source, docs, traces, or local code can be inspected.
- Do not equate a tool appearing in one agent UI with that tool inheriting the host's sandbox or authority model.
- Do not turn comparison findings into automatic permission for runtime changes, external writes, deployment, or lifecycle mutation.

Canonical source:
- OpenAI article: `https://openai.com/index/unrolling-the-codex-agent-loop/`
- OpenAI News RSS records the publication date as 2026-01-23 and describes it as a technical deep dive into how Codex CLI orchestrates models, tools, prompts, and performance through the Responses API.
- Implementation evidence linked by the article: `https://github.com/openai/codex`

## Core article model

```text
user input
  -> assemble instructions + tools + conversation items
  -> model inference
       -> assistant message: end the turn
       -> tool call: execute tool, append result, infer again
```

Distinguish:
- **Turn**: one user input until control returns to the user.
- **Iteration**: one inference/tool-call cycle within the turn.
- **Artifact output**: code/files/environment mutations may be the primary output; the assistant message is the termination signal, not the whole deliverable.

The durable architectural lesson is:

```text
agent behavior = model capability + harness policy + tools + context management
```

Using the same model in two harnesses does not make them the same agent.

## Important OpenAI engineering claims

1. **Exact-prefix caching**
   - Codex sends complete, stateless request context rather than relying on `previous_response_id` in the described path, preserving straightforward Zero Data Retention support.
   - Repeated full requests are network-heavy, but model computation can remain effectively linear when the old prompt is an exact prefix of the new prompt and provider prompt caching hits.
   - Model changes, tool-schema changes, tool-order instability, sandbox/approval changes, or working-directory changes may invalidate the reusable prefix.
   - Prefer appending new state as later messages over rewriting old messages.

2. **Tools are prompt surface**
   - Tool definitions consume context on every inference call.
   - Dynamic tools are not free; ordering and schema stability affect cache behavior.

3. **Sandbox ownership is per execution surface**
   - Codex's sandbox instructions apply to the Codex-provided shell tool.
   - MCP tools are responsible for their own guardrails; they do not automatically inherit the Codex shell sandbox.

4. **Compaction is core runtime behavior**
   - Conversation growth can exhaust the model context window inside one turn.
   - The article describes automatic use of `/responses/compact`, returning compacted input items including opaque encrypted compaction state.
   - Provider-native compaction can preserve model-specific latent state better than a plain natural-language summary, but is less portable.

## Comparison method

Before comparing systems, establish evidence for both sides:

1. Read the canonical article and its linked implementation/docs.
2. Inspect the current target harness documentation and source for:
   - turn loop and termination;
   - prompt assembly and role precedence;
   - tool-schema stability and dispatch;
   - sequential/parallel execution;
   - context thresholds and compaction failure behavior;
   - persistence, memory, skills, and session lineage;
   - sandbox/approval ownership;
   - retry, fallback, interruption, and iteration budgets;
   - subagents, schedulers, gateways, task ledgers, and external adapters.
3. Separate **inner-loop features** from **outer-control-plane features**.
4. Separate verified current behavior from design intent or marketing claims.
5. Compare advantages together with the state, cost, and security liabilities they introduce.

## Inner loop vs. outer control plane

A focused coding harness typically owns:
- prompt construction;
- inference/tool iterations;
- repository-aware instructions;
- shell/editor execution;
- sandboxing;
- context compaction;
- final assistant-message termination.

A general control plane may additionally own:
- persistent sessions and scoped recall;
- durable memory and reusable skills;
- subagent delegation and multi-model review;
- cron/event wakeups and cross-turn continuation;
- task ledger, lifecycle gates, evidence, and approvals;
- messaging gateways and external-system adapters.

Do not compare these as if they were identical layers. The recommended additive architecture is usually:

```text
Hermes/general control plane
  -> exact worker contract
  -> Codex or another coding-agent executor
  -> evidence/result proposal
  -> control-plane verification and authority gate
```

The worker should not gain lifecycle, external-write, deployment, or notification authority merely because it can execute code.

## Balanced comparison axes

Use these axes rather than a single “which is stronger?” score:

- Software-engineering specialization
- Provider portability
- Prompt/cache determinism
- Compaction fidelity and failure behavior
- Tool breadth and schema cost
- Sandbox and approval boundaries
- Parallel tools and subagents
- Session persistence and long-term learning
- Cross-turn/cross-time continuation
- Evidence, governance, and rollback
- Runtime complexity and state-coupling risk

Typical conclusion:
- A focused Codex-style harness is often stronger as a high-quality repository executor.
- Hermes-style systems are broader as persistent, multi-surface control planes.
- The broad system also carries more cache, state-consistency, memory-pollution, and authority-coupling risk.

## Image generation: two separate tool-selection loops

When a GPT-backed Hermes session receives a request to create an image, distinguish two stages:

1. **Hermes main-loop selection**
   - `image_generate` is an ordinary Hermes function tool exposed alongside the other enabled tools.
   - In the OpenAI/Codex Responses transport, the main request uses `tool_choice="auto"`; merely registering the tool does not force it.
   - The model should select it for a concrete image-artifact request because the tool contract and Hermes execution policy require producing the artifact, but this is model-directed selection rather than a hard image-intent router.
   - If the tool/plugin is disabled or unavailable, the GPT model cannot silently substitute a native image result through this Hermes path.

2. **Image-provider execution after selection**
   - `image_generate` dispatches to the configured image provider; that provider is independent of the main chat model/provider.
   - The active provider may be FAL, OpenAI, xAI, or another configured backend. Do not infer the backend from “the main model is GPT.”
   - Hermes's `openai-codex` image provider is intentionally deterministic after dispatch: its nested Responses request declares OpenAI's native `image_generation` tool and sets `tool_choice` to `allowed_tools` with `mode="required"`.

Therefore the precise answer to “does GPT default to Image Generator?” is:

```text
main GPT -> Hermes image_generate: normally selected for an actual generation request, but tool_choice is auto, not forced
Hermes image_generate -> configured provider: deterministic provider dispatch
openai-codex image provider -> native image_generation: required/forced
```

Do not conflate the Hermes tool name `image_generate`, a UI label such as “Image Generator,” and OpenAI Responses' native tool type `image_generation`.

### Image-routing verification recipe

Do not answer this routing question from the main model/provider name alone. Verify all three boundaries:

1. **Main-loop request construction**
   - Inspect `agent/transports/codex.py::ResponsesApiTransport.build_kwargs`.
   - Confirm enabled Hermes functions are exposed and record whether `tool_choice` is `auto`, `required`, or an explicit named tool.
2. **Provider dispatch**
   - Inspect the runtime `image_generate` tool description/config to identify the active image provider and model.
   - Treat this as independent from the main chat provider; a GPT main model may dispatch to FAL, xAI, OpenAI, or another configured backend.
3. **Nested native-image request**
   - For the Hermes OpenAI-Codex image provider, inspect `plugins/image_gen/openai-codex/__init__.py::_build_responses_payload`.
   - Confirm the native tool type, model, and forced/automatic selection mode from the actual payload.

Targeted Hermes verification:

```bash
.venv/bin/python -m pytest -q \
  tests/agent/transports/test_codex_transport.py \
  tests/plugins/image_gen/test_openai_codex_provider.py
```

For stronger evidence, construct both payloads locally and read back only non-secret routing fields such as `tool_choice`, exposed tool names, prompt-cache-key prefix, native image tool type, and native image model. Do not trigger a paid image generation merely to prove request routing when deterministic payload tests suffice.

## Review checklist

- [ ] Correct article/title/date and canonical source were resolved.
- [ ] Model and harness were described as separate layers.
- [ ] Turn and iteration were not conflated.
- [ ] Exact-prefix caching implications were covered.
- [ ] Tool-schema and sandbox ownership boundaries were covered.
- [ ] Provider-native versus portable lossy compaction was compared.
- [ ] Inner loop and outer control plane were separated.
- [ ] Current target-harness claims were grounded in current docs/code/traces.
- [ ] Benefits were paired with new state/security liabilities.
- [ ] Recommendations kept coding agents as constrained workers unless wider authority was explicitly justified.
