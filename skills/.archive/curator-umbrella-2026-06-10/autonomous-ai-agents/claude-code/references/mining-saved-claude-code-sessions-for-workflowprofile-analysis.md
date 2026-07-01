# Mining Saved Claude Code Sessions for Workflow/Profile Analysis

Extracted from `/Users/charles/.hermes/skills/.archive/curator-umbrella-2026-06-10/autonomous-ai-agents/claude-code/SKILL.md` on 2026-07-01T08:56:29.614759+00:00 during full core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

## Mining Saved Claude Code Sessions for Workflow/Profile Analysis

Use this path when the user asks to analyze past Claude Code conversations, infer work habits, reconstruct a project's working goals, or audit long-running Claude workflows.

Full playbook: `references/session-log-analysis.md`

Core pattern:
1. Locate saved sessions under `~/.claude/projects/<normalized-project-path>/*.jsonl` and in-repo context under `CLAUDE.md`, `.claude/skills/`, `.claude/rules/`, `.claude/agents/`.
2. Parse logs instead of reading them raw: separate direct user prompts, assistant text summaries, agent dispatch prompts, tool results, and `ai-title` records.
3. Redact secrets before writing any extracted corpus or final summary.
4. Build compact evidence with claim IDs and evidence IDs; cross-check conversation-derived claims against `package.json`, route/screen inventory, docs, ADRs, and `git log`.
5. For multi-model analysis, feed the compact evidence state to `consult_models.py`; ensure claims are in the top-level `claims` field with `evidence[].supports`, not only a prose `claims_to_check` note.
6. In the final answer, report confidence/caveats and artifact paths, not raw private transcript dumps.

Pitfall: direct user prompts outrank assistant summaries. Do not generalize one project's preferences into a global user profile unless the user asks for long-term profile work and the evidence repeats.
