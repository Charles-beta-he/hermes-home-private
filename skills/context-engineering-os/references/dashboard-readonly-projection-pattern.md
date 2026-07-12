# Dashboard Read-only Projection Pattern for Context Engineering OS

Applicability: use when a Context Engineering / Context Packet capability has already landed as a deterministic CLI/API preflight and the next safe advancement is a dashboard/control-room readback surface.

Anti-conditions: do not use this pattern to add executor buttons, mutate runtime prompts, change the agent loop, write taskpool lifecycle state, enable cron/scheduler work, dispatch externally, publish/deploy/push, enter credentials, or perform destructive operations. Those require separate exact authority, rollback/readback, and tests.

## Pattern

1. Keep the dashboard as a projection surface.
   - Add a read-only API endpoint that calls the existing deterministic preflight/validator function.
   - Reuse the same default-off gate and output schema as the CLI path.
   - Return explicit side-effect flags such as `external=false`, `llm=false`, `writes=[]`, and `runtime_prompt_injection=false`.

2. Preserve dashboard authentication.
   - Put the endpoint under the existing protected dashboard `/api/` route family unless it is truly public health data.
   - Add an unauthenticated test that proves session-token auth still blocks access.

3. Test before UI wiring.
   - Add API tests for: unauthenticated access, default-disabled readback, enabled valid-packet readback, and enabled missing/invalid packet blocked readback.
   - Add frontend API types/helper only after the backend contract is stable.

4. Add only read-only UI controls.
   - A labeled input for the packet path is acceptable.
   - A `Check preflight` button is acceptable only when it calls the read-only API and does not mutate config or lifecycle state.
   - Display gate/status badges, packet-checked state, result counts, and side-effect flags.
   - Do not add "run", "fix", "dispatch", "approve", "enqueue", or other executor controls in this slice.

5. Verify both code and rendered UI.
   - Run backend/API tests and Python syntax checks for touched backend modules.
   - Run the frontend workspace typecheck/build using the repo-supported workspace command.
   - Start a local dashboard and use browser readback to confirm the panel renders and the button interaction updates status.
   - Read browser console errors before claiming the UI slice is done.

6. Keep commits and evidence split.
   - Commit Hermes code/UI changes in the Hermes source repo.
   - Commit SSOT/evidence notes in the profile/workflow repo.
   - Do not stage package-lock/package-manager churn unless dependency changes were intentional.

## Verification checklist

- [ ] API endpoint is protected by existing dashboard auth.
- [ ] Disabled gate returns `status=disabled` and does not validate/mutate.
- [ ] Enabled valid packet returns `status=ok` and result counts.
- [ ] Enabled missing/invalid packet returns blocked/error readback.
- [ ] UI controls have labels/accessible names and are keyboard-reachable.
- [ ] UI shows side-effect flags and runtime prompt injection remains false.
- [ ] Frontend typecheck/build passes.
- [ ] Browser readback confirms render + interaction and console has zero JS errors.
- [ ] Evidence doc records scope, boundary, commands, outputs, and any remaining gate.

## Pitfalls

- Do not mistake a dashboard readback surface for authority to execute. More context visibility does not grant permission.
- Do not let frontend verification stop at typecheck/build when the user asked for UI delivery; include a browser render/interaction readback and console-error check.
- If a package manager command mutates lockfiles unexpectedly, revert the churn unless dependency changes are part of the authorized slice.
