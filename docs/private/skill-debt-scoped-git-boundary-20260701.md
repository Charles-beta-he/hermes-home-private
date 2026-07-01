# Skill debt scoped git boundary / continuation packet

Date: 2026-07-01T09:44:16.458976+00:00

## Fresh audit evidence

- audit ok: True
- total skills: 266
- findings_by_code: `{}`
- findings_by_severity: `{}`
- latest JSON: `/Users/charles/.hermes/docs/private/skill-invocation-taxonomy/latest.json`
- latest MD: `/Users/charles/.hermes/docs/private/skill-invocation-taxonomy/latest.md`

## Git boundary evidence

- git status entries: 1367
- status counts: `{" D": 223, " M": 255, "??": 889}`
- bucket counts: `{"out_of_scope_dirty_state": 342, "session_reports": 9, "session_scripts": 3, "skill_tree_changed_or_untracked": 1013}`
- parser: `subprocess git status --porcelain=v1 -z`

## DecisionPacket

Decision: STOP before staging/commit/push.

Reason: `/Users/charles/.hermes` has broad dirty state outside the skill-debt remediation surface. A blind commit could mix unrelated cron outputs, notes, project profiles, workflow artifacts, submodule changes, and absorbed/deleted skill trees with this cleanup.

Requested authority to proceed beyond this point:
- Option A: authorize a local-only scoped commit plan and exact staging manifest, with no push.
- Option B: authorize creating an isolated patch bundle under docs/private, not a git commit.
- Option C: leave all changes uncommitted and treat the current audit/report artifacts as the closeout.

Rollback / escape hatch:
- No staging was performed in this checkpoint.
- No commit or push was performed.
- Future staging must be from a reviewed manifest, followed by `git diff --cached --name-status` readback before commit.

Post-action verification if authorized later:
1. Re-run `python3 /Users/charles/.hermes/scripts/skill_invocation_taxonomy_auditor.py --write-report --pretty`.
2. Review exact stage list from this JSON manifest or a reduced allowlist.
3. Run `git diff --cached --check` and `git diff --cached --name-status`.
4. Commit locally only, then read back `git show --stat --oneline HEAD`.
5. Push only after separate exact remote/branch authority.

## ContinuationPacket

Objective: preserve the zero-warning skill taxonomy state and decide whether/how to package the changes.

Completed evidence:
- taxonomy auditor latest: zero findings
- closeout report: `/Users/charles/.hermes/docs/private/skill-debt-zero-warning-closeout-20260701.md`
- boundary manifest JSON: `/Users/charles/.hermes/docs/private/skill-debt-scoped-git-boundary-20260701.json`

Pending action: human selects Option A/B/C above.

Current safe boundary: local reports and readbacks only; no git side effects beyond read-only status/diff inspection.

## Sample out-of-scope dirty entries

- ` M` `SOUL.md`
- ` D` `cron/output/0ca2cfd4068b/2026-04-27_05-05-19.md`
- ` D` `cron/output/1910cb31eabe/2026-04-26_23-00-35.md`
- ` D` `cron/output/1d5c2ca35c01/2026-04-27_02-15-30.md`
- ` D` `cron/output/2653ea4906ca/2026-04-26_18-00-42.md`
- ` D` `cron/output/2653ea4906ca/2026-04-27_00-00-52.md`
- ` D` `cron/output/2653ea4906ca/2026-04-27_06-01-05.md`
- ` D` `cron/output/600370f80d83/2026-04-27_02-02-06.md`
- ` D` `cron/output/6510a716937c/2026-04-27_03-02-11.md`
- ` D` `cron/output/6987cc40f289/2026-04-27_00-11-28.md`
- ` D` `cron/output/733798561af7/2026-04-27_00-06-48.md`
- ` D` `cron/output/789ca7d5e718/2026-04-26_18-01-06.md`
- ` D` `cron/output/789ca7d5e718/2026-04-26_18-05-49.md`
- ` D` `cron/output/789ca7d5e718/2026-04-27_00-06-17.md`
- ` D` `cron/output/789ca7d5e718/2026-04-27_06-05-17.md`
- ` D` `cron/output/ab3509a0e4e1/2026-04-27_04-31-01.md`
- ` D` `cron/output/c5cf6a078a72/2026-04-27_04-02-41.md`
- ` D` `cron/output/e9e8af6edb0e/2026-04-26_18-00-33.md`
- ` D` `cron/output/e9e8af6edb0e/2026-04-26_18-31-05.md`
- ` D` `cron/output/e9e8af6edb0e/2026-04-26_19-30-34.md`
- ` D` `cron/output/e9e8af6edb0e/2026-04-26_22-00-29.md`
- ` D` `cron/output/e9e8af6edb0e/2026-04-26_22-35-57.md`
- ` D` `cron/output/e9e8af6edb0e/2026-04-26_23-30-47.md`
- ` D` `cron/output/e9e8af6edb0e/2026-04-27_00-30-37.md`
- ` D` `cron/output/e9e8af6edb0e/2026-04-27_01-30-52.md`
- ` D` `cron/output/e9e8af6edb0e/2026-04-27_02-30-43.md`
- ` D` `cron/output/e9e8af6edb0e/2026-04-27_03-30-25.md`
- ` D` `cron/output/e9e8af6edb0e/2026-04-27_04-30-59.md`
- ` D` `cron/output/e9e8af6edb0e/2026-04-27_05-30-45.md`
- ` D` `cron/output/e9e8af6edb0e/2026-04-27_06-30-34.md`
- ` D` `cron/output/e9e8af6edb0e/2026-04-27_07-31-00.md`
- ` D` `cron/output/e9e8af6edb0e/2026-04-27_08-30-24.md`
- ` D` `cron/output/e9e8af6edb0e/2026-04-27_09-31-02.md`
- ` D` `cron/output/e9e8af6edb0e/2026-04-27_10-30-26.md`
- ` D` `cron/output/e9e8af6edb0e/2026-04-27_11-30-45.md`
- ` D` `cron/output/fbba30dd4a8b/2026-04-27_05-07-28.md`
- ` M` `docs/private/wechat-security-ark-AmVwmYdtFX/analysis.md`
- ` M` `hermes-agent`
- ` M` `hooks/registry.yaml`
- ` M` `notes/engineering-cybernetics/autonomous-evolution-log.jsonl`

