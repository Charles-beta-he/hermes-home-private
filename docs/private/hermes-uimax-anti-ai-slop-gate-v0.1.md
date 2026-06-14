# Hermes UIMax anti-AI-slop gate v0.1

Task: `2026-06-14-impeccable吸收-ai-ui-反土味检测到-hermes-uimax-视觉品味门禁`
Generated: 2026-06-14 by Hermes follow-through executor
Status: implementation-ready design artifact; no third-party install, no hook/config writes, no project UI mutation.

## Evidence read-back

1. Local intake note read: `/Users/charles/.hermes/docs/private/douyin-ui-quality-tool-7650419412096355626/intake-analysis.md`.
   - It maps the Douyin lead to canonical repo `pbakaus/impeccable` and records the problem class: AI UI can pass functionally but feel generic/土 and hard to name.
   - It records Impeccable facts: design guidance for AI coding agents, `PRODUCT.md`/`DESIGN.md` context, command vocabulary, and detector CLI examples.
2. Live GitHub/API read-back performed against `https://api.github.com/repos/pbakaus/impeccable` and raw `README.md`/`package.json`.
   - Repo: `pbakaus/impeccable`; description: “The design language that makes your AI harness better at design.”
   - Live metadata at read-back: Apache-2.0, JavaScript, default branch `main`, stars `38108`, forks `2099`, open issues `31`, pushed `2026-06-14T05:19:15Z`.
   - `package.json`: npm package `impeccable`, version `2.3.2`, Node `>=24`, CLI bin `impeccable`.
   - README: “1 skill, 23 commands, live browser iteration, and 41 deterministic detector rules”; detector examples include `npx impeccable detect --fast --json .`.
3. Current Hermes UIMax read-back: `/Users/charles/.hermes/skills/software-development/uimax-audit/SKILL.md`.
   - Existing UIMax dimensions: Visual Design, Responsiveness, Accessibility, Code Quality, Interaction, Console Health.
   - Existing acceptance rule: UIMax scoring is secondary to flow truth; browser flow completion must not be replaced by polished screenshots.

## Fit decision

Absorb Impeccable as a **reference taxonomy and optional read-only detector**, not as an installed skill/hook. The immediate Hermes value is a seventh UIMax sub-dimension named `anti_ai_slop` that turns “界面很土但说不出原因” into named findings with evidence and repair advice.

Do not auto-install `npx impeccable skills install`, because that can write harness skill directories and provider-native hook manifests. The safe default is taxonomy-first and detector-optional.

## Proposed UIMax scoring extension

Add `anti_ai_slop` as a subcheck under Visual Design, and optionally surface it as a separate row when UI work is taste-sensitive.

| Dimension | Existing role | New anti-slop addition | Pass threshold |
|---|---|---|---|
| Visual Design | layout, spacing, typography, color, hierarchy | named slop findings with screenshot/code evidence | no P0/P1 generic-pattern findings without justified brand exception |
| Responsiveness | 375px and 1280px+ behavior | slop must be checked per viewport because cramped padding/touch target failures can be viewport-specific | mobile and desktop both reviewed |
| Accessibility | ARIA, focus, contrast, keyboard | detector findings cannot override WCAG/a11y flow proof | a11y remains hard gate |
| Code Quality | inline styles, CSS vars, hardcoded colors | code-pattern evidence for palette/font/card/tokens issues | code evidence attached when available |
| Interaction | animation/feedback/reduced-motion | bounce/elastic/glow/overdrive flagged unless intentional | motion purpose stated |
| Console Health | JS errors/API failures | unchanged | zero JS errors |
| `anti_ai_slop` | new named taste gate | generic SaaS/AI template tells, copy clichés, weak hierarchy, mechanical cards/gradients | finding -> evidence -> why bad -> repair |

## `anti_ai_slop` taxonomy for Hermes

Initial finding families adapted from Impeccable README/intake plus current UIMax language:

1. **Generic SaaS template tells**: purple-to-blue gradients, rounded-square icon tile above every heading, hero eyebrow/pill chip, repeated section kicker labels, oversized H1 without hierarchy.
2. **Typography slop**: Inter/system-default everywhere without brand reason, single font for all roles, flat type hierarchy, bad line length, tiny body text, excessive tracking, italic serif display headline as decoration.
3. **Color slop**: gray text on colored backgrounds, pure black/gray with no tint, cream/beige default palette, dark mode with glowing accents, gradient text used as a substitute for hierarchy.
4. **Layout/card slop**: cards nested in cards, monotonous spacing, cramped padding, flush-to-border content, side-tab accent borders, border accents on rounded elements.
5. **Motion/interaction slop**: bounce/elastic easing, motion without product purpose, hover effects that do not communicate state, small touch targets.
6. **Copy slop**: marketing buzzwords, aphoristic cadence, em-dash overuse, generic “Transform your workflow” language, unclear UX labels.
7. **Brand-context mismatch**: a rule only fails when it conflicts with the project’s PRODUCT/DESIGN context; intentional brand choices are allowed if documented.

