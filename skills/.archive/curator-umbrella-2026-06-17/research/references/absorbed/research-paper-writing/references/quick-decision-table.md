# Quick Decision Table

Extracted from `/Users/charles/.hermes/skills/.archive/curator-umbrella-2026-06-17/research/references/absorbed/research-paper-writing/SKILL.md` on 2026-07-01T08:56:29.614759+00:00 during full core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

### Quick Decision Table

| Your Situation | Strategy | Why |
|---------------|----------|-----|
| Mid-tier model + constrained task | **Autoreason** | Sweet spot. Generation-evaluation gap is widest. Baselines actively destroy weak model outputs. |
| Mid-tier model + open task | **Autoreason** with scope constraints added | Add fixed facts, structure, or deliverable to bound the improvement space. |
| Frontier model + constrained task | **Autoreason** | Wins 2/3 constrained tasks even at frontier. |
| Frontier model + unconstrained task | **Critique-and-revise** or **single pass** | Autoreason comes last. Model self-evaluates well enough. |
| Concrete technical task (system design) | **Critique-and-revise** | Direct find-and-fix loop is more efficient. |
| Template-filling task (one correct structure) | **Single pass** or **conservative** | Minimal decision space. Iteration adds no value. |
| Code with test cases | **Autoreason (code variant)** | Structured analysis of *why* it failed before fixing. Recovery rate 62% vs 43%. |
| Very weak model (Llama 8B class) | **Single pass** | Model too weak for diverse candidates. Invest in generation quality. |
