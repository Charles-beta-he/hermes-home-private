# Public-Evidence Opportunity Validation for Solo Operators

## Scope and boundaries

- **Scope:** domain-level research workflow for one-person-company opportunity discovery when warm-network access is weak, social energy is constrained, or the user wants asynchronous validation.
- **Applicability:** use for market/opportunity research, productized-service discovery, and pre-SaaS validation.
- **Anti-conditions:** do not use as a mandate to scrape private data, spam contacts, bypass platform rules, or avoid all customer contact forever. Do not treat the external repositories named below as permanent dependencies; re-check licenses, maintenance, and fit before implementation.
- **Falsifier:** if the user has a strong warm network, regulated-enterprise sales motion, or already-validated customer pipeline, direct interviews/sales may beat this inbound-first path.

## Core pattern

When the user lacks warm contacts, avoid defaulting to “ask friends / interview 20 people / go do cold calls.” Prefer:

```text
public evidence → automated sample/report → landing/waitlist → inbound form → async delivery → paid validation
```

The key is not to skip validation; it is to change the validation mechanics to reduce social load.

## Pipeline nodes

1. **Seed pool** — failed-startup databases, GitHub issues/discussions, public reviews/complaints, competitor pages/pricing, forums, hiring/JD signals, policy notices.
2. **Collection** — convert public signals into structured records: source, segment, problem quote, evidence URL, frequency, money signal, and risk.
3. **Scoring** — use:

   ```text
   opportunity_score =
     pain_strength × payment_signal × reachability × operator_can_deliver
     ÷ competition × domain_unknowns × compliance_risk × delivery_complexity
   ```

   Penalize heavy outbound, unfamiliar expert domains, in-person BD, regulated advice, marketplace cold starts, and hardware/supply-chain dependency. Reward async inbound, report/template/service-first delivery, public evidence, and frontend/AI/automation leverage.
4. **Sample assets** — generate one-page service pages, diagnostic reports, competitor teardowns, issue/complaint maps, risk assessments, or landing-page audits before building SaaS.
5. **Waitlist/form gate** — ask who they are, current pain, current workaround, willingness to pay for a diagnostic/report/template, and async contact method.
6. **Low-pressure lead stages** — discovered → scored → sample generated → published → inbound lead → async delivery → paid/declined → feedback.
7. **Paid validation** — sell small diagnostics/templates/reports before building full SaaS.
8. **Async feedback** — form/doc/email questions: did it help decide, which section had value, would they pay again.

## External project categories to re-check

Treat these as examples of reusable building blocks, not global requirements.

- **LLM-friendly crawling:** `unclecode/crawl4ai`, `apify/crawlee-python`; use for public webpage-to-markdown/evidence collection.
- **Web extraction services/frameworks:** `firecrawl/firecrawl`; useful to study or use, but verify license/commercial boundary.
- **Browser automation/MCP patterns:** `browserwing/browserwing`; useful for turning repeatable browser workflows into commands.
- **Lead discovery:** Google Maps/lead-generation repos can inspire overseas/local-business research, but must not become spam automation.
- **CRM references:** `twentyhq/twenty`, `frappe/crm`; study object model and pipeline UI, avoid deploying a heavy CRM before the workflow is validated.
- **Report generation:** `observablehq/framework` for static data reports/dashboards; security-report tools can inspire evidence-pack structure.
- **Waitlist:** lightweight Next.js waitlist templates can scaffold the first landing page.
- **Workflow platforms:** `n8n`/`activepieces` can be external orchestrators or architecture references, but are too heavy as the first deliverable.

## Minimal MVP shape

```text
collect public evidence
→ normalize into JSONL/SQLite
→ score opportunity fit
→ generate Markdown/HTML report
→ generate waitlist landing copy/form fields
```

Start local-first with files/scripts. Add backend/CRM only after reports create inbound interest.

## Solo-maker compliance blocker triage

When a one-person or AI-assisted product hits monetization friction (registration, website/app filing, paid services, ad-network access, payments, invoices, app-store review, or regulated online services), split the blocker before advising:

```text
commercial subject friction
  → entity registration, address, bank/tax/invoice, enterprise filing, platform settlement
license / regulated-activity requirement
  → official regulator criteria, scope triggers, application conditions, non-exemption rules
platform commercial rule
  → ad network/payment/app store subject type, content policy, settlement rules
business-model trigger
  → own products/services vs third-party marketplace/platform/info publishing/transaction matching
```

Applicability: use this as a research triage pattern, not legal advice. Anti-condition: do not store jurisdiction-specific conclusions as global rules; re-check current official sources for the user’s location, entity type, and business model. A local entrepreneurship policy may reduce registration/address/guidance friction while leaving license requirements unchanged.

## Pitfalls

1. Building a full SaaS before anyone pays for the diagnostic/report.
2. Using contact scraping as permission to spam.
3. Optimizing automation infrastructure instead of publishing sample reports.
4. Choosing domains that require deep authority, compliance opinions, hardware, or in-person BD.
5. Treating social anxiety as a reason to avoid validation rather than as a constraint that changes the validation channel.
6. Collapsing “can register a lightweight business entity” into “can legally run a regulated business”; registration support and licensing exemption are different questions.
7. Confusing a platform’s enterprise-subject requirement with a government license requirement; validate both separately.
