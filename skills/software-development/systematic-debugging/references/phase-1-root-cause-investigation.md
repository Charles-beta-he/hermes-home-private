# Systematic Debugging Phase 1 Root Cause Investigation

Extracted from `/Users/charles/.hermes/skills/software-development/systematic-debugging/SKILL.md` on 2026-07-01T08:52:42.874486+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## Phase 1: Root Cause Investigation

**BEFORE attempting ANY fix:**

### 1. Read Error Messages Carefully

- Don't skip past errors or warnings
- They often contain the exact solution
- Read stack traces completely
- Note line numbers, file paths, error codes

**Action:** Use `read_file` on the relevant source files. Use `search_files` to find the error string in the codebase.

### 2. Reproduce Consistently

- Can you trigger it reliably?
- What are the exact steps?
- Does it happen every time?
- If not reproducible → gather more data, don't guess

**Action:** Use the `terminal` tool to run the failing test or trigger the bug:

```bash
# Run specific failing test
pytest tests/test_module.py::test_name -v

# Run with verbose output
pytest tests/test_module.py -v --tb=long
```

**Java/Spring Boot startup pitfalls:**
- After deleting or renaming controller/classes, `mvn package` may leave old `.class` files under `target/classes` and the repackaged jar can still fail with the same ambiguous mapping or bean conflict even though source search shows zero references. If a Spring Boot app still reports a deleted controller/mapping after source cleanup, verify with `jar tf ... | grep DeletedClass` and run `mvn clean package` before concluding the fix failed.
- In multi-module Maven repos, `mvn -pl app/<module> spring-boot:run` can fail because sibling reactor artifacts are not installed. Run `mvn -pl app/<module> -am -DskipTests install` first, then start the app module.
- Do not exclude an infrastructure auto-configuration just to get a local backend up if production beans constructor-require it (for example excluding RocketMQ auto-config while a controller requires `RocketMQTemplate`). That converts real-backend verification into a partial harness; either start/provide the real dependency or make the bean conditional in a proper test profile.
- In React/Vitest suites, many unrelated text/label failures can come from a shared i18next singleton, not from the components themselves. Symptom: expected English labels but rendered DOM is Chinese (or another prior test language). Reproduce one failure and inspect the DOM language first. Fix the test harness by adding the required resource bundle in `beforeEach` with overwrite/deep merge and `await i18next.changeLanguage('<lang>')`; do not rely on `if (!i18next.isInitialized) init(...)` alone, because earlier tests may already have initialized the singleton.
- Frontend release/version runtimes must separate pre-auth and authenticated surfaces. If a login/OTP/public auth page shows repeated 401s for a release-manifest endpoint, trace global hooks that run before auth. Pre-auth should read a static no-store artifact such as `/version.json` with `fetch(..., { cache: 'no-store', credentials: 'omit' })`; if protected release APIs are not proven login-safe, keep the whole browser runtime static-only instead of calling authenticated release endpoints after login. Verify with targeted Vitest plus build/build:release when the app generates version artifacts.
- Public auth pages can still 401 from unrelated global widgets even after release-runtime is fixed. Applicability: SPA shells with root-mounted widgets/hooks and token refresh interceptors. Anti-condition: do not apply to deliberately protected routes. If a public auth page shows an auth-expired business error, identify the request name first and audit root-mounted widgets whose hooks run before `if (hide) return null` (for example support/session widgets, bootstraps, or heartbeats). A stale local token can make hook-level “has token” guards fire protected endpoints, which then cascade into refresh. See `references/frontend-public-auth-stale-token-global-hooks.md`.
- Spring `Ambiguous mapping` errors are backend startup-contract bugs. If a legacy compatibility controller duplicates a canonical controller endpoint, keep the canonical route, remove/rename the duplicate compatibility mapping, and add a startup/contract test.
- If Flyway/MySQL reports `UndeclaredThrowableException` or fails around `performance_schema.user_variables_by_thread`, inspect any JDBC `DataSource`/`Connection`/`Statement` dynamic-proxy instrumentation. `Method.invoke(...)` wraps thrown `SQLException` in `InvocationTargetException`; an `InvocationHandler` must unwrap and rethrow the original cause, otherwise Flyway cannot catch `SQLException` and degrade capability probes correctly. Add a unit regression that a proxied `PreparedStatement.executeQuery()` rethrows the original `SQLException`, not `UndeclaredThrowableException`.
- A `Tomcat started on port ...` log line is not a Spring Boot readiness proof. The app can still fail during `ApplicationReadyEvent` listeners or seeders and immediately shut down. Treat startup as ready only after `Started <Application>` appears, the process remains alive, and `/actuator/health` (plus target smoke endpoints) returns 200/UP. If a post-ready seeder reports `Table '<schema>.<table>' doesn't exist`, check Flyway enablement/profile/schema before debugging controllers.
- Conversely, `mvn spring-boot:run` for a long-lived server reports Maven `BUILD FAILURE` when the tracked process is intentionally stopped by SIGTERM (`exit code 143`). Do not classify that as app startup failure if logs show `Started <Application>`, the app stayed alive, smoke endpoints were hit while alive, and shutdown appears under `ShutdownHook`. Record it as a manual/test-harness termination, not a failed boot.

