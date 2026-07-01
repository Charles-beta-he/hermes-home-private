# Social Pain Insight Loop

Applicability: use when the user wants market/customer pain discovery, opportunity analysis, product-category research, social listening, or public-source evidence for business ideas. This is especially useful when the desired output is traceable pain clusters, trends, opportunity scores, and raw-source links. Anti-conditions: do not use logged-in/private sessions, stealth/anti-bot bypass, paid APIs, or platform access-control workarounds unless the user explicitly authorizes a separate gated integration. Do not let model summaries replace raw URLs and quoted excerpts.

## Pattern

Turn a category or product idea into a source-grounded evidence loop:

```text
category / market / segment
  -> public-source discovery
  -> query expansion
  -> raw post/comment/review collection
  -> cleaning + dedupe
  -> pain clustering
  -> trend detection
  -> opportunity scoring
  -> traceable report + export
```

The useful abstraction is Karpathy/autoresearch-like iteration applied to market research: write the contract once, let the system repeatedly collect/evaluate/refine, keep improvements, rollback weak clusters, and preserve evidence.

## Inputs

- Category, product idea, or customer segment.
- Target geography/language/time window.
- Allowed public sources, for example Reddit, public forums, app reviews, product reviews, Product Hunt, YouTube comments, public social posts.
- Scoring rubric: severity, frequency, willingness-to-pay proxy, competition gap, reachability, compliance risk.
- Red lines: banned sources, no-login/no-stealth constraints, privacy requirements.

## Minimum pipeline

1. Define the research contract in plain text:
   - what to search;
   - allowed sources;
   - what counts as evidence;
   - scoring rubric;
   - stop conditions.
2. Generate query families:
   - pain terms: `problem`, `annoying`, `hate`, `struggle`, `issue`;
   - workaround terms: `how do you`, `alternative`, `manual`, `hack`;
   - comparison terms: `vs`, `better than`, `switch from`;
   - purchase/intent terms: `worth it`, `recommend`, `pay for`.
3. Collect public evidence only. Store at least URL, date if visible, excerpt, platform, engagement signal, and query used.
4. Clean and dedupe repeated posts, spam, ads, and copied content.
5. Cluster by job-to-be-done / failed expectation / workaround / severity.
6. Detect trends: repeated mentions, recent acceleration, cross-source recurrence, or unknown when evidence is too thin.
7. Score opportunities with explicit rubric; never hide subjective scoring behind a single magic number.
8. Export Markdown for narrative and CSV/JSON for downstream filtering.

## Output schema

```yaml
category: string
window: string
source_policy: public-source-only
sources:
  - platform: string
    query: string
    url: string
pain_clusters:
  - id: string
    title: string
    severity: 1-5
    frequency: int
    trend: rising|stable|declining|unknown
    opportunity_score: 0-100
    rationale: string
    evidence:
      - url: string
        excerpt: string
        date: string
        engagement: string
    suggested_product_angles:
      - string
risks:
  - string
next_validation:
  - string
```

## Verification checklist

- [ ] Every pain cluster has at least one raw URL and quote; high-confidence clusters should have multiple independent sources.
- [ ] The report labels source coverage gaps and platform bias.
- [ ] Opportunity scores cite the rubric dimensions, not just a model opinion.
- [ ] Claims from image/video/social posts are treated as leads until externally verified.
- [ ] No private/logged-in content, stealth bypass, or paid API was used without an explicit separate gate.
- [ ] Output includes a downstream-friendly export path: Markdown + CSV/JSON.

## Pitfalls

- **Summary without sources**: not acceptable. The artifact must be traceable.
- **Frequency illusion**: a subreddit or forum can over-represent a niche complaint; label source bias.
- **Metric laundering**: do not treat creator claims such as “hundreds of categories” or “1-2 day report” as proof of quality.
- **Overbuilding**: start as a one-shot public-source skill. Promote to recurring cron or a service pipeline only after one real category report passes evidence quality.
