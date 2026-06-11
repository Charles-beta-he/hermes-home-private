# PM Skills reference review — 2026-06-11

## Source facts

- Social source: WeChat Channels short link `https://weixin.qq.com/sph/Ata5dqYwjz` resolved to `https://channels.weixin.qq.com/finder-preview/pages/sph?id=Ata5dqYwjz`.
- Visible post facts: author `华盛顿`; caption `高赞开源 AI 产品管理操作系统 #开源 #github #ai #产品管理`; date `2026年6月9日`; visible project label `FacelessReels.video` in the preview area.
- Canonical repository verified directly: `https://github.com/phuryn/pm-skills`.
- Reviewed clone path: `/tmp/pm-skills-review`.
- Reviewed commit: `d384f0c9eb81fe74656a4f6da168587836939edb` (`docs: add native Codex CLI install path for PM Skills`, 2026-06-06).
- Repository guidance read: `AGENTS.md` points to `CLAUDE.md`; `CLAUDE.md` defines the structure and maintenance rules.
- Validator evidence: `python3 validate_plugins.py` returned PASS for all 9 plugins with `68` skills and `42` commands, total `110` components.

## Structure model

`pm-skills` is a marketplace of independent PM plugins:

- marketplace manifest: `.claude-plugin/marketplace.json`
- plugin directories: `pm-product-discovery`, `pm-product-strategy`, `pm-execution`, `pm-market-research`, `pm-data-analytics`, `pm-go-to-market`, `pm-marketing-growth`, `pm-toolkit`, `pm-ai-shipping`
- per-plugin manifest: `<plugin>/.claude-plugin/plugin.json`
- domain knowledge: `<plugin>/skills/<skill>/SKILL.md`
- workflow commands: `<plugin>/commands/<command>.md`
- validator: `validate_plugins.py`

Design rule from repo guidance: skills are nouns/concepts; commands are verbs/workflows. No hard cross-plugin references because plugins install independently.

## Transferable patterns for Hermes

1. Preserve the distinction between framework skills and workflow commands. Hermes should not flatten an external marketplace into dozens of narrow skills.
2. Add a workflow layer above skills: command/workflow stages should explicitly chain skills, gates, artifacts, and next-state suggestions.
3. Make `pm-ai-shipping`-style review part of Hermes delivery closure: document app → derive tests → security audit → performance audit → ship packet → real verification.
4. Keep marketplace/plugin manifests as discoverability surfaces, but add Hermes-specific gates: evidence bundle, SSOT path, taskpool candidate schema, read-back verification, and ratchet writeback.
5. Treat social/video posts as direction signals only; canonical facts come from repository/docs/validators.

## Gaps in the source pattern

- Follow-up suggestions are prose, not a machine-readable workflow state machine.
- Evidence strength is not a first-class schema.
- Project storage/SSOT layout is not prescribed.
- Real tool integrations such as GitHub Issues, Lark, PostHog, production logs, and taskpool lifecycle are outside the repo.
- Validator checks package shape, not behavior quality, hallucination resistance, or routing regressions.

## Hermes landing decision

Create a Hermes-local pipeline skill named `product-workflow-operating-system` with:

- 12-stage lifecycle: intake → discovery → evidence → strategy → metrics → PRD → red-team → planning → build → ship-check → launch → measure/retro.
- Three default high-value chains: opportunity-analysis, PRD-to-engineering, AI-code-shipping.
- Templates for evidence bundles, workflow state, and task candidates.
- A deterministic scaffold script that creates a project workflow workspace with SSOT, evidence, decisions, and task candidate files.

## Verification evidence for this review

- Browser snapshot showed WeChat post title/caption/date/author.
- GitHub page showed repository title, stars, folders, and description.
- Local clone and validator command produced all-plugin PASS.
- This artifact is a local SSOT note for the adaptation; it does not claim the external repository is installed or executed inside Hermes.
