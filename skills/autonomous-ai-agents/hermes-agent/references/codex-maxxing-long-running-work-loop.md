# Codex-maxxing long-running work loop

Source: OpenAI page and whitepaper `Codex-maxxing for long-running work` (`https://openai.com/index/codex-maxxing-long-running-work/`, whitepaper PDF `OAI_WhitePaper_Codex-maxxing26.pdf`).

Scope: Hermes self-architecture, workflow orchestration, personal-assistant loops, taskpool/mission/cron design, and agentic product work that must continue beyond a single prompt.

Applicability:
- User asks to absorb an external agent-workflow idea, make work continue across sessions, or improve Hermes long-running execution.
- A task should be treated as a durable loop rather than a one-shot answer.
- The work involves recurring check-ins, remote steering, artifact review, memory/profile/SSOT writeback, or human approval gates.

Anti-conditions:
- Do not use this pattern to justify autonomous external sending, publishing, payment, credential entry, destructive actions, or production mutation without exact authority and readback.
- Do not store WIP, task progress, PR/commit IDs, or transient open loops in global memory; keep them in project SSOT, taskpool evidence, mission ledger, session, or scoped docs.
- Do not treat a durable chat thread as a source of truth when a project SSOT/profile/evidence ledger exists.
- Do not accept external product narration as runtime certification; verify behavior with local artifacts, tests, logs, UI/API evidence, or bounded screenshots.

## Transferable pattern

External pattern: Codex is framed as a persistent workspace where work can start, keep going, and become real output through durable threads, voice input, steering, memory, tools, remote control, automations, goals, and side-panel artifacts.

Hermes translation:

```text
Durable objective/profile/SSOT
  + tool-bounded execution surfaces
  + scoped memory/skill/profile writeback
  + recurring wake signals
  + mid-turn / remote human steering
  + artifact-first review
  + proof gates and receipts
= governed long-running work loop
```

Core loop:

```text
1. Anchor: name the durable work home
   - project profile, SSOT, taskpool card, mission ledger, or session thread.
   - identify source of truth before creating derived prompts or jobs.

2. Observe: collect current state
   - Slack/Gmail/GitHub/browser/logs/taskpool/PR/preview/deployment/etc.
   - separate observed facts from model interpretation.

3. Context: retrieve the right scoped history
   - project profile / SSOT / session_search / skill / evidence ledger.
   - avoid global-memory ghosts for current status.

4. Prepare: draft or execute only reversible work
   - summarize, propose, patch local files, run tests, render previews, prepare replies.
   - irreversible actions remain draft-only unless separately authorized.

5. Review surface: make the artifact visible
   - diff, browser preview, screenshot, report, spreadsheet, Markdown, PR, task card, dashboard.
   - comments and user steering become new instructions, not silent assumptions.

6. Gate: ask or stop only at true authority/evidence boundaries
   - external send/publish/deploy/payment/credential/destructive gates require exact target + payload + readback.
   - if safe local verification remains, continue instead of leaving a plan.

7. Writeback: update the right durable layer
   - stable user preference -> compact memory.
   - reusable procedure -> skill/reference.
   - project state/decision -> project SSOT/profile/ADR/evidence.
   - future executable work -> taskpool/mission with acceptance evidence.
   - one-off progress -> session/evidence only.

8. Continue or close
   - schedule recurrence only with a self-contained prompt, stop condition, and delivery boundary.
   - close with receipts: commands, files, tests, screenshots, task state, or explicit blocker.
```

## Strong-goal requirement

For long-running execution, convert weak goals into verifiable goals.

Weak:
```text
Implement the plan in this Markdown file.
```

Strong:
```text
Port/implement X while preserving Y compatibility; success is when named tests/checks pass, differences are documented, and the review artifact is visible at <surface>.
```

Hermes acceptance fields should include:
- expected behavior;
- non-goals / red lines;
- allowed surfaces/tools;
- acceptance evidence;
- anti-drift check;
- human approval gate for irreversible actions;
- stop/continue condition.

## Voice and steering intake

Treat voice/rough input as valuable because it preserves uncertainty, half-remembered names, and implicit context. When absorbing voice or mid-turn steering:
- preserve uncertainty instead of over-normalizing it into fake certainty;
- convert loose references into verifiable lookup tasks;
- let steering update the queue while preserving safety gates;
- do not interpret broad approval as permission for unrelated side effects.

## Automation rule

Default automation posture:

```text
observe + research + draft + verify + report
not send/publish/deploy/pay/delete unless explicitly authorized for that exact action
```

Recurring jobs should include:
- cadence;
- source surfaces to inspect;
- allowed actions;
- forbidden actions;
- stop condition;
- output/delivery target;
- required skill/profile/workdir;
- readback evidence.

## Artifact-first review surfaces

Side-panel lesson mapped to Hermes: the artifact must be part of the loop, not hidden behind chat prose.

Preferred review surfaces:
- git diff / PR;
- local browser preview / screenshot diff;
- Storybook / Streamlit / Jupyter / Remotion / Slidev;
- Markdown report / CSV table / spreadsheet / PDF;
- taskpool card / mission board / dashboard;
- command/test/log receipts.

## Pitfalls

1. Durable-thread worship: long chat history is useful, but project SSOT/evidence remains canonical for long-running projects.
2. Memory pollution: do not save current project status or open loops to always-on memory.
3. Automation authority creep: scheduled/remote loops prepare decisions; they do not silently cross external side-effect gates.
4. Artifact gap: a chat summary without diff/preview/test/report is not enough for work that claims delivery.
5. Goal ambiguity: long-running agents drift unless success criteria and anti-drift checks are explicit.
6. Connector sprawl: more tool access increases blast radius; bind each loop to allowed surfaces and authority.

## Verification checklist

- [ ] Durable home named: profile / SSOT / taskpool / mission / session.
- [ ] Current state observed from a real source.
- [ ] Goal converted to observable acceptance evidence.
- [ ] Allowed and forbidden actions are explicit.
- [ ] Artifact review surface exists.
- [ ] Human gate exists for irreversible actions.
- [ ] Writeback target is correct and not global-memory WIP.
- [ ] Recurrence, if any, has cadence, stop condition, and delivery boundary.
