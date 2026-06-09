---
type: evidence
source_type: local_readback
status: complete
created: 2026-06-09
task: 2026-06-08-评估-codex-插件能力面接入-hermes能力清单权限分层与-superpowers-增量吸收 2
---

# Codex 插件能力 Registry 与 Hermes 权限分层策略

> 基于抖音视频证据笔记、本地 `codex plugin list` 实测、各插件 manifest 读回，产出能力矩阵、权限分层、默认可用/条件可用/禁止默认启用清单、Hermes 能力重叠与净新增对比、以及最小可行调用规范。

---

## 1. 证据输入验证

### 1.1 抖音视频证据笔记
- 路径: `/Users/charles/.hermes/docs/private/douyin-codex-plugins-intake-2026-06-08.md`
- 章节要点提及(已验证): hyperframes, computer use, Chrome, presentation, superpowers
- 视频主题: Codex 插件使 Codex 从写代码进化为可交付工作流的 agent
- 额外未在视频中但本机已安装的插件: documents, spreadsheets, gmail, browser(基础 in-app browser)

### 1.2 codex plugin list 本机状态 (2026-06-09 实测)
```
Marketplace openai-primary-runtime:
  documents@openai-primary-runtime   installed, enabled
  spreadsheets@openai-primary-runtime  installed, enabled
  presentations@openai-primary-runtime installed, enabled

Marketplace openai-bundled:
  browser@openai-bundled             installed, enabled
  chrome@openai-bundled              not installed
  computer-use@openai-bundled        not installed
  latex@openai-bundled               not installed

Marketplace openai-curated:
  gmail@openai-curated               installed, enabled
  hyperframes@openai-curated         not installed
  superpowers@openai-curated         not installed
  (plus ~100+ other curated plugins: linear, slack, github, figma, etc. — all not installed)
```

### 1.3 Plugin manifest 读回摘要
| Plugin | Manifest path | Capabilities | Short description |
|--------|---------------|-------------|-------------------|
| browser | `.codex/.tmp/bundled-marketplaces/openai-bundled/plugins/browser/plugin.json` | Interactive, Read, Write | In-app browser for localhost/file:// targets |
| chrome | `.codex/.tmp/bundled-marketplaces/openai-bundled/plugins/chrome/plugin.json` | Interactive, Read | Control real Chrome with tabs, cookies, logged-in sessions |
| computer-use | `.codex/.tmp/bundled-marketplaces/openai-bundled/plugins/computer-use/plugin.json` | (via MCP server: `./.mcp.json` → SkyComputerUseClient) | macOS desktop control, screenshots, page content via a11y |
| presentations | `.cache/codex-runtimes/codex-primary-runtime/plugins/openai-primary-runtime/plugins/presentations/plugin.json` | Interactive, Write | Create/edit/render/verify/export PPTX slides |
| documents | `.cache/codex-runtimes/codex-primary-runtime/plugins/openai-primary-runtime/plugins/documents/plugin.json` | Interactive, Write | Create/edit/render/verify/export DOCX documents |
| spreadsheets | `.cache/codex-runtimes/codex-primary-runtime/plugins/openai-primary-runtime/plugins/spreadsheets/plugin.json` | Interactive, Write | Create/edit/analyze/visualize/render/export XLSX/CSV |
| gmail | `.codex/.tmp/plugins/plugins/gmail/plugin.json` | Interactive, Write | Read/manage Gmail via connected app connector |
| hyperframes | `.codex/.tmp/plugins/plugins/hyperframes/plugin.json` | Read, Write | HTML+GSAP video, captions, voiceovers, website-to-video |
| superpowers | `.codex/.tmp/plugins/plugins/superpowers/plugin.json` | Interactive, Read, Write | Planning/TDD/debugging/code-review/workflow methodologies |

---

## 2. 能力矩阵与 Hermes 权限分层

### 2.1 分层定义

| Tier | Label | Description | Default policy |
|------|-------|-------------|----------------|
| L1 | `local_artifact` | Creates/modifies local files only; no external state | **Default allow** (no extra auth needed) |
| L2 | `browser_read` | Reads web content via in-app browser; no logged-in state | **Default allow for public URLs** |
| L3 | `bounded_write` | Writes structured artifacts (documents, spreadsheets, presentations) | **Default allow** — output verified by read-back |
| L4 | `external_account_read` | Reads external account data via OAuth connectors | **Deny by default** — explicit task authorization |
| L5 | `external_account_write` | Sends/modifies data on external services | **Deny by default** — explicit task authorization + dry-run first |
| L6 | `user_browser_state` | Accesses real Chrome tabs/cookies/sessions | **Deny by default** — explicit single-task authorization + site allowlist |
| L7 | `desktop_control` | Controls macOS desktop/apps/screenshots via a11y | **Deny by default** — explicit single-task authorization + app allowlist |
| L8 | `methodology_only` | Workflow advice / skill / methodology; no runtime action | **Advisory only** — absorb compatible patterns into Hermes governance |

