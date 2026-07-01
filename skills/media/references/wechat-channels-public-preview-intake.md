# WeChat Channels public-preview video intake

Scope: global media-analysis procedure for public `weixin.qq.com/sph/...` links. Applicability: use only for public-preview analysis, external artifact verification, and read-only intake proposals. Anti-conditions: do not use this as authorization to bypass QR/App gates, install packages, copy external code, or mutate unrelated project/runtime state.

## Procedure

1. Open the public preview page and extract only visible facts:
   - canonical preview URL / share id
   - author/account
   - date/location when visible
   - caption text
   - visible cover-frame text if accessible
   - QR/App gate boundary
2. Do not claim full playback if the browser only exposes the preview or QR-gated page.
3. Verify any named external project through first-party sources:
   - GitHub API for repo metadata: stars/forks/issues/license/language/created/pushed
   - npm/registry metadata when package names appear
   - official homepage/docs/catalog JSON when linked or discoverable
4. Separate video claims from verified artifact facts. Star counts in videos may be stale or promotional.
- If creating a follow-up intake task, include:
   - source link and visible preview facts
   - external artifact verification
   - red lines: no QR bypass, no installing external packages/skills, no copying external code/hooks into the live agent environment
   - overlap review against existing tasks/skills
   - recommendation matrix for adopt / adapt / reject / later
- If the preview names only a project label and search cannot identify an authoritative repo/site/package, create the task as **source identification + overlap review**, not adoption. Negative search evidence is valid intake evidence; keep marketing claims such as line counts, scare framing, star counts, or “big-company reaction” as verification requirements, not facts.

## Pitfalls

- `weixin.qq.com/sph/...` pages often expose preview metadata but not complete video playback. Treat the QR/App gate as a hard boundary.
- Video captions may refer to an ecosystem-wide star count rather than the named repository. Verify the specific repo before reporting.
- Public media intake is not implementation authorization. If a repo advertises MCP/A2A/hooks/skills, first land it as read-only evidence and a bounded recertification task.
- For multiple related media links, consolidate into one class-level intake task when the work is a comparative absorption/review, instead of creating one narrow task per video.

## Good report shape

- "Visible from public preview" — facts from page.
- "Externally verified" — repo/package/docs facts with current counts.
- "Claims not verified" — video claims that remain promotional or app-gated.
- "Taskpool placement" — task id/path, status, acceptance criteria, red lines.
