# Anthropic J-space / Global Workspace Research Note

Use when the user asks about Anthropic's "J-space", Jacobian lens, global workspace in language models, or related interpretability claims.

## Canonical sources

- Anthropic summary: https://www.anthropic.com/research/global-workspace
- Full Transformer Circuits paper: http://transformer-circuits.pub/2026/workspace/index.html
- PDF: https://www-cdn.anthropic.com/files/4zrzovbb/website/cc4be2488d65e54a6ed06492f8968398ddc18ebe.pdf
- Reference implementation: https://github.com/anthropics/jacobian-lens
- Demo: http://neuronpedia.org/jlens

## Retrieval pattern

If web search is blocked or noisy, use Anthropic's sitemap as the source of truth:

1. Fetch `https://www.anthropic.com/sitemap.xml` with a browser-like user agent.
2. Filter `/research/` URLs, prioritizing recent `lastmod` entries.
3. Fetch candidate pages and search for `J-space`, `J space`, `Jacobian lens`, or `global workspace`.
4. Extract article links for the full paper, PDF, code repo, and demo from the Anthropic page.
5. Use the full Transformer Circuits paper for technical claims; use the Anthropic blog for plain-English framing.

## Core concepts to preserve

- **J-lens / Jacobian lens**: maps an intermediate residual-stream activation through an average input-output Jacobian to the final-layer/unembedding basis, reading out tokens the model is disposed to verbalize later.
- **J-space**: the subspace spanned by J-lens token directions; named after Jacobian. A token lighting up means the concept is internally salient / verbalizable, not necessarily that the model will output that token.
- **Global-workspace claim**: Anthropic argues J-space satisfies functional properties analogous to access-consciousness/global-workspace theories: reportability, directed modulation, internal reasoning, flexible broadcast/generalization, and selectivity.
- **Safety relevance**: J-lens can expose silent cognition such as eval-awareness, prompt-injection recognition, planned fabrication/manipulation, hidden-goal signatures, or tool-result discrepancies.
- **Training relevance**: counterfactual reflection training changes what the model is disposed to say if asked to reflect, and can shift silent reasoning/behavior by populating J-space with constitution/ethics concepts.

## Analysis cautions

- Do **not** claim this proves phenomenal consciousness or subjective experience. The paper explicitly focuses on functional/access-consciousness analogies.
- Do **not** equate J-space with chain-of-thought. CoT is text; J-space is internal activation content that may never be output.
- Treat J-lens readouts as token/bag-of-ideas evidence, not complete sentences or full natural-language thoughts.
- Note limitations: one-token vocabulary bottleneck, multi-token/abstract concept diffusion, imperfect lens coverage, and need for open-model replication beyond Anthropic's internal Claude experiments.

## Good response shape

For user-facing analysis, provide:

1. Original-source links table.
2. One-sentence thesis.
3. Explanation of J-lens vs J-space.
4. Evidence organized by the five global-workspace properties.
5. Safety/alignment implications.
6. Boundary/caution section separating functional access from consciousness claims.
7. Practical implications for agent auditing or interpretability if relevant to the user's interests.

## Agent-runtime absorption

When the user asks to absorb the paper into Hermes/agent workflow optimization, use `references/j-space-agent-audit-translation.md`.

Key reusable translation: treat J-space as inspiration for material-boundary audits. Before high-side-effect actions, ensure the control concepts are explicit: intent, authority, evidence, scope, negative cases, rollback, and readback. After tool observations, ensure discrepancy concepts are explicit: mismatch, contradiction, stale evidence, failure, uncertainty, and untrusted source. This is a behavioral proxy unless real J-lens/J-space internal-state access exists for the target model.
