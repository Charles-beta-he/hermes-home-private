---
name: research
description: Use when you need the Research workflow umbrella. See references/ for
  detailed guides.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags:
    - research
    - workflow
    - umbrella
    - routing
    related_skills:
    - arxiv
    - blogwatcher
    - llm-wiki
    - polymarket
    - research-paper-writing
---

# Research

## Overview

This umbrella skill is the routing surface for research. Use it to choose the most specific child skill, reference, or workflow instead of treating the category name as a one-size-fits-all procedure.

## When to Use

- You need help somewhere inside research and want the quickest route to the right child skill.
- You are not yet sure which research sub-workflow best matches the request.
- You want a compact map of the research skill family before loading a more specific procedure.
- Don't use for: a request that already clearly matches one specific research child skill; load that child skill directly.

## Routing Guide

- `arxiv` — you need to search and retrieve academic papers from arXiv using their free REST API.
- `blogwatcher` — you need to monitor blogs and RSS/Atom feeds for updates using the blogwatcher-cli tool.
- `llm-wiki` — you need guidance on karpathy's LLM Wiki — build and maintain a persistent, interlinked markdown knowledge base. For Hermes-specific evaluation and landing-zone boundaries, use `references/llm-wiki-compiled-knowledge-layer.md`.
- `polymarket` — you need guidance on query Polymarket prediction market data — search markets, get prices, orderbooks, and price history.
- `travel-planning-with-personal-history` — use `references/travel-planning-with-personal-history.md` when planning trips/routes, especially motorcycle/couple travel, and the user expects current facts plus personal history/photo-location de-duplication.
- `research-paper-writing` — you need guidance on end-to-end pipeline for writing ML/AI research papers — from experiment design through analysis, drafting, revision, and submission.
- `references/public-evidence-solo-validation.md` — use when validating one-person-company opportunities for users with weak warm networks or social-energy constraints: public evidence → automated sample/report → landing/waitlist → inbound async paid validation.
- `references/social-pain-insight-loop.md` — use when doing public-source customer pain / opportunity research from social posts, forums, reviews, or comments: raw-source collection → pain clustering → trend judgment → opportunity scoring → traceable Markdown/CSV export. Anti-condition: no logged-in/private scraping, stealth bypass, or model-only summaries without raw URLs/excerpts.
- `references/collectible-wine-price-check.md` — use when checking current value, resale range, or aging/appreciation claims for vintage wine/spirits. Resolve the exact bottle, triangulate merchant prices, convert currency live, and separate retail asking price from domestic landed/private resale value.
- `references/medical-misconduct-public-evidence.md` — use when checking public evidence for medical sexual-assault/molestation/privacy-violation allegations tied to a hospital, doctor, procedure, or anesthesia setting. Classify exact matches vs same-region unrelated cases, legal status, and practical process checks; absence of indexed evidence is not proof of safety or non-occurrence.
- `references/public-medical-incident-research.md` — use when the user asks to query a Chinese public medical “事件” and the phrase may be an ambiguous cluster rather than one canonical incident; disambiguate adverse event / misconduct allegation / pricing dispute / general Q&A, separate verified sources from snippets, and avoid collapsing unrelated cases.

## Selection Rules

- Prefer the narrowest child skill that matches the user request, platform, and desired artifact.
- Stay at the umbrella level only for routing, taxonomy, or category-wide orientation.
- If the request spans multiple subskills, use this umbrella to map the lane first, then hand off to the specific workflow that will do the real work.

## Absorbed Workflow Packages (5 consolidated in curator umbrella pass)

These former narrow child skills are now treated as subsections/reference packages under this class-level umbrella. Load the package only when the task needs that provider/tool's detailed commands, templates, or scripts; otherwise use the umbrella routing rules above.

- `arxiv` → `references/arxiv.md`: Use when you need to search and retrieve academic papers from arXiv using their free REST API.
- `blogwatcher` → `references/blogwatcher.md`: Use when you need to monitor blogs and RSS/Atom feeds for updates using the blogwatcher-cli tool.
- `llm-wiki` → `references/llm-wiki.md`: Use when you need guidance on karpathy's LLM Wiki — build and maintain a persistent, interlinked markdown knowledge base.
- `polymarket` → `references/polymarket.md`: Use when you need guidance on query Polymarket prediction market data — search markets, get prices, orderbooks, and price history.
- `research-paper-writing` → `references/research-paper-writing.md`: Use when you need guidance on end-to-end pipeline for writing ML/AI research papers — from experiment design through analysis, drafting, revision, and submission.


## Daily-report project disambiguation

When the user asks to "解析/分析 <name>" and the prior context may be a daily report, Product Hunt item, GitHub Trending entry, or newsletter signal, do not jump to the globally most famous meaning of the name. First resolve the name against recent session/report evidence, then analyze the concrete source artifact. See `references/daily-report-project-analysis.md` for the checklist.

## Common Pitfalls

1. Using the research umbrella as the full procedure even though a more specific child skill already fits.
2. Reading the routing map but never loading the referenced child skill or support material that contains the actual execution steps.
3. Choosing a child skill without checking that its platform, tools, and expected artifacts match the current task.
4. When the user refers to an item from a prior daily report/newsletter by shorthand (for example a Product Hunt/GitHub item name), do not jump to broad web interpretation first. Search prior sessions/local report artifacts for the exact report context, then resolve the canonical source/repo from that evidence before doing general web or GitHub research.
4. Ambiguous-name miss: treating a daily-report project name as a general web/entity query (e.g. entertainment franchise, company, common product name) before checking session_search or the local report that introduced it.

## Verification Checklist

- [ ] The request was mapped to the best-fitting child skill or explicitly kept at umbrella level for routing only.
- [ ] The selected child skill descriptions, references, and prerequisites were checked before substantive execution.
- [ ] Any claimed handoff, output, or route decision was read back against the specific child workflow before completion.



## 输入

- 用户请求的具体参数

## 检查点

- [ ] 输入参数完整
- [ ] 输出符合预期格式