See `references/spring-boot-real-backend-startup.md` for a concrete real-backend startup debugging checklist and error examples.

### 3. Check Recent Changes

- What changed that could cause this?
- Git diff, recent commits
- New dependencies, config changes
- **Deployment staleness**: If the code looks correct locally but the user reports a bug, check whether the deployed version matches local HEAD. A correct local fix that isn't deployed produces symptoms identical to a code bug. Check build timestamps, Railway/Vercel deployment logs, or `git log` vs production version before deep-diving backend types or data flow.

**Action:**

```bash
# Recent commits
git log --oneline -10

# Uncommitted changes
git diff

# Changes in specific file
git log -p --follow src/problematic_file.py | head -100
```

### 4. Gather Evidence in Multi-Component Systems

**WHEN system has multiple components (API → service → database, CI → build → deploy):**

**BEFORE proposing fixes, add diagnostic instrumentation:**

For EACH component boundary:
- Log what data enters the component
- Log what data exits the component
- Verify environment/config propagation
- Check state at each layer

Run once to gather evidence showing WHERE it breaks.
THEN analyze evidence to identify the failing component.
THEN investigate that specific component.

### 5. Trace Data Flow

**WHEN error is deep in the call stack:**

- Where does the bad value originate?
- What called this function with the bad value?
- Keep tracing upstream until you find the source
- Fix at the source, not at the symptom

**Action:** Use `search_files` to trace references:

```python
# Find where the function is called
search_files("function_name(", path="src/", file_glob="*.py")

# Find where the variable is set
search_files("variable_name\\s*=", path="src/", file_glob="*.py")
```

### 6. Trace Data Through Pipeline Boundaries (Multi-Component Systems)

**WHEN the data flows through a normalization → persistence → reconstruction → API replay pipeline:**

This is a common pattern in LLM agent frameworks. Data enters the system in one shape, gets transformed, stored to DB, loaded, transformed again, and sent to an API. **Each boundary can silently drop fields.**

**Map the full pipeline before picking a fix:**

```
API response → normalize_response() → [NormalizedResponse object] → _build_assistant_message() → dict
  → append_message() → SQLite → get_messages_as_conversation() → dict
  → _copy_reasoning_content_for_api() → api_messages dict → transport.build_kwargs() → API call
```

At EACH boundary, verify:
- **Inbound**: what fields does the input have? (use `print(list(input.keys()))` or `dir()`)
- **Outbound**: what fields does the output have?
- **Loss**: did any field disappear? Was it intentionally stripped?
- **Transformation**: did any field change type or format?

**Action:** Read EVERY file in the pipeline chain, following each function call. Focus on:

