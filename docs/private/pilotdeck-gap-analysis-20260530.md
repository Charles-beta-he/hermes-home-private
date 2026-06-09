# PilotDeck vs Hermes — Gap Analysis & Transferable Patterns

**Date:** 2026-05-30
**Source:** `OpenBMB/PilotDeck` (commit `8f8da6a`, cloned 2026-05-30)
**Scope:** Routing, task complexity, cost optimization, always-on patterns

---

## 1. Architecture Comparison

| Dimension | PilotDeck | Hermes |
|---|---|---|
| **Language** | TypeScript (Node.js gateway + React UI) | Python (CLI + TUI + gateway) |
| **Unit of isolation** | WorkSpace (per-project files/memory/skills) | Profile (`~/.hermes/profiles/<name>/`) + brain overlays |
| **Routing** | Built-in `RouterRuntime` with 4-tier judge + auto-orchestration | External `model-router.py` ε-greedy selector + config fallback |
| **Memory** | White-box per-WorkSpace, Dream Mode consolidation | Skill-injected context + brain notes + session DB (FTS5) |
| **Background execution** | Always-on: discovery plans, work cycles, workspace snapshots | Cron jobs + taskpool dispatch tick + bg-review |
| **MCP** | Native first-class | Supported via MCP server config |
| **Cost tracking** | `TokenStatsCollector` per-session, baseline comparison | `pricing.py` + `model-router.py` log |

---

## 2. Smart Routing — Algorithm Deep Dive

### PilotDeck's 4-Tier Classification

PilotDeck uses a **judge model** (lightweight, e.g. Sonnet) to classify each user message into one of 4 tiers:

| Tier | Description | Typical Model |
|---|---|---|
| `simple` | Greetings, confirmations, single-step Q&A, trivial writes | Light (MiniMax-M2.7) |
| `medium` | Single tool call, short generation, 1-2 file ops | Mid (Sonnet 4.5) |
| `reasoning` | Deep single-agent: multi-file, data analysis, multi-step | Strong (Opus 4.5) |
| `complex` | Sub-agent orchestration: parallel workstreams | Orchestrator + sub-agents |

**Key design decisions:**
- `complex` is **exclusively** for sub-agent orchestration — not for single-agent deep work
- Judge prompt includes **previous tier context** to prevent mis-downgrading continuations ("继续", "ok", "go")
- 4 default routing rules prevent judge confusion between `reasoning` and `complex`
- Judge timeout: 15s default, 3 retries with 1s backoff
- Sub-agent detection: checks for `<pilotdeck-subagent-model>` tags + missing Agent/Task tool

### Auto-Orchestration Trigger

When tier = `complex`:
1. Inject orchestrator system prompt (plan-and-delegate)
2. Strip tools to whitelist: `agent`, `read_file`, `grep`, `glob`, `read_skill`
3. Sub-agents inherit full tool permissions
4. Sub-agent model can be overridden (`subagentModel` config)

### Hermes's Current Routing

Hermes `model-router.py` uses:
- **ε-greedy selection** based on `route_outcomes` model_stats
- **Task tier/class** filtering (codegen, feature, bugfix, review)
- **Pricing-aware** scoring via `pricing.py`
- **Sticky routing** (session-level model persistence)
- **Provider availability** check via env vars + OAuth sets

**Gap:** No LLM-based judge classifier. Routing is stats-driven (outcome history) rather than content-driven (message complexity).

---

## 3. Transferable Patterns for Hermes

### Pattern A: Judge-Based Tier Classification (HIGH VALUE)

**What:** Use a lightweight model to classify message complexity before routing.

**Hermes integration point:** `agent/run_conversation()` pre-dispatch, or `model-router.py select` enhancement.

**Sketch:**
```python
# In model-router.py or a new classify_message.py
TIERS = {
    "simple": "Greetings, confirmations, single-step Q&A",
    "medium": "Single tool call, short code gen, 1-2 file ops",
    "reasoning": "Multi-file ops, data analysis, multi-step workflows",
    "complex": "Parallel delegation, multi-agent orchestration",
}

def classify_tier(message: str, previous_tier: str = None) -> str:
    judge_prompt = build_judge_prompt(message, TIERS, previous_tier)
    # Use cheapest available model (e.g. MiMo-flash or Gemini-flash)
    result = hermes_chat(provider="xiaomi", model="mimo-v2.5-flash", 
                         message=judge_prompt, max_tokens=64)
    return parse_tier(result)
```

**Cost:** ~$0.001 per classification (lightweight judge)
**Savings:** 70%+ on mixed workloads (PilotDeck benchmark)

### Pattern B: Continuation-Aware Routing (MEDIUM VALUE)

**What:** Detect continuation messages ("继续", "ok", "go") and inherit previous tier.

**Hermes integration:** Session-level sticky routing already exists in `model-router.py` via `STICKY_FILE`. Enhancement: add continuation detection to prevent tier downgrade.

### Pattern C: Per-Session Token Statistics (MEDIUM VALUE)

**What:** Track token usage per session with baseline model comparison for cost savings reporting.

**Hermes integration:** `TokenStatsCollector` equivalent → extend `pricing.py` or add to `model-router.py` stats output.

### Pattern D: Always-On Discovery Plans (HIGH VALUE)

**What:** Background agent proactively discovers tasks, runs monitors, lands deliverables as files.

**Hermes comparison:** Hermes has cron jobs + taskpool dispatch tick + bg-review, but lacks:
- **Discovery plans** (proactive task identification from workspace state)
- **Work cycles** (structured idle-time work with workspace snapshots)
- **Dormant state tracking** (knowing when user is away vs active)

**Gap:** Hermes bg-review is reactive (reviews past conversations), not proactive (discovers new work).

### Pattern E: Workspace-Scoped Memory Isolation (LOW PRIORITY)

**What:** Per-WorkSpace memory with white-box editing and Dream Mode rollback.

**Hermes comparison:** Hermes profiles provide isolation; brain notes provide workspace-scoped context. Memory is skill-injected, not user-editable in the same way.

**Assessment:** Hermes's brain overlay + profile system already provides isolation. The white-box editing UX is a UI concern, not a routing/architecture gap.

---

## 4. Task Complexity Evaluation Criteria (from PilotDeck)

| Signal | Simple | Medium | Reasoning | Complex |
|---|---|---|---|---|
| Tool calls needed | 0 | 1-2 | 3+ | Parallel agents |
| File operations | 0 | 1-2 | 3+ | Cross-project |
| Analysis depth | None | Shallow | Deep single-domain | Multi-domain |
| Output format | Short text | Code/text | Structured report | Delegated artifacts |
| Continuation | N/A | N/A | May continue | May orchestrate |

---

## 5. Recommended Hermes Implementation Order

1. **Judge classifier** (classify_message.py) — 1-2 days, high ROI
2. **Continuation detection** in sticky routing — 0.5 days
3. **Token stats collector** — 1 day, enables cost reporting
4. **Discovery plan integration** with taskpool — 3-5 days, highest strategic value
5. **Workspace snapshot** for always-on — 2-3 days, depends on #4

---

## 6. Anti-Drift Constraints

- Do NOT add TypeScript/Node.js dependencies to Hermes
- Do NOT require MCP for routing (Hermes routing is CLI-first)
- Keep judge model configurable (not hardcoded to one provider)
- Preserve ε-greedy fallback when judge is unavailable
- Cost tracking must be local-only (no external telemetry)