## Sample skill-tree changed/untracked entries

- ` M` `skills/.archive/curator-umbrella-2026-06-10/autonomous-ai-agents/claude-code/SKILL.md`
- ` M` `skills/.archive/curator-umbrella-2026-06-10/autonomous-ai-agents/codex/SKILL.md`
- ` M` `skills/.archive/curator-umbrella-2026-06-10/autonomous-ai-agents/opencode/SKILL.md`
- ` M` `skills/.archive/curator-umbrella-2026-06-10/github/codebase-inspection/SKILL.md`
- ` M` `skills/.archive/curator-umbrella-2026-06-10/github/github-auth/SKILL.md`
- ` M` `skills/.archive/curator-umbrella-2026-06-10/github/github-code-review/SKILL.md`
- ` M` `skills/.archive/curator-umbrella-2026-06-10/github/github-issues/SKILL.md`
- ` M` `skills/.archive/curator-umbrella-2026-06-10/github/github-pr-workflow/SKILL.md`
- ` M` `skills/.archive/curator-umbrella-2026-06-10/github/github-repo-management/SKILL.md`
- ` M` `skills/.archive/curator-umbrella-2026-06-10/media/gif-search/SKILL.md`
- ` M` `skills/.archive/curator-umbrella-2026-06-10/media/youtube-content/SKILL.md`
- ` M` `skills/.archive/curator-umbrella-2026-06-10/mlops/evaluation/weights-and-biases/SKILL.md`
- ` M` `skills/.archive/curator-umbrella-2026-06-10/mlops/huggingface-hub/SKILL.md`
- ` M` `skills/.archive/curator-umbrella-2026-06-10/mlops/inference/llama-cpp/SKILL.md`
- ` M` `skills/.archive/curator-umbrella-2026-06-10/mlops/rag-knowledge-management/SKILL.md`
- ` M` `skills/.archive/curator-umbrella-2026-06-10/productivity/airtable/SKILL.md`
- ` M` `skills/.archive/curator-umbrella-2026-06-10/productivity/google-workspace/SKILL.md`
- ` M` `skills/.archive/curator-umbrella-2026-06-10/productivity/maps/SKILL.md`
- ` M` `skills/.archive/curator-umbrella-2026-06-10/productivity/nano-pdf/SKILL.md`
- ` M` `skills/.archive/curator-umbrella-2026-06-10/productivity/notion/SKILL.md`
- ` M` `skills/.archive/curator-umbrella-2026-06-10/productivity/ocr-and-documents/SKILL.md`
- ` M` `skills/.archive/curator-umbrella-2026-06-10/productivity/powerpoint/SKILL.md`
- ` M` `skills/.archive/curator-umbrella-2026-06-10/productivity/teams-meeting-pipeline/SKILL.md`
- ` M` `skills/.archive/curator-umbrella-2026-06-10/research/llm-wiki/SKILL.md`
- ` M` `skills/.archive/curator-umbrella-2026-06-10/research/research-paper-writing/SKILL.md`
- ` M` `skills/.archive/curator-umbrella-2026-06-17/autonomous-ai-agents/hermes-voice-console-integration/SKILL.md`
- ` M` `skills/.archive/curator-umbrella-2026-06-17/devops/hermes-tool-availability/SKILL.md`
- ` M` `skills/.archive/curator-umbrella-2026-06-17/research/references/absorbed/llm-wiki/SKILL.md`
- ` M` `skills/.archive/curator-umbrella-2026-06-17/research/references/absorbed/research-paper-writing/SKILL.md`
- ` M` `skills/.archive/curator-umbrella-2026-06-17/software-development/simplify-code/SKILL.md`
- ` M` `skills/.archive/devops/cli-tool-installation/SKILL.md`
- ` M` `skills/.archive/devops/hermes-observability/SKILL.md`
- ` M` `skills/.archive/devops/icon-asset-pipeline/SKILL.md`
- ` M` `skills/.archive/devops/macos-network-admin/SKILL.md`
- ` M` `skills/.archive/devops/multi-repo-branch-orchestration/SKILL.md`
- ` M` `skills/.archive/git-state-aware-debugging/SKILL.md`
- ` M` `skills/.archive/github/git-conflict-resolution/SKILL.md`
- ` M` `skills/.archive/product-prototype-code-audit/SKILL.md`
- ` M` `skills/.archive/project-profile-maintenance/SKILL.md`
- ` M` `skills/.archive/software-development/architecture-theory-audit/SKILL.md`
- ` M` `skills/.archive/software-development/cloud-edge-architecture/SKILL.md`
- ` M` `skills/.archive/software-development/concurrent-async-guard/SKILL.md`
- ` M` `skills/.archive/software-development/financial-ledger-frontend-patterns/SKILL.md`
- ` M` `skills/.archive/software-development/hermes-self-improvement-pipeline/SKILL.md`
- ` M` `skills/.archive/software-development/hybrid-app-packaging/SKILL.md`
- ` M` `skills/.archive/software-development/pwa-cache-invalidation/SKILL.md`
- ` M` `skills/.archive/software-development/pwa-install-prompt/SKILL.md`
- ` M` `skills/.archive/software-development/pwa-safe-area-handling/SKILL.md`
- ` M` `skills/.archive/software-development/task-depth-analysis/SKILL.md`
- ` M` `skills/.archive/task-framing-governance/SKILL.md`
- ` M` `skills/.archive/taskpool-ingest-triage/SKILL.md`
- ` M` `skills/.archive/testing/playwright-authenticated-screenshots/SKILL.md`
- ` M` `skills/.bundled_manifest`
- ` M` `skills/api-and-interface-design/SKILL.md`
- ` M` `skills/autonomous-ai-agents/SKILL.md`
- ` M` `skills/autonomous-ai-agents/hermes-agent/SKILL.md`
- ` M` `skills/autonomous-ai-agents/hermes-agent/references/background-watch-notifications.md`
- ` M` `skills/autonomous-ai-agents/hermes-experience-ratchet/SKILL.md`
- ` M` `skills/autonomous-ai-agents/hermes-personal-assistant-flow/SKILL.md`
- ` M` `skills/autonomous-ai-agents/hermes-pipeline/SKILL.md`
- ` M` `skills/autonomous-ai-agents/kanban-codex-lane/SKILL.md`
- ` D` `skills/autonomous-ai-agents/references/absorbed/claude-code/CHANGELOG.md`
- ` D` `skills/autonomous-ai-agents/references/absorbed/claude-code/SKILL.md`
- ` D` `skills/autonomous-ai-agents/references/absorbed/claude-code/evals/prompts.csv`
- ` D` `skills/autonomous-ai-agents/references/absorbed/claude-code/references/fable-5-migration.md`
- ` D` `skills/autonomous-ai-agents/references/absorbed/claude-code/references/session-log-analysis.md`
- ` D` `skills/autonomous-ai-agents/references/absorbed/claude-code/test-prompts.json`
- ` D` `skills/autonomous-ai-agents/references/absorbed/codex/CHANGELOG.md`
- ` D` `skills/autonomous-ai-agents/references/absorbed/codex/SKILL.md`
- ` D` `skills/autonomous-ai-agents/references/absorbed/codex/evals/prompts.csv`
- ` D` `skills/autonomous-ai-agents/references/absorbed/codex/references/codex-plugin-evaluation.md`
- ` D` `skills/autonomous-ai-agents/references/absorbed/codex/test-prompts.json`
- ` D` `skills/autonomous-ai-agents/references/absorbed/opencode/CHANGELOG.md`
- ` D` `skills/autonomous-ai-agents/references/absorbed/opencode/SKILL.md`
- ` D` `skills/autonomous-ai-agents/references/absorbed/opencode/evals/prompts.csv`
- ` D` `skills/autonomous-ai-agents/references/absorbed/opencode/test-prompts.json`
- ` M` `skills/autonomous-ai-agents/references/claude-code-goal-control-loop.md`
- ` M` `skills/autonomous-ai-agents/tradingagents-reference-patterns/SKILL.md`
- ` M` `skills/chinese-platforms/SKILL.md`
- ` M` `skills/codebase-intelligence/SKILL.md`
