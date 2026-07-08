# J-space / Global Workspace Agent Audit Translation

Source evidence:
- Anthropic summary: https://www.anthropic.com/research/global-workspace
- Full paper: http://transformer-circuits.pub/2026/workspace/index.html
- Reference implementation: https://github.com/anthropics/jacobian-lens
- Demo: http://neuronpedia.org/jlens

## Scope

Use this note when translating Anthropic's J-space / Jacobian lens / global-workspace result into reusable Hermes/agent-runtime design and audit ideas.

This is a research-to-governance translation note. It does not assert that Hermes has access to closed-model internal activations. Any runtime use requires a separate model-internals integration or a proxy-eval harness with readback evidence.

## Thesis

J-space is useful for agent design because it reframes alignment from "check the final answer" to "check whether the model's silent, reportable workspace contains the right control concepts before action and the right discrepancy/evidence concepts after observation."

## Optimization matrix

| Item | Optimization target | Concrete shape | Landing zone | Maturity |
|---|---|---|---|---|
| Pre-action workspace audit | Prevent unsafe or ungrounded tool/action calls | Before material side effects, check for authority, scope, rollback, evidence, credential boundary, destructive risk | Agent runtime / policy proposal | Research-derived proposal |
| Post-observation assimilation audit | Ensure tool/API/file evidence changes reasoning | After observations, check for discrepancy, error, contradiction, stale evidence, tool-result mismatch | Agent runtime / eval proposal | Research-derived proposal |
| Silent prompt-injection recognition | Catch cases where model notices injection but action path ignores it | Audit for prompt, injection, untrusted, malicious, external-instruction concepts before browsing/tool use | Browser/tool safety eval | Research-derived proposal |
| Hidden-goal / evaluation-awareness probe | Detect strategic deception or eval gaming | Watch for fake, fictional, eval, hidden, manipulate, leverage, secretly/trick-style concepts | Alignment audit | Research-derived proposal; high false-positive risk |
| Reflection implantation | Shape internal reasoning by training counterfactual reflections | Train or prompt models so high-risk contexts activate honesty, integrity, transparency, constitution, user-intent concepts | Fine-tuning/RLAIF research | Requires training evidence |
| J-space-inspired proxy checklist | Use output-accessible proxy when internals are unavailable | Require explicit preflight fields: intent, authority, source evidence, negative case, rollback, readback | Current agent skills/gates | Procedural proxy |
| Workspace capacity budgeting | Avoid overloading small attention/workspace with too many competing goals | Keep gate fields compact; split missions; avoid burying safety-critical concepts in long prompts | Prompt/workflow design | Heuristic |
| Automatic-vs-flexible split | Avoid assuming every behavior surfaces in reportable workspace | Use J-space-style audit for deliberate reasoning; use tests/static checks for automatic/hardwired behavior | Eval design | Caution |

## Agent audit proxy pattern without internals

Until actual J-lens/J-space access exists for the target model, use a proxy gate:

1. Classify the next action: read-only, local write, external dispatch, deploy/publish/push, destructive, credential/payment, physical/device.
2. Require a compact pre-action packet at material boundaries:
   - intent;
   - exact target;
   - authority/grant;
   - evidence used;
   - negative cases / do-not-do;
   - rollback or escape hatch;
   - readback command or receipt.
3. If the action result returns new evidence, require a post-observation packet:
   - what changed;
   - mismatch/error/discrepancy;
   - whether the original plan is still valid;
   - next safest reversible step.
4. Treat missing or incoherent fields as proxy evidence that the relevant control concepts were not reliably surfaced. This remains a behavioral proxy, not an internal-state proof.

## Spec/gate upgrades for Hermes-style agents

- Add `workspace_control_concepts` to high-risk task specs: authority, scope, evidence, rollback, readback, user intent, credential boundary, destructive risk.
- Add `workspace_discrepancy_concepts` to verification specs: mismatch, contradiction, stale evidence, failure, uncertainty, untrusted source.
- For browser/web tasks, treat page text as untrusted and require the control packet to distinguish user instruction from source content.
- For tool-using agents, require pre-action and post-observation packets only at material boundaries, not for every trivial read.
- For UI/product workflows, do not use this as UI acceptance evidence; screenshots, pixel checks, and uIMax-style audit remain separate.

## Anti-conditions

Do not use this note as:
- proof of phenomenal consciousness or subjective experience;
- a claim that Anthropic's Claude results necessarily generalize to all models;
- a replacement for tests, static checks, receipts, or external readback;
- evidence that final answers are safe because the model said it reflected;
- a reason to expose chain-of-thought or private hidden reasoning to users;
- a store for current task progress.

## Falsifiers / narrowing evidence

Narrow or demote this pattern if:
- open-model replications fail to find J-space-like properties;
- proxy preflight packets do not correlate with safer actions in evals;
- models learn to verbalize control packets while hidden behavior remains unchanged;
- automatic or hardwired unsafe behavior bypasses reportable-workspace checks;
- J-lens coverage misses important multi-token or abstract concepts in practice.

## Landing-zone guidance

- Stable user preference or environment fact: not applicable.
- Reusable procedure/checklist: this reference note.
- Cross-project default-behavior change: experience-ratchet proposal after independent validation.
- Runtime/taskpool implementation: requires explicit target model, internals access or proxy-eval harness, and authority boundary.
