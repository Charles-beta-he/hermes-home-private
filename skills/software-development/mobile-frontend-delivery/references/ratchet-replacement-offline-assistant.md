# Ratchet Replacement for Mobile/Offline Assistant Delivery

Use this reference when a mobile/offline assistant or agent companion is being matured from idea/prototype into production without a big-bang rewrite.

## Core idea

Use ratchet replacement: every new capability enters as a reversible, evidence-gated slice before becoming the default. Do not let a prototype silently become production, and do not replace the whole system in one step.

## Conceptual sources

- Michael Tomasello, *The Cultural Origins of Human Cognition*: ratchet effect in cumulative culture — improvements are retained and built upon.
- Joseph Henrich, *The Secret of Our Success*: reliable accumulation requires high-fidelity transmission, selection, and institutions.
- Donald Campbell, “Blind variation and selective retention”: variation → selection → retention as a general learning mechanism.
- Nelson & Winter, *An Evolutionary Theory of Economic Change*: organizational routines evolve through selection and retention.
- Lindblom, “The Science of Muddling Through”: complex systems benefit from small reversible increments.
- Martin Fowler, Strangler Fig Application: grow the new path around the old, route gradually, retire old paths last.
- Michael Feathers, *Working Effectively with Legacy Code*: add seams and tests before replacement.
- Humble & Farley, *Continuous Delivery* and Forsgren/Humble/Kim, *Accelerate*: small batches, automated verification, recovery metrics.
- Skelton & Pais, *Team Topologies*: production replacement also requires ownership and cognitive-load boundaries.

## Ratchet unit contract

Each unit should have:

- `contract`: input/output/permission/failure states;
- `evidence`: tests, browser proof, curl/API readback, logs, screenshots;
- `rollback`: flag, old path, or fallback;
- `ownership`: source of truth and write boundary;
- `promotion_gate`: what moves it from draft → validated → promoted;
- `demotion_gate`: privacy leak, hallucination, duplicate side effect, false UI state, or status split.

## Typical units for offline assistant delivery

1. Shared offline evidence core.
2. Pocket/mobile gateway dry-run.
3. ContextCard/EvidenceSpan exporter.
4. Basic PWA/mobile app shell.
5. IndexedDB/WebCrypto or native secure persistence.
6. Vertical adapter such as Travel TripState/OCR.
7. Gateway reconciliation and readback.
8. Native shell only when permissions/signing/device needs justify it.
9. Enterprise release/telemetry/security.

## Promotion ladder

- `contract-ready`: docs/contracts/fixtures exist.
- `validated`: at least one real test/browser/API proof passes.
- `promoted`: two independent scenarios pass and no red line is violated.
- `demoted`: any red-line violation or false state is found.

## Common pitfalls

- Treating a shared core or gateway contract as an app. A user-facing offline assistant needs an actual shell with composer, state, source panel, and browser/mobile proof.
- Claiming Hybrid/online handoff before the runtime performs HTTP submission and readback.
- Letting the mobile client become a second fact source. It should be a projection/cache unless explicitly designed otherwise.
- Storing progress only in chat. Maintain a project progress ledger and profile pointer.
