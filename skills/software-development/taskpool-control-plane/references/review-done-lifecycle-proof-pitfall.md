# Review/Done Lifecycle Proof Pitfall

Extracted from `/Users/charles/.hermes/skills/software-development/taskpool-control-plane/SKILL.md` on 2026-07-01T08:24:04.829872+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## Review/done lifecycle proof pitfall

Taskpool `done` is not a direct closure shortcut for ordinary `pending` or `claimed` work. For implementation tasks, close through the governed lifecycle path and provide evidence in the accepted shapes:

1. Move `pending -> claimed -> running -> review` before `done` unless the command explicitly allows another audited route.
2. Evidence refs should use accepted prefixes such as `command:`, `artifact:`, `proof:`, `url:`, `file:`, or `brainctl:`. Bare prose like “tests passed” is not enough.
3. For `review -> done`, advisory-only/model-consensus evidence is insufficient. Include deterministic implementation evidence such as a real test/build command, selfcheck/proof result, and the artifact path or commit reference that contains the change.
4. If a batched transition times out mid-loop, do not rerun the whole batch blindly. First list/read the target task statuses, resume only the unfinished task(s), then rerun selfcheck.

Anti-condition: do not force-close merely to make the dashboard clean; if evidence shape is rejected, fix the proof bundle or leave the task in `review`.
