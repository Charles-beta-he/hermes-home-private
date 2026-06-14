# Local control-console capability sessions

Use this pattern when a localhost dashboard needs to move from read-only projection to a small set of user-triggered side effects.

## Target model

Do not treat “one-click open” as arbitrary execution. Interpret it as: one click opens a short-lived, audited session for a registered allowlist of capabilities. Each capability still has action-specific validation and readback.

Good wording: “一次性开启短时能力会话” / “one-click short-lived capability session”. Avoid “一次性开放” alone because it can imply permanent or unrestricted execution.

## Safe shape

1. Default modes stay read-only:
   - `snapshot` / static dev output must not expose tokens.
   - A stale local session file must not make public snapshots armed unless the desktop/API runtime is actually present.
2. Keep a server-side capability registry:
   - e.g. `snapshot.refresh`, `mission.decide`.
   - Unknown actions are ignored/rejected.
3. Arm via a dedicated endpoint:
   - exact confirmation phrase;
   - short TTL with max cap;
   - writes a local session ledger containing action names and expiry only;
   - no token, confirmation phrase, or secret in the session file.
4. Auth should avoid token-in-public-snapshot:
   - prefer a same-origin HttpOnly cookie set by a health/bootstrap endpoint;
   - keep header-token support only for scripted probes if needed;
   - require JSON content type plus Host/Origin allowlists.
5. Every side-effect endpoint must check both auth and `capability_allowed(action)`.
   - Do not let “safe” local-file writes such as snapshot refresh bypass the capability session once they are listed as capabilities.
6. Keep action-specific validation server-side, not only in UI:
   - for mission decisions, read the mission store read-only and require decision exists, status is open, options are explicit/non-empty, and answer exactly matches one option.
7. Read back immediately after a successful write and refresh projections.
8. Audit both accepted and rejected writes with action, code, actor, and compact previews only.

## Verification checklist

- Default snapshot: no token, `controlActionsAllowed=false`, `missionDecisionsAllowed=false`, session unarmed.
- Desktop probe:
  - health sets HttpOnly cookie;
  - pre-arm side-effect returns `capability_not_armed`;
  - bad confirmation fails;
  - arm succeeds and snapshot shows only registered capabilities;
  - post-arm side-effect succeeds;
  - text/plain/simple POST still fails.
- Mission-backed E2E for `mission.decide` when a real mission direction exists and the user authorizes full validation:
  1. Create a minimal real `hermes mission handoff` on the existing mission, with one recommended option and safe alternatives.
  2. Verify the public snapshot shows the open decision but still has no token and no armed capability.
  3. Through the localhost console API, prove `mission.decide` fails before arm, arm the short-lived session, prove an invalid answer is rejected by server-side option validation, then submit the exact valid option.
  4. Read back `hermes mission status` / snapshot: open decisions are zero and the mission resumed to active.
  5. Append a `hermes mission stage-report` containing command evidence and explicitly noting that the test wrote mission-ledger events but did not trigger external platforms, remote pushes, production deploys, or other broad side effects.
  6. Remove the session file and regenerate a default snapshot; assert it is unarmed/no-token/no-open-decisions before committing any generated snapshot.
- API tests cover cookie auth, TTL expiry, unarmed rejection, shell=False argv execution, answer-option validation, and no token/confirm phrase persistence.
- Browser harness must stay clean in preview mode; if the API is absent in preview, avoid health fetch noise outside the desktop port.

## Common pitfalls

- Public JSON snapshots are tempting bootstrap channels; do not put session tokens there.
- UI option buttons are not sufficient validation. Re-check exact allowed choices at the server boundary.
- If an action is listed in the registry, direct calls to that action must require an armed session too.
- “One-click open” should describe opening the registered/TTL-scoped set, not unlimited executor authority.
