# External repo intake evidence — ComposioHQ/awesome-codex-skills

Date: 2026-06-14

## User framing

User asked to add taskpool item for: “ComposioQ：1.3万星开源工具，一键赋予AI专业架构能力” with three highlighted skills:

1. `brooks-lint` — book-grounded AI code review / code quality audit.
2. `codebase-recon` — global codebase radar using git-history analysis and token-saving reconnaissance.
3. `connect-apps` — connect AI/agents to 1000+ apps for real workflows such as PR/deploy.

User-supplied install framing: `npx skills add [技能链接]`, restart Claude/Cursor/etc, combine skills into custom AI programming workflow.

## Canonical source inspected

- Repo: https://github.com/ComposioHQ/awesome-codex-skills
- Full name: `ComposioHQ/awesome-codex-skills`
- Description: `A curated list of practical Codex skills for automating workflows across the Codex CLI and API.`
- Stars/forks at intake: 13628 / 1315
- Default branch: `master`
- Language: Python
- Topics: `awesome`, `awesome-lists`, `awesome-resources`, `codex`, `codex-cli`, `codex-skills`, `coding-agent-skills`, `coding-agents`, `gpt-5-1-codex`, `gpt-5-codex`, `llm`, `skills`
- License: none detected at repo root via GitHub API
- Updated at: 2026-06-13T18:29:03Z

## Repo structure inspected

Top-level contains a curated skill index plus many individual skill folders, including:

- `connect/`, `connect-apps/`
- `codebase-migrate/`, `create-plan/`, `deploy-pipeline/`, `gh-address-comments/`, `gh-fix-ci/`, `mcp-builder/`, `pr-review-ci-fix/`, `sentry-triage/`, `webapp-testing/`
- productivity/data/communication folders such as `meeting-notes-and-actions/`, `notion-*`, `linear/`, `issue-triage/`, `spreadsheet-formula-helper/`
- meta folders: `skill-creator/`, `skill-installer/`, `skill-share/`, `template-skill/`

README describes Codex skills as modular instruction bundles with `SKILL.md` metadata, loaded on trigger to keep context lean. Recommended install is a Python installer into `$CODEX_HOME/skills`, not the `npx skills add` command from the user’s summary. Some referenced external skills do advertise `npx skills add` in their own README.

## Highlighted skill mapping

### 1) brooks-lint

Canonical repo from awesome list:

- Repo: https://github.com/hyhmrright/brooks-lint
- Description: `AI code reviews grounded in 12 classic engineering books — decay risk diagnostics with book citations, severity labels, and 6 analysis modes including full-sweep auto-fix`
- Stars/forks at intake: 1039 / 48
- License: MIT
- Language: JavaScript
- Topics include: `ai-code-review`, `architecture-review`, `auto-fix`, `claude-code-plugin`, `codex-cli-plugin`, `code-quality`, `code-smells`, `refactoring`, `test-quality`.
- README inspected: actual current claim is **twelve** classic engineering books, not six. It evaluates six production-code decay risks and six test-suite decay risks. Books include Brooks, McConnell, Fowler, Martin, Hunt & Thomas, Evans, Ousterhout, SE@Google, Osherove, Google Testing, Feathers, Meszaros.

Hermes relevance:
- Useful as a reference for evidence-grounded review rubrics, severity labels, citation-backed findings, false-positive guards, architecture/test-quality review dimensions.
- Do not import as-is; map into Hermes code-review/multimodel review/evidence-gated task closure patterns.

### 2) codebase-recon

Canonical repo from awesome list:

- Repo: https://github.com/yujiachen-y/codebase-recon-skill
- Description: `A coding agent skill that analyzes git history to understand a codebase before reading any code`
- Stars/forks at intake: 20 / 1
- License: MIT
- Language: none detected
- README/SKILL inspected: git-history probe and 7 parallel analyses: code hotspots, bus factor, bug magnets, team momentum, firefighting frequency, recently added files, active contributors. Cross-references hotspots ∩ bug magnets and reports primary owners and momentum/bus-factor risks.

Hermes relevance:
- Directly useful as a low-token pre-read reconnaissance phase before codebase analysis/refactoring.
- Candidate landing: Hermes codebase-intelligence / project-evidence-grounding / taskpool intake preflight.
- Need benchmark against current search/session/profile flow; use deterministic git commands and source provenance rather than LLM-only summary.

### 3) connect-apps / connect

Canonical source inside ComposioHQ repo:

- `connect-apps/SKILL.md` description: connect Claude to external apps via Composio CLI; send emails, create issues, post messages, and take actions across Gmail, Slack, GitHub, Notion, and 1000+ services.
- `connect/SKILL.md` description: connect Codex to any app via Composio CLI for real actions across 1000+ services.
- Setup includes `curl -fsSL https://composio.dev/install | bash`, `composio login`, `composio link <toolkit>`, and `composio execute <SLUG> -d '{...}'`; supports `search`, `tools info`, `--dry-run`, `--get-schema`, `run`, and `proxy`.
- Environment variables: `COMPOSIO_API_KEY`, `COMPOSIO_BASE_URL`, `COMPOSIO_SESSION_DIR`, `COMPOSIO_DISABLE_TELEMETRY=true`.

Hermes relevance:
- Maps to external side-effect executors and app-connector policy, not ordinary skill import.
- Potentially overlaps Hermes native send_message/GitHub/Feishu/taskpool adapters; must remain behind permission gates, dry-run/schema checks, audit logs, and app/tool allowlists.
- Do not install Composio, log in, link apps, execute actions, or route secrets during intake.

## Hermes classification

- Artifact type: curated Codex skill ecosystem + external action connector references.
- Main lane: `evolution`.
- Project: `hermes-agent`.
- Dominant architecture target: `skill-graph` because main value is skill-library/routing/governance, with secondary `local-brain` and external side-effect executor implications.
- Priority: P2.

## Anti-drift / red lines

- Do not run `npx skills add`, `curl | bash`, `composio login`, `composio link`, or any `composio execute` during intake.
- Do not install third-party skills into Hermes or Codex without a separate review/gate.
- Do not treat an awesome list as audited code.
- Do not upload local skills, brain/taskpool notes, project files, credentials, or session transcripts to external services.
- `connect-apps` is a side-effect executor surface; it cannot bypass Hermes permission, proof, and human-gate policy.
- User summary says “六本书级代码审查”, but current brooks-lint README says twelve books; preserve the discrepancy as source-drift evidence.

## Recommended taskpool objective

Create a source-review/gap-mapping task to evaluate whether/how ComposioHQ awesome-codex-skills, brooks-lint, codebase-recon, and connect-apps should influence Hermes skills/control-plane:

1. Inventory relevant skill clusters and reject duplicates/noisy imports.
2. Map brooks-lint rubrics to Hermes code-review evidence gates.
3. Map codebase-recon git probes to a deterministic low-token pre-read workflow.
4. Map connect-apps to a governed external-side-effect executor contract with dry-run/schema/permission gates.
5. Decide patch existing Hermes skills vs create new workflow pack vs reject/watchlist.
