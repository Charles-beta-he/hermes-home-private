# External capability absorption proof loop

Use when a user asks to absorb/learn from an external repo, demo, video, or open-source project and also says to add it to the taskpool or “全盘推进”.

## Landing-zone split

Classify mixed findings before durable writes:

- Reusable workflow/proof pattern -> patch the relevant skill.
- Project-specific source URL, branch, commit, task id, or local path -> taskpool item or scoped project/reference file, not global memory.
- Concrete future implementation work -> taskpool candidate/proposal, not a fake skill.
- Session progress -> proof log only, not memory.

## Bounded execution pattern

1. Create a taskpool capability-absorption task with the external source URL, capability claim, target surface, acceptance criteria, red lines, required artifacts, and evidence refs.
2. Do not treat task creation as implementation proof. Immediately perform the next bounded landing slice if tools and permission allow.
3. Preserve governance boundaries while matching interaction feel. For example, visible/HUD/diagnostic experience can land first; always-on microphones, wake words, destructive tools, or external side effects stay default-off and gated.
4. Record proof back into the task file: exact commands, pass counts, files changed, and commit hashes.
5. Commit only scoped project changes; do not mix unrelated working-tree noise.

## Verification checklist

- Taskpool item exists and includes source, claim, red lines, acceptance evidence, and required artifacts.
- Implementation evidence is real: tests/type-checks/smoke output, not model-only certification.
- `/status`/doctor/diagnostic surfaces show the readiness or blockers when the feature is operationally relevant.
- Unsafe 1:1 behaviors are explicitly anti-conditioned: default-off, explicit permission, stop control, and audit/readback before production use.
- Final report names residual gated work separately from completed, verified work.