1. **`getattr(obj, field, None)` vs `hasattr(obj, field)`**
   - `hasattr` returns `True` for `@property` definitions even when the underlying data is missing
   - `getattr` returns the property's return value (which may be `None`)

2. **`if value:` vs `if value is not None:`**
   - `if value:` uses truthiness: empty string `""`, `0`, `[]`, `False` all fail the check
   - `if value is not None:` preserves the value even when it's falsy
   - This is the #1 cause of silent field loss at normalization boundaries

3. **Deep copy vs shallow copy** — `msg.copy()` (shallow) vs `copy.deepcopy(messages)` (deep). Nested dicts/lists in shallow copies share references with the original, so modifications to one affect the other — or vice versa when the same mutable object is reused.

4. **`if row["field"]:` vs `if row["field"] is not None:` in DB readback** — SQLite returns `""` for empty text fields and `None` for NULL. `if row["field"]:` treats both as falsy, silently dropping empty strings on round-trip.

5. **`msg.copy()` on dicts with complex nested objects** — Tool calls, function arguments, and provider_data all contain nested structures. A shallow copy means child objects are shared between source and destination — mutations in one path leak into the other. Use `copy.deepcopy` when the dict contains mutable children.

```python
# WRONG — shallow copy passes through None for missing keys
api_msg = msg.copy()
api_msg["reasoning_content"] = api_msg.get("reasoning_content")  # None if missing

# WRONG — truthiness check drops empty strings
if reasoning_content:
    provider_data["reasoning_content"] = reasoning_content

# RIGHT — explicit None check preserves empty strings
if reasoning_content is not None:
    provider_data["reasoning_content"] = reasoning_content
```

**Real example (DeepSeek reasoning_content loss, April 2026):**
```
Root cause: chat_completions.py:351 used `if reasoning_content:` instead of
`if reasoning_content is not None:`. Empty string `""` was silently dropped
from provider_data, never flowing into the stored msg dict.

Impact: DeepSeek's assistant messages lost reasoning_content on replay →
HTTP 400 on every turn after the first. Fallback retried with the same
broken schema → all retries failed → session never persisted.

Fix: One-line change — truthiness check → None check.
```

### 7. Cross-Reference With Upstream Repository

**WHEN working with a fork or open-source project that receives updates:**

BEFORE proposing a fix, check whether the bug is already known upstream. This avoids:
- Wasting time duplicating work
- Writing a fix that will be overwritten by `git pull` on next update
- Missing context from existing discussions (root cause analysis, edge cases, alternative approaches)

**Action:**

```bash
# Search GitHub issues with relevant keywords
open_browser -> https://github.com/<owner>/<repo>/issues?q=is%3Aissue+{keywords}
```

Sample keywords from common bug classes:
- `reasoning_content` + `400` — DeepSeek/Kimi thinking mode validation
- `think` + `stream` + `tag` — streaming reasoning tag display leaks
- `_clean_for_display` — gateway stream filtering
- `context_compressor` + `memory` — compression + memory interaction

**When you find a matching issue:**
- Note its status (Open/Closed/PR-linked)
- Check if a PR already exists with a fix
- Check if the fix has been merged — if so, `hermes update` will bring it
- If the fix is not yet merged, decide whether to patch locally or wait

### 8. Fix Sustainability Audit — Will This Survive `hermes update`?

**WHEN the fix touches files inside the hermes-agent repo (`~/.hermes/hermes-agent/`):**

Before writing any fix, map which files it affects against the update mechanism:

```
`hermes update` does git pull on ~/.hermes/hermes-agent/
→ Any file inside this directory WILL be overwritten on next update

Exempt files (NOT overwritten by update):
  ~/.hermes/config.yaml         — user config
  ~/.hermes/.env                — API keys
  ~/.hermes/memories/           — persistent memory
  ~/.hermes/skills/             — user skills
  ~/.hermes/scripts/            — user scripts
  ~/.hermes/cron/               — cron job data
```

