# Multi-model adapter health and internal-projection pitfalls

Use when a multi-model certification run shows repeated planner timeouts, Claude Code `error_max_turns`, or unexplained `schema_mismatch` / `verifier_gap` on otherwise grounded evidence.

## Applicability

- Hermes `consult_models.py` / certification fanout / mainloop certification worker.
- Multi-model self-checks that use Claude Code, MiMo/Xiaomi, GPT/Codex, DeepSeek, Gemini, or similar adapters.
- Mainloop verification gates that can see internal JSON artifacts or continuation handoff text.

Anti-conditions:

- Do not treat a transient provider outage as a permanent negative fact about a model.
- Do not remove a model from all routing globally just because one provider probe failed. Prefer health-gated participation for the affected workflow.
- Do not count fallback/shadow plans as model certification votes.

## Debugging path

1. Separate provider health from packet size.
   - Reproduce with a tiny prompt first, e.g. `hermes chat -q 'ping' --model <model> --provider <provider> --quiet --max-turns 1`.
   - If the tiny prompt times out or produces no stdout, the issue is adapter/provider health, not evidence-bundle size.

2. Inspect the plan artifact, not just the final consensus.
   - Look at `tick-*/plans/<model>.json`.
   - A low-confidence generated shadow plan with text like `timed out after ... via adapter` or `runtime failed` is not a successful vote.

3. For Claude Code planner/verifier calls, disable tools when only JSON/text is needed.
   - Symptom: `subtype=error_max_turns`, `num_turns=2`, `stop_reason=tool_use` while the invocation used `--max-turns 1`.
   - Root cause: Claude Code attempted tool_use; max-turns=1 made the CLI fail before the tool loop could resolve.
   - Fix pattern: add `--tools ""` to the Claude Code planner/verifier invocation and keep the prompt evidence-only.

4. For slow/unhealthy optional providers, use workflow-scoped health gating.
   - Example pattern: support an env flag such as `SKIP_MIMO=1` that removes MiMo/Xiaomi from the planner set for background certification while preserving the ability to re-enable it after health probes pass.
   - Adjust quorum/min-quorum so the remaining independent providers can still satisfy the required evidence gate without creating a brittle all-remaining-must-succeed condition.

5. When a required model is missing from certification, separate static policy from runtime selection.
   - First read the quorum/ratification policy and confirm whether the model is required or only optional.
   - Then inspect the actual selected planner list after health filtering and quota gating; a model can be present in `quorum.yaml` but absent from the fan-out because a model-health circuit breaker is active.
   - Read the durable health state and classify the reason (`auth_invalid` / `model_or_path_invalid` hard skip vs timeout/parse/truncated output soft skip). Do not report “config missing” until the pre-filter policy is proven absent.
   - For MiMo/Xiaomi specifically, a tiny `hermes chat` or direct API probe can pass while planner calls still fail: long planner prompts may spend many tokens in `reasoning_content`, hit `finish_reason=length`, and leave `message.content` empty or truncated, causing JSON extraction failures such as `empty output`. Treat this as a planner-output/adapter-budget issue, not provider auth failure.
   - Stable MiMo repair pattern: remove baked-in small `max_tokens` caps from the Xiaomi planner/probe adapter, allow a workflow-scoped override such as `XIAOMI_MAX_TOKENS`, classify HTTP-200-but-empty/truncated content as `truncated_or_empty_content` rather than `ok`, and retry once with a compact JSON-only prompt when `finish_reason=length` or `message.content` is empty/truncated. Do not fix by lowering quorum, deleting MiMo, or adding a permanent model ban.
   - Required ratification models that are soft-unhealthy should be re-probed with a planner-shaped prompt before clearing health or rerunning; otherwise the next round may silently replace the required model with another healthy planner to satisfy min_quorum but still fail required-model ratification.
   - Keep taskpool quota/health observability aligned with the certification panel: if MiMo is required in `quorum.yaml`, the taskpool API quota/capacity model set should include it too, so dispatch summaries show whether it was checked, passed, soft-unknown, or hard-blocked.

6. Treat evidence gaps as packet/gate bugs until proven otherwise.
   - If evidence exists but truth gate reports `evidence_coverage=0.0`, check claim IDs after state generation. Single-claim states may normalize to `C-001`; evidence supporting a chunk slug will not link.
   - If claim-level evidence is green but route-specific evidence is missing, add a route-required-evidence ledger (`required`, `present`, `missing`, `coverage`) and fail closed on T3/blocking tiers.

6. Exclude internal projections from completion-claim gates.
   - Internal multi-brain planner JSON (`planner_model`, `diagnosis`, `patches`) and auto-relay continuation handoffs can contain words like “complete/verified” but are not user-facing completion claims.
   - Gate them as `skipped_internal_projection` (or equivalent) before generating certification jobs, otherwise the queue fills with JSON-fragment claims that inevitably produce `schema_mismatch` / `needs_link_review`.

## Verification checklist

- [ ] Tiny provider probe distinguishes provider health from packet size.
- [ ] Claude Code planner/verifier calls that need no tools include `--tools ""` or an equivalent tool-disable setting.
- [ ] Optional/unhealthy providers are excluded by workflow-scoped health gating, not by a global permanent ban.
- [ ] Quorum after exclusions still requires at least two independent successful reviewers for certification-critical claims.
- [ ] Generated state claim IDs match every evidence item's `supports` links.
- [ ] Route-required evidence coverage is reported separately from claim-level truth coverage.
- [ ] Internal JSON/auto-relay projections do not enqueue completion certification jobs.
