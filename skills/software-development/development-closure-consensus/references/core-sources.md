# Core Sources for Development Closure Consensus

This reference maps the public development closure consensus to stable engineering sources. It is not a bibliography dump; each source is included because it supports a reusable closure rule.

## Foundational sources

1. **The Pragmatic Programmer** — Andrew Hunt, David Thomas, 1999 / 2019
   - Supports: end-to-end responsibility, automation, feedback, knowledge capture.
   - Closure rule: manually proven repeated work should become a reusable asset.

2. **Software Requirements** — Karl Wiegers, Joy Beatty, 1999 / 2013
   - Supports: intake quality, acceptance criteria, requirements clarification, change control.
   - Closure rule: closure starts at task handoff, before coding.

3. **Test-Driven Development: By Example** — Kent Beck, 2002
   - Supports: short feedback loops, verification-before-claiming, refactor discipline.
   - Closure rule: no evidence, no done.

4. **Continuous Integration** — Paul M. Duvall, Steve Matyas, Andrew Glover, 2007
   - Supports: shared baseline health, frequent integration, rapid failure visibility.
   - Closure rule: local success is not shared integration success.

5. **Continuous Delivery** — Jez Humble, David Farley, 2010
   - Supports: build/test/deploy automation, deployability, rollback readiness.
   - Closure rule: delivery closeout must include verifiable release readiness, not just commit.

6. **The Checklist Manifesto** — Atul Gawande, 2009
   - Supports: reliable execution in complex/high-risk work.
   - Closure rule: critical gates must be checklist-backed, not memory-backed.

## Modern governance sources

7. **Accelerate** — Nicole Forsgren, Jez Humble, Gene Kim, 2018
   - Supports: evidence-based delivery performance metrics.
   - Closure rule: closure quality should consider flow, failure, recovery, and learning.

8. **DORA / Google Cloud DevOps Research**
   - Supports: lead time, deployment frequency, change failure rate, MTTR.
   - Closure rule: use consistent metrics to compare closure health across projects.

9. **Site Reliability Engineering** — Google SRE Book, 2016
   - Supports: SLO/SLI, error budgets, production reliability, postmortems.
   - Closure rule: high-risk delivery is not closed until operational risk is considered.

10. **The DevOps Handbook** — Gene Kim, Jez Humble, Patrick Debois, John Willis, 2016
    - Supports: flow, feedback, continual learning across dev/test/ops.
    - Closure rule: close the work, close the feedback, close the learning loop.

11. **Trunk-Based Development** — trunkbaseddevelopment.com and related practice literature
    - Supports: small batches, short-lived branches, reduced integration drift.
    - Closure rule: prefer small verified increments and avoid long-lived divergence.

12. **Architecture Decision Records (ADR)** — Michael Nygard pattern and community templates
    - Supports: context/decision/consequences traceability.
    - Closure rule: non-trivial technical choices need rationale, not just code.

## Principle map

| Consensus area | Primary sources |
| --- | --- |
| Intake and completion definition | Software Requirements, Pragmatic Programmer |
| Verification and feedback | TDD, CI, Checklist Manifesto |
| Shared integration | CI, Trunk-Based Development |
| Delivery readiness | Continuous Delivery, SRE |
| Operational reliability | SRE, DevOps Handbook |
| Metrics and improvement | Accelerate, DORA, DevOps Handbook |
| Decision traceability | ADR, Pragmatic Programmer |
| Assetization | Pragmatic Programmer, Checklist Manifesto, DevOps Handbook |