**Three-layer fix strategy (ranked by sustainability):**

| Layer | Method | Survives update? | Effort |
|-------|--------|-----------------|--------|
| **User data** | Edit ~/.hermes/memories/MEMORY.md, config.yaml | ✅ Always | Low |
| **Monkey-patch** | Python runtime override at startup | ✅ Yes (inject from ~/.hermes/config.yaml or startup script) | Medium |
| **Vendor code** | Edit run_agent.py, cli.py, transport files in ~/.hermes/hermes-agent/ | ❌ Overwritten by git pull | Low (but ephemeral) |
| **PR upstream** | Submit fix to official repo, get merged | ✅ Once merged, future updates carry it | High |

**Prefer higher layers when possible. Document lower-layer fixes with git hooks.**

**For monkey-patching:**
```python
# Example: Patch ChatCompletionsTransport at startup
# Place in ~/.hermes/hermes-agent/hermes_cli/startup_patch.py
from agent.transports.chat_completions import ChatCompletionsTransport

_orig_normalize = ChatCompletionsTransport.normalize_response

def _patched_normalize(self, response, **kwargs):
    result = _orig_normalize(self, response, **kwargs)
    # Fix: preserve empty string reasoning_content
    if hasattr(response, 'choices') and response.choices:
        msg_rc = getattr(response.choices[0].message, 'reasoning_content', None)
        if msg_rc is not None:
            pd = result.provider_data or {}
            pd['reasoning_content'] = msg_rc
            object.__setattr__(result, 'provider_data', pd)
    return result

ChatCompletionsTransport.normalize_response = _patched_normalize
```

**For git hooks (auto-reapply patches after update):**
```bash
# ~/.hermes/hermes-agent/.git/hooks/post-merge
#!/bin/sh
# Auto-apply local patches after git pull
git diff --quiet HEAD -- agent/transports/chat_completions.py || exit 0
# Apply patch if not already present
cd "$(git rev-parse --show-toplevel)"
grep -q "is not None" agent/transports/chat_completions.py || \
  sed -i '' 's/if reasoning_content:/if reasoning_content is not None:/' \
    agent/transports/chat_completions.py
```

### 9. Ghost Memory Detection (Context-Compression-Aware)

**WHEN analyzing issues related to persistent memory and context compression:**

Past-tense entries in persistent memory survive context compression and get re-injected as current facts. This is a common source of confusion in agent systems.

**Check for ghosts in `~/.hermes/memories/MEMORY.md`:**

| Ghost Pattern | Example | Why It's Dangerous |
|--------------|---------|-------------------|
| **Past-tense completion summary** | "三轮审查修复10个问题，最终达到无改进状态" | Future sessions treat this as current state |
| **Version number** | "v1.4.8" | Becomes stale as project evolves |
| **Past progress** | "Discover 页面 + BottomNav 已上线" | Pages may have been modified/removed |
| **Redundant entries** | Same project described twice | Wastes limited memory budget (2,200 chars) |

**Detection heuristic:**
```python
# A memory entry is a ghost if it answers "Was this task COMPLETED?"
# rather than "Is this fact STILL TRUE?"
#
# Linguistic markers:
# - Past tense (完成/上线/修复了/was/implemented/done)
# - Completion quantifiers (三轮/10个/全部)
# - Version numbers (v1.4.x)
# - Session-local progress (not system architecture)
```

**Fix:**
- Remove ghost entries from MEMORY.md
- Keep only architecturally durable facts (project structure, tool conventions, user preferences)
- Duplicates → merge into single entry

### 10. Automation Escalation Audit — Run Local Gates Before Spawning Broader Workers

**WHEN debugging multi-stage automation (review auto-close, blocked resolvers, ratification loops, retry daemons, certification workers):**

