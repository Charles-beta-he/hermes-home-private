# Model participant substitution in certification rounds

Use this when a required certification participant must be replaced, renamed, or migrated (for example, switching the Claude participant from an older canonical slug to a newer one) before rerunning a taskpool / multi-model certification round.

## Landing-zone classifier

- Reusable procedure / verification checklist: belongs in this skill.
- Stable user model preference: store in user memory/profile as well, but do not rely on memory alone.
- Credential/session errors while testing a provider: do not store as a durable negative rule; fix or report the setup boundary separately.
- Specific task IDs, tick paths, and one-off artifacts: cite only as transient evidence in the current run, not in the skill.

## Procedure

1. Identify the canonical participant slug the certification system actually reads.
   - Check the quorum/ratification policy, not just the chat model picker.
   - For Hermes local-brain taskpool, the ratification participant list is commonly loaded from `~/.hermes/config/quorum.yaml` and then surfaced by `consult_models.py status`.
2. Update all relevant routing surfaces as a coherent set:
   - ratification `required_models` / `optional_models`;
   - tier planner lists for the affected tier(s), especially T2/T3;
   - default/resident arbiter entries if the old model held the Claude/arbiter role;
   - pricing/router metadata in the active Hermes config if that model is selected by smart routing or verification tiers.
3. Validate config parse before running expensive certification.
   - Load YAML/config with the same path the runtime uses when possible.
   - Run the local status command that prints resolved planners/arbiter and verify the old slug disappeared from the active certification panel.
4. Smoke-test the provider without accepting fallback as evidence.
   - A command that prints the requested text after `Primary auth failed — switching to fallback` proves the fallback works, not that the requested model participated.
   - For Claude Code participants, test the underlying `claude -p ... --model <slug>` path when the certification runner uses Claude Code.
5. Rerun the certification step only after the resolved panel is correct.
   - Preserve the new discussion artifact path and model list.
   - If the old slug is gone but the new participant still fails due to auth/quota/setup, report that as the new boundary; do not claim model-level certification from the other models alone when the task requires that participant.
6. Close or requeue according to the gate result.
   - If the gate requires all required participants, a single required participant with `runtime_error`, `best_within_constraints=false`, or `amend` still blocks `done` even when other models approve.

## Pitfalls

- Updating only `config.yaml` or only `quorum.yaml` can leave the status display and the actual certification runner disagreeing.
- Normalization may preserve dotted slugs for some providers while converting dots to hyphens for others. Verify the exact resolved model list rather than guessing.
- Fallback providers are useful for ordinary chat continuity but are not equivalent to a required certification participant unless the policy explicitly treats them as substitutes.
- Do not convert a setup/auth failure into a permanent rule like “this provider does not work.” The durable lesson is the verification sequence and fallback-evidence boundary.

## Minimum verification

- `consult_models.py status` or equivalent shows the new participant in the relevant tier.
- The old participant slug is absent from the active ratification list.
- The certification run artifact lists the new model in `models_consulted`.
- The final lifecycle decision is based on the certification gate, not on a human-readable fallback response.
