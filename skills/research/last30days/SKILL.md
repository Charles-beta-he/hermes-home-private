---
name: last30days
version: "3.3.0"
description: "Use when research what people actually say about any topic in the last 30 days. Pulls posts and engagement from Reddit, X, YouTube, TikTok, Hacker News, Polymarket, GitHub, and the web."
argument-hint: 'last30days nvidia earnings reaction | last30days AI video tools | last30days what users want in react'
allowed-tools: Bash, Read, Write, AskUserQuestion, WebSearch
homepage: https://github.com/mvanhorn/last30days-skill
repository: https://github.com/mvanhorn/last30days-skill
author: mvanhorn
license: MIT
user-invocable: true
metadata:
  openclaw:
    emoji: "📰"
    requires:
      env: []
      optionalEnv:
        - SCRAPECREATORS_API_KEY
        - OPENAI_API_KEY
        - XAI_API_KEY
        - OPENROUTER_API_KEY
        - PARALLEL_API_KEY
        - BRAVE_API_KEY
        - APIFY_API_TOKEN
        - AUTH_TOKEN
        - CT0
        - BSKY_HANDLE
        - BSKY_APP_PASSWORD
        - TRUTHSOCIAL_TOKEN
      bins:
        - node
        - python3
    primaryEnv: SCRAPECREATORS_API_KEY
    files:
      - "scripts/*"
    homepage: https://github.com/mvanhorn/last30days-skill
    tags:
      - research
      - deep-research
      - reddit
      - x
      - twitter
      - youtube
      - tiktok
      - instagram
      - hackernews
      - polymarket
      - digg
      - bluesky
      - truthsocial
      - trends
      - recency
      - news
      - citations
      - multi-source
      - social-media
      - analysis
      - web-search
      - ai-skill
      - clawhub
---

# STEP 0: STALE-CLONE SELF-CHECK — RUN BEFORE READING BELOW

## Overview

Research what people actually say about any topic in the last 30 days. Pulls posts and engagement from Reddit, X, YouTube, TikTok, Hacker News, Polymarket, GitHub, and the web. It is organized around repeatable artifacts with clear input, output, and verification boundaries rather than open-ended exploration.

## When to Use

Use this skill when the request matches the `last30days` trigger and the domain-specific boundaries in this skill apply.

Don't use for:
- generic one-off questions that do not need this workflow;
- neighboring specialist workflows with a narrower matching skill;
- durable memory or project-profile writes unless this skill explicitly governs that landing zone;
- posting/liking/modifying social content, credential entry, or private/account-only data access;
- final business decisions that do not separate evidence, interpretation, confidence, and uncertainty.

Before reading anything else in this file, check whether you loaded SKILL.md from the one known stale-clone location: Claude Code's marketplaces directory.

**Run this check:**

```bash
CLAUDE_CACHE_LATEST=$(find "$HOME/.claude/plugins/cache/last30days-skill/last30days" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | sort -V | tail -1)
# Two cache layouts ship in the wild — nested ({version}/skills/last30days/SKILL.md)
# and flat ({version}/SKILL.md). Resolve to whichever shape actually exists.
CLAUDE_CACHE_SKILL_MD=""
if [ -n "$CLAUDE_CACHE_LATEST" ]; then
  if [ -f "$CLAUDE_CACHE_LATEST/skills/last30days/SKILL.md" ]; then
    CLAUDE_CACHE_SKILL_MD="$CLAUDE_CACHE_LATEST/skills/last30days/SKILL.md"
  elif [ -f "$CLAUDE_CACHE_LATEST/SKILL.md" ]; then
    CLAUDE_CACHE_SKILL_MD="$CLAUDE_CACHE_LATEST/SKILL.md"
  fi
fi
echo "CLAUDE_CACHE_SKILL_MD=$CLAUDE_CACHE_SKILL_MD"
```

If the SKILL.md path you just Read contains `/.claude/plugins/marketplaces/` AND `$CLAUDE_CACHE_SKILL_MD` is non-empty, STOP and re-read `$CLAUDE_CACHE_SKILL_MD` before proceeding. Otherwise the SKILL.md you have is fine — continue.

**Why this specific check:** `~/.claude/plugins/marketplaces/last30days-skill/` is a git clone Claude Code auto-restores to `origin/main` on session start. It can lag the versioned cache by one or more releases. Three 2026-04-22 test runs (Linear, Coinbase) loaded SKILL.md from `marketplaces/`, ran `--help` from the same stale path, did not see the `--competitors` flag that existed in the cache, and fell back to a manual comparison plan. Result: 2 of 3 windows never invoked the feature they were asked to test. STEP 0 defends against that one Claude Code-specific bug.

