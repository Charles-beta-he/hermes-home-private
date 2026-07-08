# Core Works and Hermes Landing Map

## Direct Context Engineering

1. `A Survey of Context Engineering for Large Language Models`
   - URL: https://arxiv.org/abs/2507.13334
   - Use: canonical survey/taxonomy.
   - Transferable claim: context engineering optimizes the information payload at inference time, not just prompt phrasing.
   - Hermes landing: Context Packet schema, Evidence DAG, context selection score.

2. `Awesome Context Engineering`
   - URL: https://github.com/Meirtz/Awesome-Context-Engineering
   - Use: broad resource map across RAG, memory, agent runtime, protocols, observability, and evaluation.
   - Hermes landing: roadmap taxonomy and reference index.

3. `context-engineering-intro`
   - URL: https://github.com/coleam00/context-engineering-intro
   - Use: AI coding practice pattern: project rules, examples, INITIAL request, PRP generation, validation gates.
   - Hermes landing: Spec Packet + task plan + validation/readback gates.

4. `SmoothAgent: Efficient Long-Horizon LLM-Based Agent Serving with Lookahead Context Engineering`
   - URL: https://arxiv.org/abs/2607.00151
   - Use: runtime/serving lens for long-horizon agents.
   - Transferable claim: offloading, reduction, isolation, and precomputed transformations reduce context overhead.
   - Hermes landing: future runtime compression/isolation/cache-aware work, not current local foundation.

## Foundational Lineage

- RAG: https://arxiv.org/abs/2005.11401
- ReAct: https://arxiv.org/abs/2210.03629
- Toolformer: https://arxiv.org/abs/2302.04761
- MemGPT: https://arxiv.org/abs/2310.08560
- Generative Agents: https://arxiv.org/abs/2304.03442
- Reflexion: https://arxiv.org/abs/2303.11366
- Lost in the Middle: https://arxiv.org/abs/2307.03172
- RULER: https://arxiv.org/abs/2404.06654
- DSPy: https://arxiv.org/abs/2310.03714
- Ragas: https://arxiv.org/abs/2309.15217

## Landing Boundaries

Safe local landing:
- SSOT/profile/docs/templates/scripts.
- Skill reference and workflow checklist.
- Local lint and examples.

Requires separate exact authority:
- Hermes core runtime prompt assembly changes.
- Taskpool lifecycle mutation.
- Cron/scheduler enablement.
- Dashboard/control-room UI changes.
- External gateway delivery, publish/deploy/push, credentials, destructive operations.

## Falsifiers

Narrow or revise this skill if:
- Context Packet overhead slows simple tasks without reducing errors.
- Evidence DAG becomes formal bureaucracy not tied to acceptance claims.
- Runtime tests show prompt injection increases token cost or tool misuse without measurable reliability gains.
- Long-context models or future runtime APIs make some compression/isolation steps obsolete, while evidence/authority gates remain necessary.
