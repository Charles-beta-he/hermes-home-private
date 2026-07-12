你是 Claude Fable 5，对 Hermes Portfolio 其他项目执行与刚才 Agent OS 相同风格的系统审核、架构审核、多角度审核。只基于证据，不声称执行工具。

范围：除 hermes-agent-os-control-plane 外的 15 个 portfolio 项目。本轮只读 metadata/evidence 审核，不改项目代码、不外发、不 push/deploy、不改 lifecycle。

Portfolio doctor: ok=true, project_count=16, profile_count=16, errors=0, warnings=0。
Strict verify: ok=true。
机器审计 summary: {'pass': 7, 'warn': 8, 'fail': 0, 'total': 15}。
项目摘要：
[
  {
    "id": "hermes",
    "type": "platform",
    "status": "ledgered",
    "audit_status": "warn",
    "ledger_exists": true,
    "ssot_exists": true,
    "current_components_count": 0,
    "evidence_declared_count": 0,
    "discovered_readback_artifacts_count": 0,
    "gaps": [
      "warning:current_components"
    ]
  },
  {
    "id": "hermes-skill-learning",
    "type": "knowledge-system",
    "status": "ledgered",
    "audit_status": "pass",
    "ledger_exists": true,
    "ssot_exists": true,
    "current_components_count": 2,
    "evidence_declared_count": 0,
    "discovered_readback_artifacts_count": 0,
    "gaps": []
  },
  {
    "id": "lark",
    "type": "integration",
    "status": "ledgered",
    "audit_status": "pass",
    "ledger_exists": true,
    "ssot_exists": true,
    "current_components_count": 2,
    "evidence_declared_count": 0,
    "discovered_readback_artifacts_count": 0,
    "gaps": []
  },
  {
    "id": "mobile-offline-avatar-travel",
    "type": "mobile-platform/edge-runtime",
    "status": "platform-framed+validated-local-slices",
    "audit_status": "pass",
    "ledger_exists": true,
    "ssot_exists": true,
    "current_components_count": 13,
    "evidence_declared_count": 0,
    "discovered_readback_artifacts_count": 0,
    "gaps": []
  },
  {
    "id": "project-portfolio-os",
    "type": "portfolio-governance",
    "status": "ledgered",
    "audit_status": "warn",
    "ledger_exists": true,
    "ssot_exists": true,
    "current_components_count": 0,
    "evidence_declared_count": 0,
    "discovered_readback_artifacts_count": 10,
    "gaps": [
      "warning:current_components"
    ]
  },
  {
    "id": "uvisa-app-2.0",
    "type": "application",
    "status": "work-project/excluded-unless-user-switches",
    "audit_status": "warn",
    "ledger_exists": true,
    "ssot_exists": true,
    "current_components_count": 0,
    "evidence_declared_count": 0,
    "discovered_readback_artifacts_count": 0,
    "gaps": [
      "warning:current_components"
    ]
  },
  {
    "id": "hermes-self-extension-os",
    "type": "agent-runtime-evolution",
    "status": "validated-active-control-loop-slice",
    "audit_status": "pass",
    "ledger_exists": true,
    "ssot_exists": true,
    "current_components_count": 7,
    "evidence_declared_count": 0,
    "discovered_readback_artifacts_count": 0,
    "gaps": []
  },
  {
    "id": "hermes-control-console",
    "type": "operator-console",
    "status": "validated-local-slice",
    "audit_status": "warn",
    "ledger_exists": true,
    "ssot_exists": true,
    "current_components_count": 0,
    "evidence_declared_count": 0,
    "discovered_readback_artifacts_count": 0,
    "gaps": [
      "warning:current_components"
    ]
  },
  {
    "id": "career-ops",
    "type": "personal-productivity-product",
    "status": "ledgered",
    "audit_status": "warn",
    "ledger_exists": true,
    "ssot_exists": true,
    "current_components_count": 0,
    "evidence_declared_count": 0,
    "discovered_readback_artifacts_count": 0,
    "gaps": [
      "warning:current_components"
    ]
  },
  {
    "id": "single-session-multitopic-trace",
    "type": "hermes-self-architecture",
    "status": "initiated",
    "audit_status": "warn",
    "ledger_exists": true,
    "ssot_exists": true,
    "current_components_count": 0,
    "evidence_declared_count": 0,
    "discovered_readback_artifacts_count": 0,
    "gaps": [
      "warning:current_components"
    ]
  },
  {
    "id": "hermes-capability-model-router",
    "type": "hermes-self-architecture",
    "status": "validated-local-slice",
    "audit_status": "warn",
    "ledger_exists": true,
    "ssot_exists": true,
    "current_components_count": 0,
    "evidence_declared_count": 0,
    "discovered_readback_artifacts_count": 0,
    "gaps": [
      "warning:current_components"
    ]
  },
  {
    "id": "hermes-persona-wake-stage",
    "type": "cross-end-ai-assistant-ux-system",
    "status": "claim-unverified-files-missing",
    "audit_status": "pass",
    "ledger_exists": true,
    "ssot_exists": true,
    "current_components_count": 4,
    "evidence_declared_count": 0,
    "discovered_readback_artifacts_count": 0,
    "gaps": []
  },
  {
    "id": "uaec-h5",
    "type": "work-application/mobile-trading-h5",
    "status": "work-project/excluded-unless-user-switches",
    "audit_status": "warn",
    "ledger_exists": true,
    "ssot_exists": true,
    "current_components_count": 0,
    "evidence_declared_count": 0,
    "discovered_readback_artifacts_count": 0,
    "gaps": [
      "warning:current_components"
    ]
  },
  {
    "id": "hermes-embodied-workflow-os",
    "type": "outer-tooling/embodied-workflow-platform",
    "status": "ordered-high-risk-drain-taskpool-written-outbox-deploy-preflight-hardware-auth-gated",
    "audit_status": "pass",
    "ledger_exists": true,
    "ssot_exists": true,
    "current_components_count": 29,
    "evidence_declared_count": 2,
    "discovered_readback_artifacts_count": 0,
    "gaps": []
  },
  {
    "id": "hermes-fitness-posture-coach",
    "type": "self-use/visual-conversation-domain-pack",
    "status": "projectized_metadata_seed_built_pose_adapter_smoked_fail_closed",
    "audit_status": "pass",
    "ledger_exists": true,
    "ssot_exists": true,
    "current_components_count": 5,
    "evidence_declared_count": 0,
    "discovered_readback_artifacts_count": 0,
    "gaps": []
  }
]

请输出中文，最多 1200 字：
1. 系统审核结论
2. 架构审核结论
3. 多角度矩阵（profile/SSOT/ledger/evidence/readback/work-project-boundary/maturity-claim/portfolio-doctor）
4. 优化方案 P0/P1/P2
5. Fable 5 对本轮是否通过的审计结论（PASS/WARN/FAIL）与反证条件。