**Other install paths are fine:** `~/.codex/skills/`, `~/.agents/skills/`, an `npx skills add` install dir, or a repo checkout are all valid load points - the resolver in Step 1 picks them up. Do NOT abort or hop on those paths.

---

# SKILL CONTRACT — READ BEFORE ANY TOOL CALL

The detailed skill/output contract was moved to `references/skill-and-output-contract.md`.

Load it before any non-trivial Last30Days run or before rendering final output.

Minimum in-root rule: obey the runtime/source/security boundaries and never emit raw scrape clusters as the final answer.

# HOW TO INVOKE THIS SKILL (READ FIRST, FOLLOW EVERY TIME)

The detailed invocation contract was moved to `references/invocation-contract.md`.

Load it when translating a slash-command/user request into direct engine invocation, agent mode, or source plan.

Minimum in-root rule: use the skill as the primary UX; direct CLI is a fallback for scripting/dev/cron and must preserve shell quoting safety.

# last30days v3.3.0: Research Any Topic from the Last 30 Days

> **Permissions overview:** Reads public web/platform data and optionally saves research briefings to `LAST30DAYS_MEMORY_DIR` (defaults to `~/Documents/Last30Days`). X/Twitter search uses optional user-provided tokens (AUTH_TOKEN/CT0 env vars). Bluesky search uses optional app password (BSKY_HANDLE/BSKY_APP_PASSWORD env vars - create at bsky.app/settings/app-passwords). All credential usage and data writes are documented in the [Security & Permissions](#security--permissions) section.

Research ANY topic across Reddit, X, YouTube, and other sources. Surface what people are actually discussing, recommending, betting on, and debating right now.

## Runtime Preflight

Before running any `last30days.py` command in this skill, resolve a Python 3.12+ interpreter once and keep it in `LAST30DAYS_PYTHON`:

```bash
for py in python3.14 python3.13 python3.12 python3; do
  command -v "$py" >/dev/null 2>&1 || continue
  "$py" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)' || continue
  LAST30DAYS_PYTHON="$py"
  break
done

if [ -z "${LAST30DAYS_PYTHON:-}" ]; then
  echo "ERROR: last30days v3 requires Python 3.12+. Install python3.12 or python3.13 and rerun." >&2
  exit 1
fi

LAST30DAYS_MEMORY_DIR="${LAST30DAYS_MEMORY_DIR:-$HOME/Documents/Last30Days}"
```

## Configuration

Set `LAST30DAYS_MEMORY_DIR` before invoking the skill to choose where raw research files are saved. If it is not set, the skill defaults to `~/Documents/Last30Days`.

## Step 0: First-Run Setup Wizard

Before proceeding to Step 1, handle first-run setup.

**First-run detection (silent, no commands, no output to user):**
- If `~/.config/last30days/.env` does NOT exist, this is a first run.
- If the file exists and contains `SETUP_COMPLETE=true`, skip Step 0 entirely and go to Step 1 (CRITICAL: Parse User Intent below). Do NOT announce that setup is complete. The user does not need a status message on every run.

**If this IS a first run:**
- Use the Read tool to load `skills/last30days/nux-wizard.md` (relative to the skill root).
- Follow the wizard's instructions end-to-end. The wizard handles platform detection (OpenClaw vs Claude Code), auto vs manual setup, ScrapeCreators opt-in, and the initial topic picker.
- After the wizard writes `SETUP_COMPLETE=true` to `~/.config/last30days/.env`, proceed to research.

The wizard lives in a separate file so the common-case (already set up) path through this file is short and the voice-contract rules further down stay in context.

---


## CRITICAL: Parse User Intent

Detailed query-type/intent parsing rules were moved to `references/parse-user-intent.md`.

Load it when the request may be a comparison, market scan, trend watch, product evaluation, or ambiguous topic.

Minimum in-root rule: identify query type before collection; wrong query framing produces bad evidence even if the engine succeeds.

## Step 0.45: Query Quality Pre-Flight (detect keyword-trap topics BEFORE running the engine)

Detailed query-quality preflight rules were moved to `references/query-quality-preflight.md`.

Load it when topic wording may trigger generic/keyword-trap results.

Minimum in-root rule: improve the query plan before execution rather than compensating after low-signal collection.

## Step 0.5: Pre-Flight Resolution (handles, repos, communities)

The detailed handle/repo/community pre-flight resolution procedure was moved to `references/preflight-resolution-handles-repos-communities.md`.

Load it when the topic includes ambiguous handles, repositories, communities, products, or comparison entities.

Minimum in-root rule: resolve the entity before running broad collection; avoid keyword-trap queries when canonical handles/repos are available.

## Agent Mode (--agent flag)

If `--agent` appears in ARGUMENTS (e.g., `/last30days plaud granola --agent`):

1. **Skip** the intro display block ("I'll research X across Reddit...")
2. **Skip** any `AskUserQuestion` calls - use `TARGET_TOOL = "unknown"` if not specified
3. **Run** the research script and WebSearch exactly as normal
4. **Skip** the "WAIT FOR USER RESPONSE" pause
5. **Skip** the follow-up invitation ("I'm now an expert on X...")
6. **Output** the complete research report and stop - do not wait for further input

Agent mode saves raw research data to `LAST30DAYS_MEMORY_DIR` (defaults to `~/Documents/Last30Days`) automatically via `--save-dir` (handled by the script, no extra tool calls).

Agent mode report format:

```
## Research Report: {TOPIC}
Generated: {date} | Sources: Reddit, X, Bluesky, YouTube, TikTok, HN, Polymarket, Web

### Key Findings
[3-5 bullet points, highest-signal insights with citations]

### What I learned
{The full "What I learned" synthesis from normal output}

### Stats
{The standard stats block}
```

---

## If QUERY_TYPE = COMPARISON

Detailed comparison / `--competitors` / `--competitors-plan` protocol moved to `references/comparison-and-competitor-mode.md`.

Load it for `{A} vs {B}` topics, competitor discovery, multi-entity plans, Polymarket disambiguation, and head-to-head table synthesis.

Minimum in-root rule: comparison runs require per-entity resolution and a filled head-to-head block; dashes in resolved entities mean the run is under-specified.

## Step 0.55: Pre-Research Intelligence (resolve communities + handles)

The detailed pre-research intelligence pass was moved to `references/pre-research-intelligence.md`.

Load it for ambiguous products/communities/handles or when prior source resolution is needed before query-plan generation.

Minimum in-root rule: do not spend collection budget until key entities and communities are resolved enough to produce high-signal queries.

## Step 0.75: Generate Query Plan (YOU are the planner)

Detailed query-plan generation instructions were moved to `references/generate-query-plan.md`.

Load it after entities/communities are resolved and before running the collection engine.

Minimum in-root rule: build a source-aware query plan with per-source constraints; do not run one broad keyword across every source.

## Research Execution

Detailed research-execution command guidance was moved to `references/research-execution.md`.

Load it when invoking the engine, handling temp plan files, or preserving shell-quoting safety.

Minimum in-root rule: write complex JSON plans to temp files; do not inline fragile single-quoted JSON with apostrophes.

## STEP 2: DO WEBSEARCH AFTER SCRIPT COMPLETES

Detailed post-engine WebSearch supplement rules were moved to `references/websearch-supplement.md`.

Load it after script collection when web context, comparison articles, or source corroboration is needed.

Minimum in-root rule: supplemental web evidence must be appended and weighed, not replace source-specific social/community data.

## Judge Agent: Synthesize All Sources

The detailed judge-agent synthesis procedure was moved to `references/judge-agent-synthesize-all-sources.md`.

Load it after engine output + supplemental web search are available and before final synthesis.

Minimum in-root rule: synthesize across sources, cite evidence clusters, and label confidence; do not simply concatenate findings.

## Synthesis and Presentation Contract

The detailed post-research synthesis, comparison-output, invite-vision, optional HTML brief, wait/respond, context-memory, and footer instructions were moved to `references/synthesis-and-presentation-contract.md` to keep the root skill loadable.

Load that file after the collection engine and supplemental web search are complete, before presenting the final Last30Days synthesis or when the user asks for a comparison, shareable brief, more options, or expert follow-up.

Minimum in-root rule: do not present raw clusters as the answer. First internalize the evidence, rank claims by source quality, clearly separate facts from interpretation, include the required badge/footer, and invite the user's next direction.

## Security & Permissions

Detailed Last30Days security/permission notes were moved to `references/security-and-permissions.md`.

Load it before enabling optional providers, credentials, or source-specific auth.

Minimum in-root rule: do not post/like/modify content, access user accounts, log secrets, or send data to endpoints outside the listed source boundary.

## Common Pitfalls

1. Producing a plausible artifact without checking the requested output contract.
2. Skipping prerequisite checks and assuming the environment already matches the workflow.
3. Reporting success before reading back the actual outputs, files, or external side effects.

## Verification Checklist

- [ ] Preconditions, scope, and tool availability were checked before following this workflow.
- [ ] The key output artifacts, commands, or side effects were verified by read-back or direct inspection.
- [ ] Any remaining uncertainty, blocker, or human handoff was stated explicitly.
- [ ] The generated artifact was read back and checked against the requested structure or template.
