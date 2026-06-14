# Cybersecurity Skills + ERC-8126 安全技能图谱 intake

Captured: 2026-06-14

## Source evidence

Primary repo:
- https://github.com/mukul975/Anthropic-Cybersecurity-Skills
- GitHub API readback 2026-06-14: Python, Apache-2.0, ~15.6k stars, ~1.8k forks, created 2026-02-25.
- Description: 754 structured cybersecurity skills for AI agents; mapped to MITRE ATT&CK, NIST CSF 2.0, MITRE ATLAS, D3FEND, NIST AI RMF; agentskills.io standard; works with Claude Code, GitHub Copilot, Codex CLI, Cursor, Gemini CLI, Hermes Agent, etc.
- Root files observed: README.md, LICENSE, SECURITY.md, ATTACK_COVERAGE.md, index.json, skills/, mappings/, tools/, .claude-plugin/.
- index.json readback: dict with `skills` list, 754 records; records include `name`, `description`, `domain`, `path`.
- tools/validate-skill.py readback: metadata validator with canonical subdomains including incident-response, digital-forensics, soc-operations, web-application-security, network-security, penetration-testing, cloud-security, container-security, endpoint-security, api-security, mobile-security, blockchain-security, supply-chain-security, wireless-security, ai-security.
- ATTACK_COVERAGE.md readback: maps skills to MITRE ATT&CK techniques/tactics; includes defensive, hunting, exploitation, and response skills.
- SECURITY.md readback: repository scope explicitly includes skills with commands or scripts that could cause unintended harm.

Related existing Hermes tasks:
- `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-06-02-评估-anthropic-cybersecurity-skills-对-hermes-安全技能图谱的参考价值.md` — completed general repo evaluation; conclusion: only adopt read-only index/metadata/validator and defensive samples, do not bulk-enable risky scripts.
- `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-06-14-将-erc-8126-转化为-agent-web3-安全体检自检标准.md` — active/in progress standardization task for ERC-8126 Agent/Web3 selfcheck.

Related standards / repos:
- ERC-8126: https://eips.ethereum.org/EIPS/eip-8126 — Agent verification dimensions ETV/MCV/SCV/WAV/WV/PDV/QCV and risk score model.
- NVIDIA/garak — LLM vulnerability scanner for prompt injection, leakage, hallucination, jailbreak, etc.
- OWASP Top 10 for LLM Applications — LLM app security taxonomy.
- getagentseal/agentseal, luckyPipewrench/pipelock, always-further/nono — candidate references for agent-skill/MCP/tool-call security, firewall/egress receipts, sandboxing.

## Net-new delta vs existing tasks

This is not another generic Anthropic-Cybersecurity-Skills review and not a duplicate ERC-8126 article task.

Net-new objective: combine both evidence streams into a concrete Hermes landing plan:
1. Read-only security skill index adapter.
2. Risk classifier for 754 skills.
3. Mapping from security skills/frameworks to Agent/Web3 selfcheck domains.
4. Minimal defensive-only skill subset proposal.
5. Explicit deny/human-approval policy for red-team/offensive classes.

## Proposed safety classification

Initial policy classes:
- `safe_readonly`: index, framework mapping, report templates, taxonomy docs.
- `defensive_allowed`: incident triage, detection engineering, coverage mapping, guardrail design, prompt-injection detection methodology.
- `lab_only`: forensics, malware analysis, binary analysis; allowed only against provided artifacts/lab data.
- `human_approval_required`: web/API/pentest checks, cloud environment scans, dependency scans touching nonlocal systems.
- `deny_auto_execute`: C2 infrastructure, exploitation, phishing/social engineering, credential access, post-exploitation, persistence/evasion, real-target scanning.

## Proposed first defensive candidates

- `triaging-security-incident` → Hermes incident-response / runbook template.
- `implementing-mitre-attack-coverage-mapping` → coverage matrix for selfcheck/reporting.
- `detecting-ai-model-prompt-injection-attacks` → browser/web/MCP/tool-output prompt-injection checks.
- `implementing-llm-guardrails-for-security` → pre-tool intent-risk-review gate and output filtering.
- `performing-memory-forensics-with-volatility3` → lab-only forensic knowledge, no automatic command execution.

## Red lines

- Do not install or execute offensive tools from the repo during intake.
- Do not bulk import 754 skills into Hermes active skill path.
- Do not enable autonomous pentesting, scanning, exploitation, phishing, C2, malware, credential, or post-exploitation workflows.
- Do not touch real external targets, credentials, wallets, production services, or third-party systems without a separate explicit authorization packet.
- Treat the repo as an untrusted third-party knowledge source; import metadata only after validation and risk tagging.

## Acceptance target

Create a governed task to build a Hermes security skill-graph absorption plan that joins Anthropic-Cybersecurity-Skills with ERC-8126 selfcheck: schema, classifier, mapping matrix, defensive samples, and proof gates.
