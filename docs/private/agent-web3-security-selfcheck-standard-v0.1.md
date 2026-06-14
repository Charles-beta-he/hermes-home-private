# Agent/Web3 Security Self-Check Standard v0.1

Source lineage: ERC-8126 / ERC-8004 verification ideas transformed into **internal self-check only**. This standard is not an external certification, attestation, audit, or on-chain claim.

## Non-negotiable boundary

- Do not claim ERC-8126 certification.
- Do not publish self-attestation as third-party verification.
- Do not run active attacks, exploit attempts, chain transactions, credential exfiltration, or third-party writes under this standard.
- Treat social/video/repo claims as routing evidence only until independently verified.

## Dimensions

Each dimension records `score` from 0 to 100, where higher means higher risk. Final risk is **not an average**; it is the max of per-dimension risk plus kill-switch escalation.

Risk bands:

- 0-20: Low
- 21-40: Medium
- 41-70: High
- 71-100: Critical

Required dimensions:

1. `identity`
   - domain, wallet, repo, social, contract, and API entrypoints bind to the same project/agent.
2. `web_api`
   - HTTPS, certificate, headers, CORS, auth, rate limit, admin/debug/source-map exposure, OWASP-style safe checks.
3. `contract_wallet`
   - deployed address/source/bytecode alignment, owner/admin/upgrade/mint/pause/blacklist/spender risk, multisig/timelock, audit target alignment.
4. `code_supply_chain`
   - dependency and build provenance, CI secrets, package scripts, Docker/GitHub Actions risks.
5. `agent_permissions`
   - high-risk tool calls, human gates, prompt-injection resistance, audit logs, rollback/revoke/stop controls.
6. `data_privacy`
   - secret handling, sensitive logs/builds, report redaction, exploit-detail minimization.
7. `media_authenticity`
   - brand/media/team/KOL/whitepaper provenance, signatures, watermark/C2PA where relevant.
8. `ops_incident_response`
   - monitoring, alerting, kill switch, rollback, incident owner, recertification cadence.

## Kill-switch findings

Any kill-switch finding escalates final risk to `High` or `Critical` regardless of average score.

Allowed kill-switch ids:

- `secret_leak`
- `unauthorized_asset_transfer_path`
- `undisclosed_asset_seizure_authority`
- `rce_or_unauth_admin_or_sensitive_data_exposure`
- `audit_target_mismatch`
- `ungated_high_risk_agent_action`

## Evidence schema

```json
{
  "schema": "agent_web3_security_selfcheck_v0_1",
  "metadata": {
    "project": "Example Project",
    "scope": "internal self-check, no external certification",
    "internal_only": true,
    "claims_external_certification": false
  },
  "dimensions": {
    "identity": {"score": 10, "status": "pass", "evidence": ["..."]},
    "web_api": {"score": 20, "status": "pass", "evidence": ["..."]},
    "contract_wallet": {"score": 35, "status": "warn", "evidence": ["..."]},
    "code_supply_chain": {"score": 25, "status": "warn", "evidence": ["..."]},
    "agent_permissions": {"score": 30, "status": "warn", "evidence": ["..."]},
    "data_privacy": {"score": 15, "status": "pass", "evidence": ["..."]},
    "media_authenticity": {"score": 20, "status": "pass", "evidence": ["..."]},
    "ops_incident_response": {"score": 40, "status": "warn", "evidence": ["..."]}
  },
  "kill_switch_findings": [],
  "report_template_filled": true
}
```

## Report template

- Project:
- Scope:
- Self-check date:
- Internal-only disclaimer:
- Evidence sources:
- Kill-switch findings:
- Per-dimension score/status/evidence:
- Final risk:
- Remediation priority:
- Residual risk:
- Next review trigger:

## Local evaluator

Use the no-network evaluator:

```bash
python3 ~/.hermes/scripts/agent_web3_security_selfcheck.py report.json --pretty
```

The evaluator validates the schema, forbids external-certification claims, verifies all required dimensions have evidence, and computes final risk with kill-switch escalation instead of averaging.
