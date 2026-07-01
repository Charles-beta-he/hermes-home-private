# Daily-report project analysis checklist

Use when a user asks to parse/analyze a named item that may have appeared in an AI/product/GitHub daily report, especially short ambiguous names.

## Landing zone

This is a reusable research procedure. It is not a memory of one Product Hunt item or one GitHub repo.

## Procedure

1. **Resolve context before global web search**
   - Search recent sessions/reports for the exact name and likely variants.
   - Prefer the report artifact that introduced the item over generic search results.
   - If the item came from Product Hunt, GitHub Trending, AIHOT, newsletter, or a local digest script, preserve that source frame in the analysis.

2. **Disambiguate the entity**
   - Record source type: GitHub Trending repo, Product Hunt product, blog/news item, paper, model, company, or crypto/Web3 signal.
   - If multiple entities share the name, choose the one evidenced by the report and say what was excluded.
   - Avoid analyzing the globally popular meaning of the name unless the report evidence points there.

3. **Resolve GitHub evidence when present**
   - Extract or resolve the GitHub repository URL.
   - If Product Hunt only exposes redirect links, try source-page links, search by exact tagline/name, and GitHub repository search.
   - Capture metadata: `full_name`, URL, description, stars, forks, license, last push, default branch.
   - If cloning for deeper review, use a scratch path such as `~/.hermes/runs/<name>-reference-review-*` and read repo instructions/docs first.

4. **Analyze with evidence layers**
   - What it is: one-sentence product/repo positioning.
   - Architecture/workflow: core components and control boundaries.
   - Value: user/customer problem, why it is timely, and what trend it represents.
   - Engineering maturity: repo shape, tests, docs, examples, release signals, license.
   - Risks: security/privacy/safety, permission model, operational burden, overclaiming, vendor lock-in.
   - Transferability: patterns worth absorbing into Hermes or the user's workflows, separated from code that should not be copied.

5. **Classify follow-up**
   - Reusable workflow/pitfall → patch a class-level skill.
   - Concrete engineering work → propose taskpool candidate, not a fake skill.
   - Project-specific URL/path/branch → project profile or scoped reference, not global memory.
   - Session progress → no durable write.

## Output shape

- Start with the resolved entity and source evidence.
- Then give the conclusion before detail.
- For GitHub projects, include repo metadata and a short risk/readiness verdict.
- Clearly separate “worth tracking”, “worth adapting as a pattern”, and “not safe/mature enough to reuse directly”.

## Anti-conditions

- Do not treat Product Hunt copy as proof of technical capability.
- Do not rely on a name-only web search when session/report evidence exists.
- Do not run offensive/security tools or contact third-party targets while analyzing a security project; static review is enough unless the user explicitly scopes and authorizes testing.