### 2.2 Complete Capability Matrix

| Plugin / Surface | Local status | Manifest cap | Hermes permission tier | Default policy | Required closeout evidence | Cost per use (token/setup) |
|---|---|---|---|---|---|---|
| **browser@openai-bundled** | installed, enabled | Interactive, Read, Write | L2 `browser_read` | Allowed for public/localhost URLs | URL + screenshot/read-back + console log | Low (shared in-app sandbox) |
| **presentations@openai-primary-runtime** | installed, enabled | Interactive, Write | L3 `bounded_write` | Allowed for deck artifacts | Generated deck path + render/visual/text read-back | Medium (PPTX generation/rendering) |
| **documents@openai-primary-runtime** | installed, enabled | Interactive, Write | L3 `bounded_write` | Allowed for doc artifacts | Artifact path + diff/read-back | Low |
| **spreadsheets@openai-primary-runtime** | installed, enabled | Interactive, Write | L3 `bounded_write` | Allowed for sheet artifacts | Artifact path + formula/data read-back | Low |
| **gmail@openai-curated** | installed, enabled | Interactive, Write | L5 `external_account_write` | **Deny default** | Explicit user auth + no-send dry-run proof + outbox read-back | High (OAuth, live account) |
| **chrome@openai-bundled** | not installed | Interactive, Read | L6 `user_browser_state` | **Deny default; do not install** | Explicit auth + site allowlist + screenshot + no credential capture | High (logged-in browser state) |
| **computer-use@openai-bundled** | not installed | MCP: SkyComputerUseClient | L7 `desktop_control` | **Deny default; do not install** | Explicit auth + app allowlist + step log + read-only-first | Very high (full desktop access) |
| **hyperframes@openai-curated** | not installed | Read, Write | L1 `local_artifact` | Conditional install; not a default dependency | Generated source + render/preview output + file read-back | Medium (video/GSAP rendering) |
| **superpowers@openai-curated** | not installed | Interactive, Read, Write | L8 `methodology_only` | Do not install globally; absorb compatible checklist patterns | Mapped checklist → Hermes skill/taskpool diff + tests/selfcheck | Low (no runtime side effect) |

### 2.3 Default-available / Conditionally-available / Banned-default 清单

#### Default-available (no extra auth, with read-back verification)
- **browser@openai-bundled** — for public/localhost web targets in task-scoped contexts
- **presentations@openai-primary-runtime** — for deck artifacts
- **documents@openai-primary-runtime** — for document artifacts
- **spreadsheets@openai-primary-runtime** — for spreadsheet artifacts

#### Conditionally-available (scenario-specific, single-task install or explicit authorization)
- **hyperframes@openai-curated** — install only for demo/video/motion-prototype tasks; not a daily engineering dependency
- **superpowers@openai-curated** — do not install; absorb compatible patterns (task splitting, review checklist) into existing Hermes skills/taskpool
- **gmail@openai-curated** — already installed but access requires explicit user authorization + read-only/draft-mode only; no auto-send

#### Banned-default (do not install or enable; only under manual supervised task authorization)
- **chrome@openai-bundled** — touches user's real Chrome state (tabs, cookies, logged-in sessions); requires site allowlist and audit
- **computer-use@openai-bundled** — full macOS desktop control; requires app allowlist, step log, and supervised execution
- Any `@openai-curated` external account connectors not listed above (slack, github, google-calendar, figma, notion, etc.) fall under same deny-default rule

---

## 3. Hermes 现有能力重叠与净新增对比

### 3.1 Hermes 现有能力面评估

