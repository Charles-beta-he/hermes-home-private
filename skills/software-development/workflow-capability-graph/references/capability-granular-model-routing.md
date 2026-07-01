# Capability-granular model routing

Use this reference when a workflow/router discussion moves beyond coarse risk tiers (T0/T1/T2/T3) and needs to route small-grain task capabilities to the best specialist model first.

## Core rule

Route by capability primary first, then add risk-layer verification:

```text
user request
→ detect capability surface
→ select best specialist primary model
→ classify risk tier
→ add reviewer/arbiter/evidence gates only when risk or acceptance requires it
```

Do not make every task multi-model by default. Multi-model fanout is a verification/risk layer, not the first routing decision for every small task.

## Recommended surface mapping

- `ui_visual`, screenshot review, aesthetic judgment, design consistency, image prompts, visual copy/asset direction:
  - primary: Gemini-class multimodal model
  - verifier/fallback: Claude/GPT depending on availability
  - evidence: screenshot matrix, browser snapshot, visual diff/audit, interaction smoke when runtime UI is claimed
- `code_review`, architecture review, boundary review, risk arbitration:
  - primary: Claude Code / Claude Opus-class model
  - verifier: DeepSeek/GPT when independent review is required
  - evidence: diff refs, test/build output, review report, source refs
- `codegen`, implementation, patching, terminal-driven debugging:
  - primary: Codex/GPT-class implementation model
  - verifier: DeepSeek/Claude for high-risk changes
  - evidence: git diff, focused tests, build/runtime smoke
- `low_cost_triage`, first-pass classification, quick routing:
  - primary: MiMo/cheap triage model
  - verifier: none unless risk escalates
- `architecture_boundary`, P10/system design/control-plane decisions:
  - primary/arbiter: Claude Opus-class model
  - verifier: DeepSeek/GPT/Gemini depending on surface
  - evidence: repo/config refs, risk matrix, rollback plan

## Procedure

1. Define surfaces explicitly (`ui_visual`, `code_review`, `code_correctness`, `architecture_boundary`, etc.).
2. For each surface, declare `primary`, `verifier`, `fallback_verifier`, required evidence, and whether the implementer vote counts.
3. Keep self-certification forbidden: a model that produced/implemented a surface can self-report, but does not certify it.
4. Keep objective evidence authoritative: model votes are advisory without test/UI/API/readback evidence.
5. Trigger overlap voting or arbiter only when multiple surfaces are involved, risk tier is high, or evidence conflicts.
6. Verify with deterministic router smoke tests, e.g. UI task routes to Gemini and review task routes to Claude, plus provider availability/readback.

## Pitfalls

- Coarse-tier trap: T2/T3 risk routing alone does not capture who is best at UI, visual, review, or triage work.
- Fanout tax trap: making all tasks multi-model increases cost/latency and can reduce clarity; route to a specialist primary first.
- Model-as-proof trap: Gemini visual judgment or Claude review is not acceptance without objective evidence.
- Main-model displacement trap: specialist routes should not silently replace the current conversation model for ordinary chat.
- Commit-boundary trap: if a wider repo commit is blocked by unrelated pre-existing guards, commit any scoped subrepo changes that can be cleanly verified and report the remaining root-repo boundary rather than bypassing hooks.

## Verification checklist

- [ ] Router has deterministic tests for at least UI→Gemini and review→Claude primary selection.
- [ ] Runtime capability route exposes per-surface primary model and independent verifier.
- [ ] Provider probe/readback shows the chosen specialists are currently available, or fallback/fail-closed behavior is explicit.
- [ ] Evidence requirements are surface-specific and not satisfied by model votes alone.
- [ ] Portfolio/project ledger records the decision only as validated to the level actually proven.
