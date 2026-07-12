# Evidence-relation normalization and certification status separation

## Applicability

Use when a certification state accepts evidence in more than one schema, especially explicit `supports` / `contradicts` arrays and shorthand `claim_id + status` fields.

Anti-conditions:

- Do not infer relationships from prose, filenames, model agreement, or similar-looking IDs.
- Do not treat Provider runtime quorum as full discussion/ratification certification.
- Do not persist a transient provider failure as a permanent model ban.

## Canonicalization boundary

Normalize evidence before claim grounding:

```text
claim_id=C-001, status=supports
  -> supports=[C-001]

claim_id=C-002, status=contradicts
  -> contradicts=[C-002]
```

Preserve existing explicit arrays and deduplicate normalized IDs. Accept only recognized relation values; unknown statuses remain unlinked and fail closed. Do not fuzzy-match `C1`, `C-1`, and `C-001` unless the state builder owns and records that normalization.

For command evidence, apply the failed-command rule after relationship normalization: a non-zero command may remain contradictory evidence, but its `supports` links must be cleared. This ordering prevents shorthand support links from bypassing the command truth gate.

## RED/GREEN regression matrix

1. Shorthand `claim_id + status=supports` becomes `verified_by_evidence`.
2. Shorthand `claim_id + status=contradicts` becomes `contradicted_by_evidence` and blocks high-severity truth certification.
3. Legacy explicit arrays remain compatible.
4. Unknown or unmatched claim IDs remain unsupported/unlinked.
5. A failed command cannot support a claim after normalization.
6. A failed command may still contradict a claim.
7. Read back the generated evidence bundle; CLI exit zero alone does not prove truth grounding.

## Keep three statuses separate

Report independently:

1. `provider_runtime`: actual calls, successful calls, runtime min quorum, and fresh plan artifacts.
2. `truth_grounding`: claim coverage, contradictions, and `can_certify_truth`.
3. `discussion_certification`: expected participants, approvals, ratification quorum, agreement threshold, unresolved high-severity issues, and final manifest verdict.

A run can correctly be:

```text
provider_runtime=verified
truth_grounding=grounded
discussion_certification=degraded_not_certified
```

Plan-file count is not success count: failed participant artifacts may still exist. Use manifest call/result fields and participant approvals rather than file existence alone.

## Closure rule

Only claim complete certification when the final manifest explicitly permits it and all required discussion/ratification gates pass. Otherwise report the grounded engineering result and the remaining quorum/human boundary separately.