## Required finding output format

Every anti-slop issue should be reported as:

```yaml
anti_ai_slop_findings:
  - id: typography.flat_hierarchy
    severity: P1
    surface: SettingsPage / mobile 375px
    evidence:
      screenshot: artifacts/uimax/settings-mobile.png
      code: src/pages/Settings.tsx:88-132
      detector: optional/impeccable-detect.json#rule=flat-type-hierarchy
    why_it_feels_bad: "Everything has the same visual weight, so the page looks like a generated settings template instead of a deliberate product surface."
    repair: "Introduce one dominant page title, one secondary section rhythm, and reduce card nesting; bind sizes to product typography tokens."
    brand_exception: null
```

For chat-facing responses to “这个界面丑但说不出来哪里丑”, use the compact form:

1. **命名问题**：e.g. “卡片套卡片 + 紫蓝渐变模板味”。
2. **证据**：screenshot region, DOM/CSS/code line, or detector JSON rule.
3. **为什么土**：connect to hierarchy, brand mismatch, visual rhythm, interaction, or copy cliché.
4. **怎么修**：one concrete, localized repair before broad redesign.
5. **保留项**：what is intentionally kept because it matches product/brand.

## Optional read-only detector integration gate

Detector use is allowed only when all conditions pass:

```text
if project_has_node >= 24
and user/project explicitly allows npm package execution
and command is read-only detector mode
and no skills install/update/link command is invoked
then run: npx --yes impeccable@2.3.2 detect --fast --json <target>
else use taxonomy-only manual UIMax audit
```

Allowed detector commands:

```bash
npx --yes impeccable@2.3.2 detect --fast --json .
npx --yes impeccable@2.3.2 detect --fast --json src/
npx --yes impeccable@2.3.2 detect --fast --json index.html
```

Forbidden without explicit human authorization:

```bash
npx impeccable skills install
npx impeccable skills update
npx impeccable skills link
/impeccable init  # when it would write PRODUCT.md / DESIGN.md in a project
any command that writes .claude/.cursor/.codex/.gemini/hooks or project files
```

Detector JSON is evidence, not authority. A finding is actionable only after UIMax ties it to screenshot/code/read-back and product context.

## PRODUCT/DESIGN context packet for Hermes UI work

Before generating or evaluating UI, collect this lightweight context packet. It mirrors Impeccable’s `PRODUCT.md`/`DESIGN.md` idea but remains Hermes-native and can live in task evidence or project profile.

```yaml
ui_context_packet:
  product_lane: product | brand | internal_tool | data_dashboard | consumer_app
  audience: "who uses it, skill level, locale"
  primary_job: "one sentence user outcome"
  emotional_target: "calm / premium / playful / operational / serious / ..."
  anti_references:
    - "what the UI must not feel like"
  brand_tokens:
    colors: []
    typography: []
    density: compact | normal | spacious
    motion: none | subtle | expressive
  existing_design_sources:
    product_doc: null
    screenshots: []
    component_library: null
  allowed_exceptions:
    - "e.g. dark glow allowed for cyberpunk cockpit, but must pass contrast"
```

## Implementation path after this artifact

1. **No-write current tranche (this artifact)**: keep task at review with artifact evidence if lifecycle gate accepts it.
2. **Future code/skill tranche**: add a section to `uimax-audit/SKILL.md` or a companion reference that references this artifact, but only after explicit authority to mutate active skills.
3. **Future harness tranche**: add an optional detector wrapper that checks Node version and requires explicit opt-in before any `npx` execution.
4. **Future validation tranche**: run against a known UI fixture and produce screenshot + code + optional detector JSON to prove finding format.

## Acceptance mapping

- Read back Douyin evidence: yes, `intake-analysis.md` and `router_item.json` read.
- Verify live repo facts: yes, GitHub API + raw README/package read.
- Compare UIMax: yes, current active `uimax-audit/SKILL.md` dimensions and flow-truth rule read.
- Define `anti_ai_slop`: yes, taxonomy, scoring extension, output format.
- Optional detector integration gate: yes, read-only commands and forbidden write commands defined.
- PRODUCT/DESIGN context packet: yes, YAML packet defined.

Residual gap: active Hermes skill files were intentionally not modified in this tranche because the task red line says not to modify UIMax skill and not to install/write hooks/config. This artifact is implementation-ready design evidence, not a deployed runtime gate.
