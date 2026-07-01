# Public media advisory intake through taskpool closeout

Applicability: global Hermes taskpool workflow for public, non-private media/repo signals that are being handled as advisory/evidence tasks. Session-specific examples are illustrative only and must not be treated as standing project facts. Anti-condition: do not use this reference for private chats, credentialed pages, paid content, production deploys, or tasks that require installing/running untrusted code.

Use when a public social/video/repo link becomes a taskpool advisory item and the user authorizes full follow-through. This is a repeatable pattern for **evidence deposition**, not a license to implement or adopt the external capability.

## Trigger

- User shares public media links and asks to analyze/add to taskpool.
- User later says “认可，全盘推进” or equivalent.
- The item is advisory/evidence lane, not a production implementation task.

## Objective model

Success means:

1. Current taskpool mainline is respected: close or advance the highest-priority dispatchable P1/P0 work first when safe.
2. Public media items become bounded evidence packets with source readback, not vague summaries.
3. Advisory tasks reach `review`/`done` only with explicit evidence refs and proof-style closure strings accepted by taskpool gates.
4. No login/QR/private scraping bypass, no credential entry, no external publish, no installation/run of untrusted tools unless separately authorized.

## Procedure

1. **Check taskpool order first**
   - Run evidence-spine / dispatch dry-run via the taskpool orchestrator in normal work sessions.
   - If there is a P1/P0 work-lane dispatchable, drain that first unless blocked by permission/production/destructive boundary.
   - Only then continue P2/P3 advisory intake.

2. **Capture public media facts conservatively**
   - Use only public preview/browser/OCR where login/app gates exist. Do not bypass QR/app login.
   - Resolve short URLs to canonical public URLs when possible.
   - Capture visible author, title/caption, publish time, declared AI-generated label if present, duration, and engagement counters with ambiguity preserved.
   - Treat social claims as attention signals, not technical proof.

3. **Verify external artifacts directly**
   - For repository claims, query official APIs/docs for repo name, license, stars/forks, default branch, archived state, README/package/spec excerpts.
   - Prefer official project docs/specs over reposted articles.
   - Record access boundary and what was actually read.

4. **De-duplicate against existing task lines**
   - Search taskpool/brain for adjacent topics before creating a new implementation line.
   - If already covered, make the result a review/de-dup evidence packet and bounded follow-up candidate, not a broad duplicate task.

5. **Write a concise evidence packet**
   - Store under an explicit workflow/research path for that task/profile.
   - Include: source boundary, visible media facts, official artifact readback, existing coverage/de-dup relation, capability/value matrix, anti-conditions, recommendation, and minimum future slice.

6. **Advance lifecycle with proof-friendly evidence**
   - `pending -> claimed -> running -> review -> done` for bounded advisory items when evidence is complete.
   - Attach evidence strings such as:
     - `url:<canonical-public-url>`
     - `file:<absolute-evidence-packet-path>`
     - `command:<official/API readback summary>`
     - `proof:api_readback ...`
     - `proof:ui_surface public-media-page ...`
   - If closeout blocks with `browser_or_ui_surface_proof`, add a truthful `proof:ui_surface` describing the public preview/browser readback; do not fake screenshots.

7. **Promotion boundary**
   - Advisory done is not implementation approval.
   - Future implementation requires a separate task with reproduction/harness/risk gates.

## Reusable judgment patterns

- “Agent cockpit” public-media tools are usually best absorbed first as a **read-only activity/evidence inbox** concept, not as a replacement IDE or always-on watcher.
- “Knowledge format” public-media specs are usually best treated as **export/import compatibility targets for compiled knowledge bundles**, not as proof that retrieval is obsolete.

## Anti-conditions

- Do not install or run untrusted social-media tool repos just to close an advisory item.
- Do not enter platform credentials or bypass app/QR gates.
- Do not convert one social clip into global behavior, memory, or a skill without a class-level reusable procedure.
- Do not let advisory items preempt an unblocked P1/P0 work-lane mainline.
