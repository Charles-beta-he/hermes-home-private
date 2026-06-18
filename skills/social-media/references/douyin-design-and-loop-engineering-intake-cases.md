# Douyin design-module and loop-engineering intake cases

Use this reference when a Douyin/TikTok/Xiaohongshu-style post presents either:

- a reusable UI/design extraction tool or skill; or
- a short engineering-methodology lesson such as Context Engineering / Harness Engineering / Loop Engineering.

The goal is to separate concrete module candidates from vocabulary/checklist-only lessons.

## Case lens A — website style extraction / design-intake tools

Treat these as potential **capability absorption** candidates when the post claims a reusable tool that can run against arbitrary websites and produce durable design artifacts.

Evidence to capture:

1. Resolve short link and save canonical social URL plus SSR metadata.
2. Preserve note images/video/contact sheet and OCR visible repo/tool names.
3. Verify the named repo/package directly before judging value.
4. Save README/SKILL/package excerpts and repo metadata, including license state.
5. Distinguish source evidence:
   - primary extraction evidence: live DOM, computed styles, CSS variables, stylesheet rules, visible text, interaction states;
   - review evidence: screenshots/contact sheets/previews;
   - generated artifacts: `DESIGN.md`/`design.md`, `design-preview.html`, evidence JSON.

Absorb as a module candidate only if the capability has a stable input/output contract:

- input URL(s);
- browser/runtime evidence bundle;
- durable design document;
- preview/review surface;
- validation/redaction rules.

Recommended taskpool shape:

- Use `add-repo-capability-absorption` when a verified repo/package exists.
- Target surface is usually `skill` or `sidecar`, integration level `evaluate` first.
- Acceptance should require license/dependency/risk review, 2-3 public dry-runs, explicit module interface, and a non-replacement boundary against existing UI validation skills.

Redlines:

- Do not import/vend external skills before license and compatibility review.
- Do not clone copyrighted designs verbatim; keep output at design-system/token/style-contract abstraction.
- Do not treat screenshots as the primary source when DOM/computed-style evidence is available.
- Do not let design-intake artifacts replace real UI/browser/viewport validation.

## Case lens B — Loop Engineering / workflow maturity lessons

Short clips about `Context Engineering → Harness Engineering → Loop Engineering` usually belong in a checklist/reference lane, not as code.

Map the terms as:

- **Context Engineering** — what information, rules, memory, project profiles, and evidence the agent sees.
- **Harness Engineering** — the execution and verification harness: browser/terminal/test runners, dry-run paths, proof checks, acceptance gates.
- **Loop Engineering** — a governed loop: observe state → select bounded action → execute → verify artifact/proof → update state → continue or escalate.

Recommended landing zone:

- For automation/task-worker absorption, load `harness-intake-contract` and land the lesson as a map → goal → acceptance → division → evidence → gates contract.
- Add/patch an architecture or workflow maturity checklist when the post only contributes vocabulary or a review lens.
- Create an advisory task only when there is concrete follow-up to write the checklist.
- Do not create a runtime module from a short vocabulary clip alone.

Minimum checklist questions:

1. Is there state write-back or only context injection?
2. Is there a proof/acceptance gate or only tool execution?
3. Is there a failure, retry, and human-escape path?
4. Are durable artifacts produced, or only transient previews/logs?
5. Does the loop preserve permission/side-effect boundaries?

Redlines:

- Do not treat a short social clip as an authoritative taxonomy.
- Do not rename existing architecture just because a term is trending.
- Do not use “loop” language to bypass proof, permission, or human gates.
