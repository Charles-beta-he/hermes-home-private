# External search adapters in governed execution graphs

- **Scope:** class-level architecture pattern for adding broad-web, documentation, social, repository, or page-fetch providers to agent execution graphs.
- **Applicability:** research/coding graphs that need current external evidence and can authorize bounded external reads.
- **Anti-conditions:** simple direct lookups, secret/private sources, unbounded fan-out, or workflows where external reads are prohibited.
- **Falsifier:** narrow this pattern if provider diversity, source-reality gates, or bounded parallelism do not improve claim accuracy or closure cost in repeated evaluations.

## Core rule

A search provider is an **external-read adapter node**, not the researcher, reducer, verifier, or truth authority.

```text
objective
  -> query planner
  -> fake-edge/dependency check
  -> provider router
       -> broad-web adapter
       -> official-doc adapter
       -> repository/release adapter
       -> social/current-discussion adapter
  -> deterministic normalizer/reducer
  -> source-reality + citation-support gate
  -> local-context correlation
  -> fresh verifier
  -> evidence packet
```

## Adapter contract

```yaml
id: external_search_adapter
consumes: [bounded_query, source_scope, date_scope, result_limit]
produces: [normalized_results, source_urls, provider_metadata, typed_errors]
side_effects: external_read_and_possible_metered_cost
budget: [query_count, result_limit, retries, output_bytes, total_cost]
gates: [auth_ready, network_allowed, source_reality, citation_coverage, budget]
cannot_prove: [source_truth, exhaustive recall, provider_superiority]
```

## Fake-edge rule

Parallelize only genuinely independent evidence questions. Query reformulations for one question remain inside one node. Shared API quotas, output directories, caches, files, and provider rate limits are hidden dependencies and must be declared before fan-out.

## Provider routing

Route by evidence need rather than marketing hierarchy:

- broad live web: discovery and current coverage;
- curated/versioned docs: package/API precision;
- repository/release/issues: implementation and release facts;
- social search: current discussion and reactions;
- direct page fetch: source text after discovery.

Provider breadth does not substitute for direct-source verification. High-impact claims should use source diversity or an authoritative primary source.

## Governance

1. Keep search, reduction, synthesis, and verification as separate responsibilities.
2. Preserve typed failures; never fabricate results after provider/auth/network errors.
3. Retain URL-level provenance through reduction.
4. Use a fresh verifier to check source reality and claim support.
5. Bound query count, retries, result count, output bytes, and metered cost.
6. Never expose credentials to prompts, logs, receipts, memory, or skills.
7. Search installation/discovery does not grant credential, publish, deploy, lifecycle, or external-write authority.
8. Measure outcome quality, correction rate, source validity, and closure cost—not number of agents or searches.

## Perplexity evidence example

The official `pplx` CLI demonstrates a useful adapter contract: JSON stdout on success, typed JSON stderr on failure, web-search/domain/date scoping, content fetch, saved full output plus bounded preview. Its broad-web role complements rather than universally replaces versioned documentation adapters. Binary provenance/notarization, authentication, API cost, and direct-source verification remain separate gates.

## Verification checklist

- [ ] Every search edge is a real dependency or explicitly parallel independent question.
- [ ] Shared quotas/files/caches are modeled as dependencies.
- [ ] Adapter output is normalized without dropping URLs or typed errors.
- [ ] Material claims pass source-reality and citation-support checks.
- [ ] A fresh verifier, not the search node, closes the claim.
- [ ] Cost/retry/output budgets are enforced.
- [ ] Credential and external-write boundaries remain closed.
