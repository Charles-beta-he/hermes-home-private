# Certification Readiness Packet Pattern

Applicability: use when a Context Engineering OS slice has local code/test/API/UI evidence and the user asks to advance toward `certified`, but an independent verifier vote or full UI acceptance gate is still pending.

Anti-conditions: do not use this pattern to claim `certified` from implementer self-report, old test output, a handoff summary, or model-only agreement without objective evidence. Do not use it for unrelated project progress logs; session progress belongs in SSOT/task evidence, not skills.

## Pattern

1. Separate readiness from certification.
   - `certification-ready evidence package` means objective evidence has been collected and mapped.
   - `certified` requires the required independent verifier vote(s), route-required evidence, and any UI acceptance gate explicitly in scope.
   - If verifier work is asynchronous, record `pending verifier vote` instead of waiting silently or claiming completion.

2. Build a claim matrix before the final verdict.
   - One row per material claim.
   - Columns: claim, evidence, status.
   - Mark negative requirements explicitly, e.g. `no runtime prompt injection`, `no writes`, `no LLM`, `no external dispatch`.
   - Negative claims need negative evidence such as API readback flags, tests, or console/process readback.

3. Include fresh same-slice evidence.
   - Code commits or exact diff scope.
   - Tests/typecheck/build/compile outputs from the current slice.
   - API readbacks for default-disabled and enabled-valid states when the feature has a config gate.
   - Browser render/interaction/console readback for dashboard/UI surfaces.
   - Static security scan for added code when introducing UI/API surfaces.
   - Process cleanup readback if temporary dashboards/servers were started.

4. State out-of-scope closed boundaries.
   - Runtime prompt injection.
   - Agent loop mutation.
   - Taskpool lifecycle writes.
   - Scheduler/cron/watchdog.
   - External dispatch.
   - Publish/deploy/push.
   - Destructive operations.
   - Credential/payment entry.

5. Record allowed vs forbidden wording.
   - Allowed before verifier returns: `certification-ready evidence package`, `locally verified and committed`, `full certification pending independent verifier vote`.
   - Forbidden before verifier returns: `certified`, `fully certified`, `A+ UI certified`.

6. Land the packet in the project SSOT.
   - Use a numbered certification/readiness document under the project workflow directory.
   - Link it from the roadmap/converge matrix.
   - Commit SSOT separately from source-code changes.

## Checklist

- [ ] Every material acceptance claim has fresh objective evidence.
- [ ] Every negative requirement has negative readback evidence.
- [ ] Implementer self-report is not counted as verifier evidence.
- [ ] Async verifier status is represented as pending/amend/reject/approve, not hidden.
- [ ] UI claims distinguish targeted browser readback from full uIMax/A+ acceptance.
- [ ] The final wording does not overclaim beyond the verifier gate.