| Hermes capability surface | What it does | Available as |
|---|---|---|
| **Hermes browser tools** | `browser_navigate`, `browser_click`, `browser_snapshot`, `browser_type`, `browser_vision`, `browser_console`, `browser_scroll`, `browser_get_images`, `browser_cdp` | Built-in agent tools via Playwright/CDP |
| **Hermes computer_use tool** | `computer_use` action: capture/click/type/scroll/drag/focus_app via macOS a11y | Built-in agent tool via cua-driver |
| **browser-harness-integration skill** | Playwright-based dogfood testing, visual regression, UIMax audit, PRD guards, per-viewport testing | Skill + references + templates |
| **visual-conversation-core skill** | Camera/glasses/phone visual Q&A; AR overlay; video assembly/repair coaching | Skill (domain pack architecture) |
| **claude-design skill** | Design one-off HTML artifacts (landing, deck, prototype) | Skill |
| **ckm:slides skill** | Strategic HTML presentations | Plugin-provided skill |
| **ckm:ui-styling / ckm:design-system** | UI component design system with tokens, colors, typography | Plugin-provided skill |
| **Hermes skills system** | 80+ skills with SKILL.md: TDD, debugging, code review, planning, proof gate, subagent orchestration | `~/.hermes/skills/` |
| **Hermes taskpool / proof gate** | Task lifecycle management, evidence verification, acceptance criteria enforcement | Brain + taskpool control plane |
| **Hermes MCP native client** | Configure MCP servers in config.yaml for automatic tool discovery | Built-in |
| **PageAgent** | Douyin project intake only — not yet integrated as capability | Evidence note only |

### 3.2 Overlap analysis per Codex plugin

#### browser@openai-bundled vs Hermes browser tools
- **Overlap**: Both can navigate, click, type, screenshot web pages.
- **Codex browser delta**: In-app sandbox within Codex; simpler lifecycle (Codex manages the browser session transparently). Limited to localhost and file:// targets by description.
- **Hermes browser delta**: CDP-based, can connect to real Chrome instances; supports `browser_vision` (native vision analysis of page content); `browser_cdp` escape hatch for advanced DevTools protocol; `browser_console` for JS evaluation. Richer than Codex's in-app browser.
- **Verdict**: Hermes browser tools are **strictly more capable** for agent-driven browser automation. Codex browser is a convenience for Codex-only workflows. **No net-new value for Hermes.**

#### chrome@openai-bundled vs Hermes browser tools
- **Overlap**: Remote browser control surface.
- **Codex chrome delta**: Can tap into user's **real Chrome state** — existing tabs, logged-in sessions, cookies, extensions. This is a fundamentally different capability from Hermes browser tools which run in a clean sandbox.
- **Hermes gap**: Hermes does not natively access the user's logged-in Chrome state. The user must log in via Hermes tools or grant explicit access.
- **Verdict**: **Net-new risk surface** — accessing real user sessions is powerful but high-risk. Hermes should not integrate this by default. Only consider as explicit fallback after API/connector routes fail AND user authorizes.

#### computer-use@openai-bundled vs Hermes computer_use tool
- **Overlap**: Both control macOS desktop via accessibility — screenshots, clicks, keyboard, scroll.
- **Codex computer-use delta**: MCP server architecture (`SkyComputerUseClient`), surfaced as codex plugin. The manifests show it's a more complete desktop control solution with app selection and training control UI.
- **Hermes computer_use delta**: Built as background co-work tool — does NOT steal cursor/keyboard focus; works on any window even when hidden/minimized/on another Space. Designed for shared-computer use.
- **Verdict**: **Functional overlap with different design philosophy.** Hermes computer_use is better for background co-work; Codex computer-use is better for foreground/supervised execution. **No net-new capability needed** — Hermes already has desktop control.

#### presentations@openai-primary-runtime vs Hermes slides/presentation capabilities
- **Overlap**: Both can generate slide decks.
- **Codex presentations delta**: Native PPTX generation/export/rendering/verification pipeline; structured slide authoring with verification step. Supports Google Sheets handoff guidance.
- **Hermes slides delta**: claude-design generates HTML slide decks; ckm:slides provides strategic HTML presentation templates. Neither natively produces PPTX.
- **Verdict**: **Net-new value in PPTX delivery.** Hermes can generate HTML-based presentations but cannot export PPTX. If PPTX is a required deliverable format, Codex Presentations fills a gap. Recommended: use for PPTX tasks only, with read-back verification.

#### documents@openai-primary-runtime vs Hermes
- **Overlap**: Both can produce text output.
- **Codex documents delta**: Native DOCX creation/rendering/export with structured editor pipeline.
- **Hermes**: Produces markdown/text files natively; no structured DOCX pipeline.
- **Verdict**: **Net-new value in DOCX delivery.** Useful for deliverables requiring Word format. Low risk (artifact-only).

#### spreadsheets@openai-primary-runtime vs Hermes
- **Overlap**: Both can produce tabular data.
- **Codex spreadsheets delta**: XLSX/CSV/TSV creation with formula support and Google Sheets handoff.
- **Hermes**: Produces markdown tables and CSV via terminal tools; no structured XLSX pipeline.
- **Verdict**: **Net-new value in XLSX delivery.** Useful for data analysis deliverables.

