# Last30Days Invocation Contract

Extracted from `/Users/charles/.hermes/skills/research/last30days/SKILL.md` on 2026-07-01T08:22:36.087987+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

# HOW TO INVOKE THIS SKILL (READ FIRST, FOLLOW EVERY TIME)

**STEP 0 - LOAD WEBSEARCH FIRST.** Your literal first tool call on every `/last30days` invocation MUST be:

```
ToolSearch select:WebSearch
```

WebSearch is a **deferred tool** in Claude Code v2.1.114. The frontmatter of this file authorizes it (`allowed-tools: ... WebSearch`) but the runtime lists it as "schemas are NOT loaded." Calling WebSearch without `ToolSearch select:WebSearch` first will fail or do nothing. That friction is the documented cause of the second-most-common failure mode of this skill: the model sees "WebSearch is there but deferred," takes the low-friction path, skips Step 0.5 and 0.55, and runs the engine bare with only keyword search. The output looks fine but misses founder X timelines, GitHub repo activity, and subreddit-specific threads.

Load WebSearch first. No exceptions. Then proceed to the branching rule below.

**STEP 1 - RUN THE ENGINE. You MUST run `scripts/last30days.py` via Bash. Do not produce output from WebSearch alone.**

The single most common failure mode of this skill is the model reading this file, skimming the section headers, and then answering the user's topic with 3-10 WebSearch calls followed by a prose summary. That is wrong output. The Python engine is the skill. Web-only synthesis is not the skill.

Branching rule:

- **If the user provided a topic** (e.g. `/last30days Kanye West`, `/last30days nvidia earnings`): proceed to Step 0.5 / Step 0.55 / Step 0.75 / Research Execution below. Do not skip straight to WebSearch. WebSearch is a **supplement after** the Python engine runs (see Step 2). It is **not a substitute**.
- **If the user provided no topic**: ask the user for a topic with a single short question. Do not run research. Do not run WebSearch. Wait.

If you are about to write a response without having run `scripts/last30days.py` at least once, stop. Return to Research Execution and run the engine. Every valid output from this skill includes the emoji-tree footer (`✅ All agents reported back!`) that the engine produces data for. No footer means you did not run the skill.

Before Step 0.5, run Step 0.45 Query Quality Pre-Flight. If the topic is a keyword trap (demographic shopping like "gift for 42 year old man", numeric/age trap, overly-literal concept phrase like "how to use Docker", or generic single-noun like "sneakers"), reframe or ask ONE clarifying question before calling the engine. Skipping Step 0.45 on a keyword-trap topic is the named failure mode of the 2026-04-18 "Birthday gift for 42 year old man" disaster: the engine ran on the literal phrase and returned 5 minutes of r/todayilearned / r/japannews / r/LivestreamFail noise because no human posts "I bought a 42 year old man a gift" on Reddit.

If your Bash call to `last30days.py` does NOT include the FULL pre-flight checklist resolved (see Step 0.5 Pre-Flight Checklist), that is a Step 0.5/0.55 skip. The engine will emit a `## Pre-Research Status` warning block in its output. Pass the warning through verbatim; do not try to hide it. The warning tells the user to rerun with WebSearch loaded.

**For person topics specifically (developers, creators, CEOs, founders): the Bash command MUST include MINIMUM `--x-handle={handle}` AND `--github-user={handle}` AND `--subreddits={list}`, and typically `--x-related={list}`, unless an explicit "no account" note was produced during Step 0.5.** A person-topic command with ONLY `--x-handle` is the Peter Steinberger disaster #2 failure mode (2026-04-18): the model read the X-handle subsection literally, stopped there, and skipped the rest of the checklist. Result: weak Reddit targeting, no GitHub person-mode scoping, no related-voices enrichment, and a thin corpus. The fix is to read the Step 0.5 Pre-Flight Checklist FIRST and resolve every applicable flag before running the engine.

---
