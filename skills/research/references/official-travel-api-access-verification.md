# Official Travel API Access Verification

## Scope and applicability

This reference is a reusable verification method for researching whether travel-industry APIs can be formally integrated across flights, lodging, attraction tickets, rental vehicles, and rail. It applies when the user requires first-party documentation and a defensible developer-access classification.

**Anti-conditions:** do not use this reference to preserve a provider's current eligibility, URL, pricing, endpoint list, or contract terms as timeless facts. Re-open and verify all first-party sources for each investigation. Do not use it for scraping or reverse-engineering internal web/mobile endpoints.

## Goal

Classify each provider using first-party evidence, without confusing a product/marketing page, logged-in portal, internal web endpoint, SDK, or third-party aggregator with a publicly supported API.

## Access-status taxonomy

- **Direct self-service**: an official page explicitly shows public registration, application creation, credentials, sandbox, and a production path. Record production-only contract/billing requirements separately.
- **Partner/enterprise review required**: official prerequisites require affiliate/partner status, an account manager, signed agreement, business qualification, platform admission, or manual approval.
- **Documentation non-public / access-gated**: an official developer or alliance portal exists, but API reference or eligibility rules require login or cannot be read anonymously.
- **No official public API verified**: after checking the official site, developer subdomains, and official documentation, no public developer registration, reference, credential, or production authorization can be verified. Phrase this as an evidence boundary—not proof that no private API exists.

## Procedure

1. Identify official domains from the provider's own site; reject similarly named aggregators and unofficial documentation or code repositories as authorization evidence.
2. Locate the actual developer reference or onboarding/prerequisites page. Prefer API reference, quick-start, authentication, sandbox, pricing, production, and terms pages over landing pages.
3. Extract explicit evidence for:
   - who may register (individual, company, managed affiliate, supplier);
   - whether credentials are issued automatically;
   - sandbox/test availability;
   - production requirements (contract, billing, account manager, review);
   - supported transaction depth (search/data only vs reservation/order/ticketing/payment);
   - publication status (anonymous docs vs login-gated/private docs).
4. Separate **test access** from **formal production access**. A provider may allow personal sandbox registration but require a contract and billing profile for production.
5. Separate **data/API availability** from **booking authority**. Status, schedules, prices, reservations, issuance, cancellation, and payments are distinct capabilities.
6. If an official marketing/product page mentions “API,” use it only to prove that a commercial API product exists. Do not infer endpoint documentation, self-service eligibility, pricing, SLA, or production authorization.
7. Do not treat observed website/App endpoints as public APIs unless the provider publishes developer terms and authorization.
8. Report an evidence matrix with provider, domain, segment, access classification, official URL, exact quoted/paraphrased prerequisite, and evidence limitation.

## Negative-evidence checklist

Before writing “no official public API verified,” confirm that the first-party public surface lacks all of:

- developer registration;
- API reference or machine-readable specification;
- authentication/key issuance instructions;
- sandbox documentation;
- production terms or partner onboarding.

State: “No public official documentation was verified; private partner interfaces may still exist.” Never state categorical nonexistence from search silence.

## Common pitfalls

- Treating “Open Platform,” “Data Product,” “Free Trial,” or “Contact Us” as proof of individual self-service access.
- Treating an affiliate program as an open developer program.
- Calling a login-gated documentation center “public documentation.”
- Equating an official agent-protocol tool with a supported commercial REST API and SLA.
- Treating third-party wrappers, scraped endpoints, or internal browser APIs as formal authorization.
- Collapsing sandbox registration and production approval into one status.
- Listing URLs without explaining what each page actually proves—and what it does not prove.

## Output recommendation

Use a concise table and preserve evidence boundaries. Recommended status labels:

1. `个人可自助测试；生产需签约/结算`
2. `需企业或合作伙伴审核`
3. `官方文档登录后可见/不可公开核验`
4. `未核验到官方公共 API（不排除私有合作接口）`

Include a short practical-selection section only after the evidence table.