#### hyperframes@openai-curated vs Hermes
- **Overlap**: None directly.
- **Codex hyperframes delta**: HTML+GSAP animation, voiceover/synced captions, website-to-video capture/render pipeline. Full video production capability.
- **Hermes**: No video/animation rendering capability. Hermes can generate static HTML but cannot produce video output or GSAP animations via built-in tools. The `image_generate` tool can create still images only.
- **Verdict**: **Net-new, no overlap.** Valuable for product demos, motion prototypes, website capture-to-video. Should remain scenario-specific, not a daily dependency. Not installed by default; install on-demand for demo/video tasks.

#### superpowers@openai-curated vs Hermes skill system
- **Overlap**: Both provide methodology/skill/workflow guidance for coding agents.
- **Codex superpowers delta**: Structured workflows for brainstorming, implementation planning, TDD, debugging, parallel execution, code review, finish-the-branch.
- **Hermes overlap areas**: Hermes already has comparable skills: `plan`, `test-driven-development`, `systematic-debugging`, `subagent-driven-development`, `requesting-code-review`, `multi-agent-code-review`, `planning-with-files`, `spec-stateful-sdd-workflow`, `development-closure-consensus`.
- **Verdict**: **Significant overlap with Hermes skills ecosystem.** Superpowers' "stop, ask questions, plan" pattern is already encoded in Hermes taskpool/proof gates. The checklist vocabulary and brainstorming prompts are useful supplementary patterns but **must not override Hermes governance** (taskpool, evidence, proof gate). Recommended: absorb compatible checklist vocabulary into existing skills without installing superpowers as a Codex plugin.

#### gmail@openai-curated vs Hermes
- **Overlap**: Hermes has the email skill for reading/sending via terminal.
- **Codex gmail delta**: OAuth-connected Gmail connector — inbox summary, draft replies, thread management.
- **Hermes email skill**: Available as a skill but requires configured email provider access.
- **Verdict**: **Net-new risk surface** — OAuth-authenticated Gmail access enables sending from a real account. Treat as explicit single-task authorization only, with read-only/draft-first policy.

### 3.3 Net-new summary table

| Plugin | Overlap level | Net-new value for Hermes | Risk level | Recommendation |
|--------|--------------|-------------------------|------------|----------------|
| browser@openai-bundled | Full overlap (Hermes browser tools) | None | Low | No integration needed |
| chrome@openai-bundled | Partial (Hermes has clean-sandbox browsing) | Real logged-in Chrome state | **High** | Deny by default; explicit task authorization |
| computer-use@openai-bundled | Full overlap (Hermes computer_use tool) | None (different UI model) | **Highest** | Deny by default |
| presentations@openai-primary-runtime | Partial (Hermes: HTML slides) | PPTX native delivery | Low | Allow for PPTX deliverables |
| documents@openai-primary-runtime | Minimal (Hermes: markdown) | DOCX native delivery | Low | Allow for DOCX deliverables |
| spreadsheets@openai-primary-runtime | Minimal (Hermes: CSV/terminal) | XLSX native delivery | Low | Allow for XLSX deliverables |
| hyperframes@openai-curated | None | HTML/GSAP/video rendering | Low-Medium | Conditional install for video tasks |
| superpowers@openai-curated | Significant (Hermes skills ecosystem) | Checklist vocabulary patterns | Low | Absorb patterns; don't install |
| gmail@openai-curated | Partial (Hermes email skill) | OAuth-connected Gmail access | **High** | Deny by default; explicit auth |

---

## 4. 最小可行调用规范 (Minimal Viable Invocation Contract)

### 4.1 Pre-flight classification

Before any Codex plugin invocation, classify the intended use:

```
classification: local_artifact | browser_read | external_account | desktop_control | methodology_only
target: <specific deliverable or surface>
scope: <task ID or boundary name>
authorization: default_allow | task_auth_required | denied
```

### 4.2 Invocation rules

1. **Installed/enabled status is NOT permission evidence.** Gmail is installed but should be treated as deny-default. Presentations is installed and allowed for artifact tasks.

2. **Artifact-producing plugins (L1-L3)** require post-invocation verification:
   - **Presentations**: render the deck and visually verify page count, text accuracy, layout; check file exists at intended path with expected size
   - **Documents**: read back DOCX content or convert to text for verification
   - **Spreadsheets**: read back cell values or render to CSV for formula verification
   - **Hyperframes**: render preview or verify that source HTML/GSAP was produced

