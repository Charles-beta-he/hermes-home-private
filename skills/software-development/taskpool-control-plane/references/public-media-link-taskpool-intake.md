# Public media link to governed task intake

Applicability: Use only for public or user-provided media/link previews when the user explicitly asks to analyze the item and add a follow-up to a governed task pool. The pattern applies to gated preview pages, social posts, short videos, image-set notes, articles, repos mentioned by media, direct GitHub/repository links, or similar external-source intake.

Anti-conditions: Do not use this to store a specific project fact, card ID, branch, private URL, or session progress in the global skill. Do not bypass app/login/paywall gates. Do not claim hidden media was consumed. Do not convert a source mention into an adoption task without independent artifact verification. Do not create a vague “review this repo later” card; even direct repository intake needs authoritative metadata, upstream-doc readback, adaptation hypothesis, non-goals, and expected verification evidence.

## Procedure

1. Resolve the submitted link and record the final URL.
2. Extract only visible/public preview evidence:
   - caption/title/text;
   - author/channel/source name;
   - date;
   - visible engagement counts, preserving ambiguity if fields are unlabeled;
   - whether login/app/QR/paywall blocks complete access.
3. If the preview names a concrete external artifact, verify that artifact directly before treating it as real:
   - repository/package/product/paper/site URL;
   - current metadata from an authoritative endpoint when available;
   - README/docs/core claims from the artifact itself.
   - For direct GitHub intake, normalize `GitHub - owner/repo` or bare repo mentions to `https://github.com/owner/repo`, read GitHub API metadata (`full_name`, description, stars, forks, issues, license, default branch, language, pushed/updated timestamps, archived), then read upstream docs. If `README.md` 404s, list repository contents or try the default branch's actual casing (for example `readme.md`) before assuming docs are absent.
   - For GitHub search discovery with `gh api`, use GET fields: `gh api -X GET /search/repositories -F q='<query>' -F per_page=10`. Do not use `-f` without `-X GET` for search endpoints; it can turn the request into a POST and return misleading 404s. Treat exact-phrase 0 results plus noisy broad-language matches as negative search evidence, not proof the project does not exist.
   - For VS Code / OpenAI / Codex extension claims from social media, verify the Marketplace extension record directly via the Visual Studio Marketplace public gallery API (`extensionquery`) and the extension Details asset before accepting the claim. Capture verified publisher, extension id, display name, version, last updated time, and visible details. If the details asset lacks the claimed feature terms (for example “Record”, “Replay”, or “Skill”), record that as `not yet verified / requires docs-or-command readback`, not as either proof or disproof.
4. Search existing taskpool/project records before creating anything. If the media repeats an already-covered theme or artifact, do **not** create another generic evaluation card. Create a bounded recertification/merge task instead, with evidence refs to the prior tasks and an explicit objective such as “determine net-new signal vs duplicate coverage.”
   - For AI-agent/toolkit/skill-library media, search both the artifact name and ecosystem aliases (for example short names, repo names, package names, and previously used project labels) before adding the card.
   - If a new media item overlaps prior absorption work, make the card an evidence-backed **net-new / recertification / overlap review** with anti-goals against direct installation or wholesale copying.
   - Popularity claims in captions (stars, “ecosystem scale,” model/tool support counts) must become verification requirements, not task conclusions, until checked against GitHub/npm/site/API readbacks.
5. Create the taskpool card as an evidence-backed follow-up, not as a media-only summary:
   - source link and resolved URL;
   - preview-only facts and gate status;
   - verified external artifact facts;
   - prior-task overlap or idempotency rationale;
   - preliminary adaptation or investigation hypothesis;
   - concrete task goals;
   - explicit non-goals and anti-conditions;
   - verification evidence expected from the future worker.
6. Use an idempotency key derived from the source link, verified artifact, or prior-task merge lane so retries do not duplicate the card.
6. Attach relevant class-level skills to the card when the task system supports skill hints, so the future worker inherits media-gate, codebase, research, or control-plane rules.
7. Read back the created card from the task system before reporting success.

## Pitfalls

- A public preview is evidence about visible metadata only; it is not proof that the full media was watched.
- Social-media claims are leads, not verified facts. Convert impressive claims into verification requirements.
- The durable learning is the intake pattern, not the one-off source URL or card ID.
- If the result is concrete engineering work, land it as a taskpool candidate/card; do not create a fake skill that merely says “do this task later.”
- Local-brain `brain_task_orchestrator.py add` may reject cards that omit governance metadata. For evolution/taskpool intake, include `--priority-layer`, `--dependency-order`, `--multimodel-triage-result`, plus architecture alignment fields such as `--anti-drift-check` and `--acceptance-evidence` when using `--lane evolution` / `--architecture-target taskpool`.
- After creating a card, read back the Markdown, not only the JSON create response. If repeated `--accept` values or generated frontmatter/body projections are incomplete, patch the card immediately so the visible Acceptance Criteria match the intended evidence gates.
- `brain_task_orchestrator.py add` can time out after writing the card and triggering follow-on lifecycle/claim hooks. Do **not** blindly retry a timed-out add: first search/read back by title, source URL, idempotency key, or generated path. If the card exists, patch it in place with any missing acceptance criteria/evidence instead of creating a duplicate.
- `brain_task_orchestrator.py add` can also return top-level `status: OK` while `event_hook.status: ERROR` (for example `multimodel_step.reason: allowlist_miss`). Treat this as a mixed result, not a failed add: read back the created Markdown by path/id, patch collapsed acceptance/red-line details if needed, and report the hook gate separately. See `references/active-claim-reconciliation-and-media-intake.md` for the paired active-claim/readback checklist.
- For WeChat Channels `weixin.qq.com/sph/<id>` public previews, use the dedicated API/readback notes in `references/wechat-channels-public-preview-api.md`: resolve fake-IP/TLS routing with `--resolve` when necessary, call `finder-preview/api/feed/get_feed_info` with Origin/Referer context, and preserve the app-gate boundary.

## Card body checklist

```text
Source:
- Original link:
- Resolved URL:
- Access boundary:

Prior coverage / idempotency:
- Existing task/project records searched:
- Duplicate vs net-new judgment:
- If follow-up, prior task refs:

Visible preview evidence:
- Title/caption:
- Author/source:
- Date:
- Counts/metrics:
- Gate status:

Verified external artifact:
- URL:
- Authoritative metadata:
- Docs/README claims:

Preliminary judgment:
- Reusable value:
- Non-goals:
- Risks:

Task goals:
- ...

Verification expected:
- Source/artifact readback:
- Minimal runnable or reproducible proof, if applicable:
- Evaluation document/path:
- Skill/profile update only if a reusable procedure emerges:
```
