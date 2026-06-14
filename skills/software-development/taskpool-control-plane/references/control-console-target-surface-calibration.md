# Control console target-surface calibration

Scope: Hermes control-plane/dashboard/console work where the user names a console-like surface and more than one local repository can plausibly satisfy the request.

Applicability: apply before editing files, running UI/build verification, or committing dashboard/control-console changes.

Anti-condition: do not use this reference to force a specific repository when the user explicitly names a different path or when the task is ordinary Hermes Agent core maintenance unrelated to a console/dashboard surface.

## Lesson

A request for "Hermes console", "Control Tower", "dashboard", or "控制台" can refer to different codebases. Do not silently default to the built-in Hermes Agent dashboard. A valid build/test/commit in the wrong repository creates false closure.

## Calibration rule

Before making changes, identify the target surface from evidence:

1. Enumerate plausible repositories/surfaces.
2. Check each candidate's git status and project identity files.
3. If the user says "desktop folder", "folder 里的项目", or "console project", prefer the standalone console app under the user's Desktop/folder workspace over the Hermes Agent internal dashboard unless explicit evidence says otherwise.
4. If choosing wrong would cause edits or commits, ask a one-line target confirmation.
5. If a wrong-target edit already happened, stop advancing that repository, summarize it as wrong-target work, then switch to the calibrated target and inspect its dirty files before editing.

## Control-console product copy pattern

When a control console/dashboard surfaces projection health, runtime selector, worker gates, Human Inbox execution-flow gates, or taskpool drift:

- Treat it as an operator safety state, not a hero diagnostic panel.
- First-screen copy should answer: `Can I act? Why protected? What is the next safe step?`
- Use Chinese product/action language for the main surface: e.g. `数据投影需复核`, `写入已保护`, `只读`, `刷新快照`, `查看技术详情`.
- Do not expose internal labels as primary copy: `PROJECTION TRUST`, `Status/Drift/Runtime/Mode/Next`, `refresh_snapshot_and_inspect_drift`, `execution_flow_task_missing_from_list`, long task IDs, or raw capability IDs.
- Keep raw status, selector mode, blocked capabilities, mismatch IDs, and snake_case reasons in a collapsed technical details area, preserving auditability without dominating the page.
- Prefer a compact strip or an Operator Overview row over a large standalone banner. If the safety state is normal, collapse it to a small chip.
- Verify visually with a browser screenshot/DOM readback: no unwanted English/snake_case in the first screen, no horizontal overflow, Mission/Human Inbox content remains visible.

## Human Inbox / Execution Flow projection rule

When the Human Inbox shows `暂停` cards from `Execution Flow Gate`, do not assume every card is active work. First inspect generated `approvalRequests` and classify rows by lifecycle status:

- Terminal rows (`done`, `archived`, `cancelled`, `completed`) are projection noise and must not appear as actionable Human Inbox cards.
- `execution_flow:external_side_effect` is a real authority/side-effect gate; keep it paused unless the user explicitly authorizes the boundary.
- `execution_flow:evidence` is a repair path; surface the exact missing evidence instead of showing it as a generic pause.

See `references/human-inbox-execution-flow-gate-triage.md` for the triage and regression pattern.

## Human Inbox / execution-flow projection pitfalls

When a control console projects `execution-flow-dry-run` rows into Human Inbox:

- Treat terminal rows as history, not pending human work. `status` or `workflow_stage` in `done`, `archived`, `cancelled`, or `completed` must not create Human Inbox approval cards and must not count as projection drift against the active taskpool list.
- `done + external_side_effect` means audit/history unless separate evidence proves a false-positive; do not show it as `完成 · ... · 暂停`.
- Add regression coverage at the snapshot-generator level: terminal execution-flow rows should produce no `approvalRequests` and no `taskIdMismatches`.
- Browser/DOM readback should explicitly check that first-screen Human Inbox has no `完成 · ... · 暂停`, no `workflow_stage=done`, and no raw internal snake_case outside collapsed details.

## Verification pattern

Before claiming completion, state the exact repository path verified and ensure test/build/browser evidence came from that repository, not from a similarly named Hermes component.