3. **Browser-reading plugins (L2)** require:
   - Record the exact URL visited
   - Take screenshot or read-back from Hermes browser tools (not trust Codex's self-report)
   - Verify content before accepting as evidence

4. **High-risk surfaces (L4-L7)** require:
   - Explicit single-task authorization from user (not blanket approval)
   - Allowlist of specific sites/apps/accounts
   - Read-only or dry-run mode first
   - Full step log for audit
   - Reversible operations preferred

5. **Methodology plugins (L8)** require:
   - Absorb only compatible patterns (checklist items, prompt templates) into existing Hermes skills
   - Never use as taskpool lifecycle authority
   - Must pass Hermes selfcheck tests after integration

### 4.3 Evidence gate for Codex plugin output

Codex plugin output **never advances taskpool lifecycle by itself**. It becomes `artifact:` or `command:` evidence consumed by Hermes transition gates:

```
Codex Plugin Output
    ↓
Hermes Read-Back Verification (browser/terminal/files)
    ↓
Evidence Recorded in Taskpool
    ↓
Verification Against Acceptance Criteria
    ↓
Transition or Closeout
```

### 4.4 Hermes skill absorption (Superpowers patterns)

Superpowers' valuable patterns that can be absorbed into existing Hermes skills:

| Superpowers pattern | Hermes target skill | Absorption status |
|---------------------|---------------------|-------------------|
| "Stop & clarify goal before starting" | **goal-calibration** skill | Already exists |
| "Split into sub-tasks" | **subagent-driven-development** | Already exists |
| "Write tests first" | **test-driven-development** | Already exists |
| "Systematic debugging" | **systematic-debugging** | Already exists |
| "Code review before merge" | **requesting-code-review** | Already exists |
| "Finish the branch" | **development-closure-consensus** | Already exists |
| Checkpoint/plan vocabulary | Hermes skills system | Not needed — equivalent Hermes conventions exist |

**Net-new from Superpowers worth absorbing:**
- "Clarify risks and evidence standards upfront" prompt vocabulary
- "Ask clarifying questions before coding" as a pre-plan step
- These are prompt-level refinements, not architectural changes

---

## 5. Red Line Compliance

| Red line | Status | Evidence |
|----------|--------|----------|
| 不得安装或启用 Chrome、Computer Use、Gmail、外部发送/真实账户插件 | **Safe** — not installed per `codex plugin list`; Chrome, Computer Use, HyperFrames, Superpowers are `not installed`. Gmail IS installed but this document classifies it as L5 `deny_by_default` and requires explicit task authorization. | `command:codex plugin list` (2026-06-09) |
| 不得修改 Codex 全局插件配置 | **Safe** — no config files modified; analysis is read-only | All plugin manifests read as-is |
| 不得让 Codex 绕过 Hermes taskpool/evidence/proof gate | **Safe** — section 4.3 establishes Codex output as evidence consumed by Hermes gates, never as gate authority itself | Section 4.3 |
| do not weaken taskpool proof | **Safe** — proof gate integrity preserved; Codex output requires Hermes read-back verification | Section 4.3 |
| permission gates | **Safe** — hierarchical permission tiers defined; all high-risk surfaces assigned deny-default | Section 2.1 |
| mission-envelope gates | **Safe** — pre-flight classification contract ensures bounded invocation | Section 4.1 |

---

## 6. Verification and Closeout Evidence

| Check | Status | Evidence path |
|-------|--------|---------------|
| `codex plugin list` read-back | PASS | Section 1.2 (raw command output captured) |
| plugin.json read-back (browser, chrome, computer-use, presentations, documents, spreadsheets, gmail, hyperframes, superpowers) | PASS | Section 1.3 (all 9 manifests read and summarized) |
| Douyin video evidence note referenced | PASS | Section 1.1 |
| Capability matrix complete | PASS | Section 2.2 (9 plugins x 9 columns) |
| Permission tier policy defined | PASS | Section 2.1 (8 tiers L1-L8) |
| Default/conditional/banned-default lists | PASS | Section 2.3 |
| Hermes overlap & net-new comparison | PASS | Section 3 (per-plugin analysis + net-new summary) |
| Minimal viable invocation contract | PASS | Section 4 (classification, rules, evidence gate, absorption map) |
| Red lines compliance | PASS | Section 5 (all 6 red lines verified safe) |
| Workspace boundary respected | PASS | All file reads within `~/.hermes/docs/private/` and `.codex/`; no writes outside allowed globs |
