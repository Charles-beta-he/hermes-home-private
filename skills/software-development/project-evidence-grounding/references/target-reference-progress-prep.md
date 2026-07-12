# Target + Reference + Progress Prep Pattern

Applicability: use when the user says they are preparing to develop a target implementation while aligning business logic to a sibling/reference implementation and delivery progress to an existing task ledger/profile.

Anti-conditions:
- Do not treat the reference repo as the edit target unless the user explicitly switches targets.
- Do not persist task progress or one-off status as memory.
- Do not call a superseded inventory the current plan; identify the active ledger first.
- Do not claim UI/business parity from static mapping or build success alone.

## Procedure

1. Establish the three-source model before coding:
   - target implementation repo: exact path, branch, last commit, dirty state;
   - reference implementation repo: exact path, branch, last commit, dirty state, and known untracked files to avoid touching;
   - progress source: canonical task inventory/ledger, including superseded files and current task count/priority split.
2. Inspect target architecture, not just filenames:
   - routes and layout/nav entrypoints;
   - pages/components grouped by business domain;
   - API wrappers, service layer, state stores, WebSocket layer, i18n/theme/PWA surfaces;
   - build/package scripts and lockfile/package manager.
3. Inspect reference anchors at the class level:
   - API/URL constants and environment domain rules;
   - network wrapper behavior: signature, common headers, auth, business `meta` error handling, retry/cookie/cert policies;
   - domain directories that correspond to target pages.
4. Map every progress item to landing surfaces:
   - target page/route/service/API/store files;
   - reference Android/native domain files or constants;
   - evidence needed to close: build/test, browser/screenshot, API readback, device/PWA proof, or design diff.
5. Create a preparation artifact under the project SSOT/tasks area instead of bloating memory. Include:
   - evidence snapshot;
   - architecture map;
   - reference anchors;
   - active task mapping;
   - recommended batches;
   - red lines and verification gates.
6. Update the project profile only with durable navigation facts and policy boundaries: repo paths, reference repo, code-navigation map, stack, branch at time of profiling, and development policy. Keep implementation progress in the SSOT artifact.
7. Verify the prep work:
   - target build or smallest available smoke;
   - profile JSON parse/readback;
   - preparation artifact readback;
   - target repo dirty state after build.

## Reporting format

Keep the final concise:
- artifact paths created/updated;
- fresh verification commands and outputs;
- target/reference/progress truth sources;
- first safe implementation batch.

## Pitfalls

- Reference-as-target drift: copying or editing the Android/reference repo when the user asked to develop the React/H5 target.
- Ledger drift: using an older broad inventory after a corrected narrower task list exists.
- Build-as-completion trap: a successful target build proves current compile health, not task completion or UI parity.
- Profile pollution: putting session-local completion status, task order, or transient warnings into the profile/memory instead of a scoped prep artifact.
