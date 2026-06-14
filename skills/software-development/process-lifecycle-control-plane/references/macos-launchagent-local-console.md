# macOS LaunchAgent for local control consoles

Use this when a localhost dashboard/control console should follow a resident Hermes installation instead of requiring a foreground `pnpm desktop` or terminal session.

## Safe resident shape

1. Treat the LaunchAgent as the process supervisor, not as an authorization boundary.
   - `RunAtLoad=true` and `KeepAlive=true` are appropriate for a local dashboard.
   - Write status/log helpers so the operator does not infer health from ports alone.
2. Keep secrets out of the plist.
   - Do not persist session/action tokens in `EnvironmentVariables`.
   - Generate per-process tokens inside the runner if needed.
   - Persist only non-secret environment such as `HERMES_HOME` and `PATH`.
3. Use explicit localhost ports and strict binding in the runner.
   - UI: fixed localhost port, strict port mode.
   - API: `127.0.0.1` only.
4. Provide package scripts or CLI commands for:
   - install/start/bootstrap
   - status
   - stop/bootout
   - uninstall when appropriate
5. Logs should land under the Hermes log directory, e.g. `~/.hermes/logs/<service>.launchd.log` and `.err.log`.
6. Verification must include real readback:
   - `launchctl list | grep <label>` or a status helper.
   - HTTP probe for the UI port.
   - HTTP probe for API health.
   - Snapshot safety check: no token, default unarmed.
   - Full project verify/browser harness after the service is running.

## Contract test targets

Add tests before implementation for:

- plist label, `RunAtLoad`, `KeepAlive`, `WorkingDirectory`, `ProgramArguments`;
- log paths;
- `HERMES_HOME` / `PATH` presence;
- absence of secret-like env keys such as `HERMES_CONTROL_CONSOLE_TOKEN`;
- launchctl status parser: running, loaded-not-running, not-loaded.

## Common pitfalls

- A leftover Vite/Node process may make it look like the console is resident; check launchd separately.
- `launchctl bootstrap` may succeed while the child immediately restarts; status should show the pid and logs should be checked.
- Browser preview harnesses can run on a different port than resident desktop mode. Avoid health-fetch noise outside the desktop port.
- Long ledger/stage-report text can create mobile horizontal overflow after snapshot changes; rerun the browser harness after real ledger events, not only against a clean fixture.
