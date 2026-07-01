# Self-managed GitLab smart-routed review receipt pattern

Applicability:
- A self-managed GitLab MR/auto-merge flow is gated by multi-model or smart-routed review.
- The diff touches auth/login/QR, funds/trading/assets, Android/mobile parity, backend-configured routing, or several runtime files.
- Provider/model health may be partial, but deterministic evidence can still support a scoped product-code decision.

Anti-conditions:
- Do not use this to claim full multi-model certification when the router says `degraded_not_certified`.
- Do not merge if any reviewer reports a concrete reproducible security/correctness blocker.
- Do not treat implementer self-report as review evidence; bind the final merge to a reviewed SHA.

Procedure:
1. Inspect the governing workflow/skill first for required review surfaces. For UAEC-H5 analyzed Lark work, `lark-task-reading/references/uaec-h5-analyzed-batch-continuation.md` requires `security/auth`, `logic/parity`, and `ui/compat` review for high-risk surfaces.
2. Build the review packet with:
   - reviewed commit SHA;
   - scoped diff against the target branch;
   - reference evidence, e.g. Android endpoint/flow lines for parity claims;
   - deterministic verification commands and fresh outputs;
   - known boundaries, e.g. no live-camera QR scan in first slice.
3. Run the multi-model/smart-router review. Preserve provider/model status honestly:
   - `approve` / `amend` / `reject` votes;
   - skipped or unhealthy providers;
   - whether the certification manifest says `degraded_not_certified`.
4. If the review is degraded because of provider quorum or evidence-router shape, distinguish two verdicts:
   - `product-code verdict`: whether concrete blockers exist in the diff;
   - `certification verdict`: whether full multi-model certification passed.
5. Capture a receipt before MR/merge. Include:
   - MR/task identifier and reviewed SHA;
   - models attempted/consulted;
   - blocker list and advisory findings;
   - deterministic evidence paths/commands/exit codes;
   - final boundary statement (`advisory_approve_with_degraded_multimodel_certification` when appropriate).
6. Create the MR with the review receipt summarized in the description or a non-blocking comment.
7. Merge by reviewed SHA (`glab mr merge <iid> --sha <reviewed_sha> ...`) so unreviewed commits cannot slip in.
8. Read back MR JSON after merge: `state`, `sha`, `merge_commit_sha`, `merged_at`, `should_remove_source_branch`, and target branch tip. Fetch/prune and verify the source branch was deleted if removal was requested.

Pitfalls:
- GitLab self-managed instances without a running pipeline may merge immediately even when `--auto-merge` is passed. Report the actual readback state rather than saying auto-merge was merely queued.
- `degraded_not_certified` from the multi-model router is not automatically a product-code blocker. It is still a certification boundary that must be stated, and it cannot be upgraded without rerunning the router after provider/evidence issues are fixed.
- Evidence fulfillment runners may reject compound shell commands with pipes/`&&`; if that happens, manually capture compact deterministic evidence and reference it in the receipt rather than weakening the claim.
- Do not hide missing visual review. If Gemini/visual provider is unavailable and UI changed, mark UI review as degraded/advisory unless screenshots/browser evidence exists.

Receipt skeleton:

```md
# <project/task> smart-routed multi-model review receipt

- Reviewed SHA: `<sha>`
- Scope: <files/features>
- Model/router status: <models + votes + degraded/certified>
- Product-code blockers: <none/list>
- Advisory findings: <list>
- Deterministic evidence: <commands + exit codes + artifact paths>
- Certification boundary: <certified | degraded_not_certified + reason>
- Merge guard: merged by reviewed SHA `<sha>` / not merged because <reason>
```
