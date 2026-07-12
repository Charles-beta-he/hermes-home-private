# Research paper → product contract landing

Use when a user asks to absorb an academic paper, arXiv link, technical claim, or named concept into an existing project/product/workflow rather than merely summarize it.

## Core rule

Do not jump from paper language to product claims. Split the result into:

1. source facts verified from the paper;
2. direct-support claims;
3. non-support / boundary claims;
4. transferable architecture patterns;
5. scoped project landing artifacts;
6. optional local reversible implementation slice with tests.

## Procedure

### 1. Verify source and version

- Resolve the exact paper/version: arXiv id, title, authors, categories, published/updated dates, PDF/HTML availability.
- Prefer the versioned URL actually read, e.g. `https://arxiv.org/pdf/<id>vN`.
- Extract enough full text to inspect abstract, methods, results, and conclusion.
- Record whether the paper is peer-reviewed, preprint-only, withdrawn, or source/code-backed when relevant.

### 2. Run direct-claim checks

For any proposed project concept, keyword, or technology name:

- Search exact name and aliases in the paper text.
- Search component terms separately.
- Record counts or explicit absence for direct provenance claims.
- Separate `supports` from `does_not_support`.

Example shape:

```text
supports:
- looped latent world-model pattern
- adaptive computation / early exit

does_not_support:
- direct provenance for <project concept>
- egocentric/wearable/runtime proof
- neuroscience/brain mechanism proof
```

### 3. Convert to transferable patterns

Extract architecture patterns, not marketing claims. A good pattern has:

- problem addressed;
- mechanism;
- target system analogue;
- acceptance boundary;
- anti-conditions;
- falsifier.

Avoid copying performance claims such as `100x efficiency` into product truth unless the experiment is reproducible and relevant to the target.

### 4. Land scoped artifacts

For an existing project, write or update scoped artifacts rather than global memory:

- research absorption note under the project evidence/research folder;
- architecture contract or design note under the project architecture/spec folder;
- evidence index entry with `supports` and `does_not_support`;
- progress ledger update with side-effect boundaries;
- task candidate for future implementation if work remains.

If no project SSOT exists, create a concise local note only after confirming the project boundary; do not invent global runtime behavior.

### 5. Optional safe implementation slice

If the user says to proceed to a productized artifact and the next slice is local/reversible, implement a deterministic contract scaffold before real model/device/runtime integration:

- define a receipt/schema;
- add a local helper or validator;
- cover positive and negative cases;
- prove all high-side-effect flags remain false;
- run the project’s focused test suite;
- write a verification report.

Do not claim real model quality, wearable readiness, medical/safety fitness, external dispatch, or hardware capability from a deterministic scaffold.

## Closure checklist

- [ ] Exact paper/version readback is recorded.
- [ ] Direct-support and non-support claims are separated.
- [ ] Transferable patterns are entity-stripped and scoped.
- [ ] Project landing artifacts cite evidence and boundaries.
- [ ] Implementation claims, if any, are backed by tests/readback.
- [ ] Remaining gates are concrete: real model, adapter, external side effect, device/hardware, production deploy, human acceptance, or missing evidence.

## Pitfalls

1. Treating paper terminology as proof of a product concept with a similar name.
2. Saving a one-off paper summary to global memory instead of a scoped evidence note.
3. Promoting a preprint’s performance claim into product copy without reproduction.
4. Letting speculative latent/model outputs become source-of-truth state.
5. Calling a contract scaffold a real model or runtime capability.
