# Codex plugin evaluation and permission tiers

Use this reference when a user shares a video/article about Codex plugins or asks whether a Codex plugin should be installed/enabled.

## Evidence-first plugin intake

1. Extract the claimed plugin names and use cases from the source.
2. Verify the local Codex version and plugin surface before judging:
   - `codex --version`
   - `codex plugin --help`
   - `codex plugin list`
3. Read each candidate plugin's local metadata when present:
   - `<plugin>/.codex-plugin/plugin.json`
   - `<plugin>/README.md`
   - relevant `skills/*/SKILL.md`
4. Separate capability value from install/permission risk.
5. Do not install or enable plugins that touch user browser state, desktop apps, external accounts, or messages without explicit user approval.

## Useful classification

- **Default-safe / local dev**: in-app `browser` for localhost/file targets, code-review helpers, local-only read/write inside a repo.
- **Productivity artifacts**: `presentations`, `documents`, `spreadsheets`; useful when the deliverable is a deck/doc/sheet, still verify output by reading/rendering it back.
- **Creative/media**: `hyperframes`; useful for HTML/CSS/GSAP video, product demos, motion prototypes, and website-to-video workflows. Treat as scenario-specific, not a default coding dependency.
- **Workflow/methodology**: `superpowers`; evaluate mechanisms such as planning, TDD, debugging, and subagent-driven development. Avoid letting it bypass Hermes taskpool, evidence, or proof gates.
- **High-permission surfaces**: `chrome`, `computer-use`, Gmail/Slack/Calendar/account plugins. Require explicit task-scoped authorization, auditability, and stop/rollback path.

## Hermes boundary rules

- Plugins are action surfaces, not facts or authority.
- Hermes taskpool/ledger/evidence remains canonical for status, claims, and completion.
- Codex plugin output must be read back, rendered, tested, or otherwise verified before reporting success.
- Browser/Chrome/Computer Use plugin choice should follow least authority:
  1. local in-app Browser for local web verification;
  2. APIs/CLIs/connectors when available;
  3. Chrome only when real user browser state is required and authorized;
  4. Computer Use only when no DOM/API/a11y/browser route can accomplish the task.

## Install decision template

```text
Plugin: <name>
Status: installed/enabled | available/not installed | unverified
Capability: <what it adds>
Hermes overlap: <existing Hermes/browser/taskpool/skill capability>
Permission tier: local | artifact write | account read | account write | desktop/browser control
Use now?: yes/no/conditional
Condition: <explicit task and authorization needed>
Verification: <how to prove output>
```

## Pitfalls

- Treating social-video plugin lists as canonical documentation.
- Installing high-permission plugins just because the capability is impressive.
- Letting workflow plugins re-plan or re-triage outside Hermes governance.
- Confusing Codex `browser` (in-app/local dev) with `chrome` (real user Chrome state).
- Reporting a plugin is useful without checking the current local marketplace/install state.