A common failure mode is to escalate too early. The orchestrator sees a broad signal like `multimodel_required`, `intervention_required`, or `needs_review`, immediately spawns a heavier worker, and accidentally bypasses the task's own deterministic gate. That creates false outcomes such as task-mismatch skips, unnecessary retries, or global workers certifying the wrong task.

**Audit order:**
1. Compute the task-local evidence first.
2. Probe the normal gate for the exact transition being attempted.
3. Only escalate if the local gate still fails **and** the failures are in the escalation domain.
4. Narrow escalation by lane/domain instead of using a global boolean alone.

**Heuristic:**
- If the failure is ordinary lane proof debt (`missing build/test/browser/curl/project evidence`), keep it in the normal gate path and return `skip` / `blocked` / `retry` there.
- If the failure is specifically about ratification or multimodel certification, then spawn the broader worker.
- For taskpool orchestration, treat `review -> done` as the base path and PUA-loop/certification as the fallback path, not the default.

**Real pattern (Hermes taskpool, May 2026):**
- Symptom: `auto-close-review` marked a normal work-lane review task as `certification_triggered_skip` with `certification_task_mismatch`.
- Root cause: the command triggered multimodel certification before checking whether the normal `done` gate was simply failing for missing project evidence.
- Durable fix: run `lifecycle_gate(..., "done", ...)` first, then trigger certification only when the remaining failures are actually ratification/multimodel-related or the lane is explicitly evolution/advisory/mission-envelope.

### 11. Multi-Loop Convergence — Iterate Until No Issues Remain

**WHEN fixing multiple bugs in a single session:**

```
Fix → Re-check → Fix → Re-check → ... until 0 issues
```

Track progress with a structured todo list. Each loop iteration:
1. Fix the highest-priority remaining issue
2. Run the self-check
3. If new issues found, add them to the todo list
4. Stop when only time-dependent items remain

**Convergence signal:** All checks pass or are explicitly labeled as time-dependent.

### 11. Claim-Validation Audit — Verify System Weakness Claims Against Source Code

**WHEN presented with a list of system weaknesses or "known issues" (from documentation, issue reports, or analysis):**

BEFORE accepting any claim as true:
1. **Read the actual source code** — do not rely on documentation or reputation
2. **Categorize each claim** using a systematic framework:

```python
def audit_claim(claim, source_code):
    """
    Categories:
    ✅ TRUE:       Claim accurately describes a real weakness
    ⚠️ PARTIAL:    Claim is directionally correct but mitigations exist
    ❌ FALSE:      Claim is wrong — the code doesn't match the description
    """
```

3. **For each claim, produce evidence:**

```
| Claim: "MCP stdio lacks chunking → deadlock"
| Reading: mcp_tool.py:1053 async with stdio_client(...)
| Finding: ⚠️ PARTIAL — asyncio streams don't block, but large payloads
|           can time out. 300s read timeout mitigates permanent deadlock.
| Verdict: Theory risk exists, but has timeout guardrails.
```

**Real example (Apr 2026 MCP 7-claim audit):**
```
Out of 7 claims:
  ✅ 4 real:     memory noise, error solidification, learning loop, OAuth no heartbeat
  ⚠️ 2 partial:  stdio blocking (has timeout), context overflow (has compression)
  ⚠️ 1 limited:  MemoryManager dirty instance (doesn't cause global deadlock)
```

**Why this matters:** Accepting false claims leads to unnecessary fixes that waste time and add complexity. Validating against source code is the only reliable way to separate real bugs from design tradeoffs.

### Phase 1 Completion Checklist

- [ ] Error messages fully read and understood
- [ ] Issue reproduced consistently
- [ ] Recent changes identified and reviewed
- [ ] Evidence gathered (logs, state, data flow)
- [ ] Problem isolated to specific component/code
- [ ] Root cause hypothesis formed
- [ ] Claim validated against source code (if third-party claim)
- [ ] Upstream repository cross-referenced (if related)

**STOP:** Do not proceed to Phase 2 until you understand WHY it's happening.

---
