# Retry storm / recursive review-gap repair pitfall

Use this when taskpool shows many `retry` tasks with nested `补证闭环` titles or `blocked resolver: transient multimodel status gate=UNKNOWN`.

Do not keep draining blindly. Diagnose the proof-recognition path first:

1. Count statuses and inspect retry frontmatter: `retry_count`, `next_attempt_at`, `review_gap_parent`, `review_gap_type`, `blocked_resolve_reason`, `multimodel_status`, and `ratification_artifact`/`evidence_refs`.
2. Check whether PASS evidence exists in historical evidence refs rather than canonical ratification fields. Legacy advisory packets may use `schema: advisory_multimodel_ratification_v1`, `certification: PASS`, `loop_status: LOOP_DONE`, `parent_task`/`repair_child_task`, `all_sha256_verified: true`, `no_red_line_violations: true`, and deterministic `selfcheck`/`proof_check: PASS`.
3. If PASS packets are real and target-bound, make the reader compatible instead of creating more repair children: scan local JSON `evidence_refs`/`evidence` read-only, accept only task-bound or parent-bound repair evidence, and preserve lifecycle gate fail-closed semantics.
4. Prevent recursive repair chains: review-gap scan should not create a repair child for a task that already has `review_gap_parent`; repair children are the bounded remediation surface.
5. Add/verify a transient retry cap for blocked resolver. After repeated `gate=UNKNOWN`/`round=unknown` retries, keep the task blocked with an explicit intervention reason instead of `resolved_to_retry` churn.
6. Verification loop: run `selfcheck`, `blocked-resolve-step`, `auto-close-review`, status counts, and process list. A healthy stopped state may still have `blocked`/`review` tasks if remaining failures are real proof/certification/UI/API-readback hard gates.

Classification: reusable taskpool control-plane procedure; not user memory and not session progress.
