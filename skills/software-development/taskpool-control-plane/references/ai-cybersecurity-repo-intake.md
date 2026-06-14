# AI Cybersecurity Repository Intake and Safe Absorption

## Scope

Use this reference when the user asks to find, remember, analyze, absorb, or add to taskpool a GitHub repository in the AI + cybersecurity / hacker / pentest / agent-security space.

Typical triggers:
- “我记得有一个黑客相关的 GitHub，找一下 AI 用的相关仓库”
- “分析这个 AI hacker / cybersecurity skills repo”
- “把安全技能库加到 Hermes / taskpool / skill graph”
- “用这些仓库强化 Agent 安全自检”

## Anti-conditions

Do **not** use this to execute offensive tools, scan real targets, install C2/pentest frameworks, run malware analysis tools against unknown samples, or grant network/credential access. Those require a separate explicit lab/authorization boundary.

Do **not** treat a cybersecurity skill repository as a ready-to-enable Hermes skill pack. Default posture is read-only indexing and governance extraction.

## Intake sequence

1. **Recall before broad search**
   - Search prior sessions/taskpool for repo names and prior analysis before asking the user to repeat details.
   - Common remembered repo: `mukul975/Anthropic-Cybersecurity-Skills`.

2. **Verify live GitHub identity**
   - Use GitHub API or repository page to confirm:
     - `full_name`, description, stars/forks, language, license, created/updated/pushed dates, topics.
   - Fetch/read only safe metadata files first: `README.md`, `SECURITY.md`, `index.json`, coverage/mapping docs, validator scripts.
   - Avoid cloning/running toolchains unless the task explicitly authorizes local inspection and the repo is safe to clone.

3. **Classify repository role**
   - Skill library / knowledge graph: e.g. `mukul975/Anthropic-Cybersecurity-Skills`.
   - LLM/Agent security test harness: e.g. `NVIDIA/garak`, `getagentseal/agentseal`.
   - Agent firewall / egress mediation: e.g. `luckyPipewrench/pipelock`.
   - Sandbox/isolation: e.g. `always-further/nono`.
   - Offensive autonomous pentest / AI hacker: e.g. `Armur-Ai/Pentest-Swarm-AI`, `0xSteph/pentest-ai-agents`, `SanMuzZzZz/LuaN1aoAgent`, `Unclecheng-li/VulnClaw`.

4. **Risk-tier before absorption**
   - `safe_readonly`: metadata, taxonomy, framework mappings, policy docs, schemas, validators.
   - `defensive_allowed`: incident triage, detection engineering, ATT&CK coverage mapping, LLM guardrails, prompt-injection detection, report templates.
   - `lab_only`: malware analysis, memory forensics, binary analysis, web/API testing, exploit research.
   - `human_approval_required`: pentest workflows, active scanning, cloud/account probing, tool installation.
   - `deny_auto_execute`: C2 infrastructure, credential attack, phishing/social engineering, exploitation, post-exploitation, persistence/evasion, real-target attack chains.

5. **Map transferable value to Hermes**
   - Prefer absorbing:
     - skill metadata schema;
     - framework mappings (MITRE ATT&CK, NIST CSF, MITRE ATLAS, D3FEND, NIST AI RMF);
     - risk labels and execution policies;
     - read-only index/importer patterns;
     - validator scripts and schema checks;
     - defensive selfcheck/report templates.
   - Avoid absorbing raw operational commands for offensive steps.

6. **Frame taskpool items as governed evolution work**
   - Title around the mechanism delta, not “analyze hacker repo”.
   - Include evidence refs to the verified GitHub repo and safe metadata artifacts.
   - Encode red lines: no real-target scan, no exploit execution, no C2 setup, no credential access, no batch skill import.
   - Acceptance should require a source review/gap map, risk-tier plan, and minimal safe landing slice.

## Canonical example: Anthropic-Cybersecurity-Skills

Repository: `mukul975/Anthropic-Cybersecurity-Skills`

Verified characteristics from prior intake:
- 754 structured cybersecurity skills for AI agents.
- Apache-2.0, Python.
- 26 security domains.
- Mapped to five frameworks: MITRE ATT&CK, NIST CSF 2.0, MITRE ATLAS, D3FEND, NIST AI RMF.
- Contains `README.md`, `index.json`, `ATTACK_COVERAGE.md`, `SECURITY.md`, `skills/`, `mappings/`, `tools/validate-skill.py`, `.claude-plugin/`.

Recommended Hermes interpretation:
- Use as a **security skill graph / taxonomy / framework-mapping source**, not as an executable toolbox.
- First safe slice: read-only importer for `index.json`, schema/validator adaptation, risk classifier, and 3-5 defensive exemplars.
- Explicitly reject or index-only high-risk skills such as C2, spearphishing, exploitation, post-exploitation, persistence/evasion, and real-target attack chains.

Good first defensive exemplars:
- `triaging-security-incident`
- `implementing-mitre-attack-coverage-mapping`
- LLM prompt-injection detection / LLM guardrails skills
- incident-response and detection-engineering templates
- memory forensics only as lab/forensic knowledge, not automatic execution

## Connection to Agent/Web3 safety selfcheck

When combined with ERC-8126-style Agent verification:
- ERC-8126 supplies the Agent trust dimensions: identity, token/contract, media, code, web endpoint, wallet, private proof, risk score.
- Cybersecurity skill repositories supply the security taxonomy, framework mapping, validation schema, and defensive workflow templates.

The safe landing is an internal selfcheck / evidence gate:
- per-domain scoring;
- one-vote-veto critical conditions;
- evidence schema;
- report template;
- skill graph index;
- human gates for anything active or offensive.

## Pitfalls

- Do not install or enable a whole cybersecurity skill repository just because it is popular.
- Do not let “ethical hacking” labels bypass Hermes red lines.
- Do not confuse read-only repo analysis with authorization to run tools.
- Do not use GitHub stars as sufficient trust evidence; verify license, SECURITY policy, metadata, and concrete file structure.
- Do not create duplicate generic tasks for same-domain repos; state the net-new mechanism vs previous security/agent-safety tasks.

## Verification checklist

- [ ] Prior task/session recall checked for existing canonical repo/task.
- [ ] Live GitHub identity and safe metadata were verified.
- [ ] Repository was classified by role and risk tier.
- [ ] Offensive/high-risk content was kept index-only or denied by default.
- [ ] Taskpool framing includes red lines and safe acceptance evidence.
- [ ] Any proposed landing starts with read-only index/schema/validator or defensive examples, not batch execution.
