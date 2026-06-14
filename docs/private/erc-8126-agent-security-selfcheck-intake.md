# ERC-8126 / Agent 安全体检自检标准 intake

Source: https://www.odaily.news/zh-CN/post/5211331
Spec: https://eips.ethereum.org/EIPS/eip-8126
Captured: 2026-06-14

## Source essence

Odaily article summarizes ERC-8126 as an AI Agent verification layer built on ERC-8004 identity registration. The EIP defines multi-layer verification for registered AI agents and produces a unified 0-100 risk score. Verification types:

- ETV: Ethereum Token Verification — contract presence/legitimacy and smart-contract risk.
- MCV: Media Content Verification — authenticity, provenance, tamper/deepfake/watermark/signature checks.
- SCV: Solidity Code Verification — deployed bytecode/code security and common vulnerabilities.
- WAV: Web Application Verification — HTTPS endpoint reachability, SSL certificate validity, common web vulnerabilities, OWASP WSTG alignment.
- WV: Wallet Verification — wallet ownership/transaction history/threat-intelligence risk.
- PDV/ZKP: private data verification / zero-knowledge proof so verification can expose conclusions without leaking source/infrastructure details.
- QCV: optional quantum-resistant encryption for sensitive verification records.

EIP-8126 normatively requires verification requests to reference an ERC-8004 `agentId`; providers resolve ERC-8004 metadata and extract wallet, chain, contract, endpoints, image/media, platform, Solidity code, etc. It defines risk tiers: 0-20 low, 21-40 moderate, 41-60 elevated, 61-80 high, 81-100 critical.

## Local interpretation for Hermes / Web3 selfcheck

Use as a framework skeleton, not as a self-issued certification standard. Convert external attestation semantics into internal selfcheck gates:

1. Identity and official-entry binding: domain, wallet, API, social, repo, contract addresses mutually prove the same project/agent.
2. Web/API security: HTTPS, certificate, headers, CORS, auth, rate limit, debug/admin/source-map exposure, OWASP WSTG-style checks.
3. Contract/on-chain safety: deployed address/source/bytecode alignment, owner/admin/upgrade/mint/pause/blacklist/spender risks, audit coverage vs deployed addresses.
4. Wallet/funds risk: ownership proof, transaction/threat-intel risk, hot-wallet exposure, multisig/timelock, readable signatures, revoke guidance.
5. Code/supply-chain safety: frontend/backend dependencies, build provenance, CI secrets, npm/Docker/GitHub Actions risk, postinstall/script injection.
6. Agent permission/tool-call safety: dangerous action gates, prompt-injection resistance, tool isolation, audit logs, rollback/revoke/stop controls.
7. Data/privacy/logging: secrets in code/logs/builds, sensitive-report redaction, evidence visibility vs exploit detail.
8. Content/media authenticity: brand assets, whitepaper/team/KOL claims, C2PA/watermark/signature/provenance where applicable.
9. Ops/incident response: monitoring, alerting, kill switch, rollback, incident ownership, recertification cadence.

## Scoring rule to preserve

Do not use naive average-only scoring. Add hard fail-closed gates:

- Private key/seed/API secret leak.
- Unauthorized asset transfer or malicious transaction/signature path.
- Contract authority can arbitrarily seize/drain user assets without disclosed governance.
- RCE, unauthenticated admin, sensitive data exposure.
- Audit/report target differs from deployed production contract/code.
- Agent can execute high-risk fund/system actions without human/permission gate.

Final output should show both per-domain scores and one-vote-veto Critical/High conditions.

## Proposed taskpool landing

Create a governed evolution task to turn this into an internal selfcheck standard/template for Hermes/Web3/Agent projects: checklist, scoring rubric, evidence schema, report template, and minimal deterministic probes where safe. No external certification claims; no automated secret scanning or active exploitation beyond safe read-only probes unless separately authorized.
