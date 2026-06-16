# Pre-merge Iceberg Scan

Use when a user asks to merge/auto-merge a PR and then requests a broader check such as “同批次 commit 是否有其他问题”, “冰山扫描”, or “find hidden issues”.

## Procedure

1. Pause merge actions until the scan finishes.
2. Define the same-batch scope explicitly:
   - the open PR head commit(s),
   - the base branch commits the PR depends on,
   - adjacent same-day/latest commits that touch the same runtime surface,
   - any screenshot/runtime symptom that triggered the scan.
3. Split the scan by risk surface, preferably in parallel workers:
   - feature/runtime change surface,
   - adjacent commits outside the PR,
   - static/config/deploy/public-route search.
4. For each finding, require evidence:
   - file/line or command output,
   - concrete user scenario,
   - severity,
   - whether it belongs in the current PR or a follow-up.
5. Fix only findings inside the current PR’s scope. Do not silently bundle unrelated flow/business bugs into a focused PR.
6. For in-scope fixes, add regression tests first when practical, then verify targeted tests and build.
7. Amend/update the PR, refresh its body with the scan result and verification, then merge only after read-back confirms the PR is clean.

## Pitfalls

- Static pre-auth fixes can still hit authenticated APIs through telemetry/event reporting. Scan both the main request and any secondary reporting calls.
- Do not duplicate route/public-auth allowlists. Reuse the project’s canonical public-route predicate when one exists.
- Deployment config drift matters for runtime manifests: if a template has `/version.json`, scan other nginx/static-server configs for the same route.
- If an adjacent commit has a real bug outside the current PR scope, report it as a separate follow-up rather than contaminating the current PR.
