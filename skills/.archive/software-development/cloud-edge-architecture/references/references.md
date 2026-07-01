# References

Extracted from `/Users/charles/.hermes/skills/.archive/software-development/cloud-edge-architecture/SKILL.md` on 2026-07-01T08:56:29.614759+00:00 during full core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

## References

- `references/local-cloud-prototype.md` — validated Brain API + Edge Worker prototype design, endpoints, test results, and LAN expansion
- `references/multi-brain-architecture.md` — multi-brain routing pattern, inter-brain communication, shared vs isolated data, hot-plug brain registration, cloud deployment
- `references/production-deployment.md` — production install (local/remote/CI), service management (launchd/systemd), config schema, LAN discovery protocol, auto-connect FSM, Cloudflare Pages deployment, zero-dependency design
- `references/edge-worker-update-management.md` — multi-source update fallback chain (local → GitHub → proxy → Cloudflare), version management with backups and rollback, launchd auto-update scheduling, diagnostic commands for network issues
- `references/lan-cross-device-deployment.md` — one-liner curl deploy pattern for adding edge workers on other LAN computers, self-contained install script, HTTP serving, verification steps, firewall/port pitfalls
- `references/master-slave-connection-testing.md` — master-slave connection testing workflow, config.yaml `main_node` pattern, health check/command execution verification
- `references/remote-multi-repo-git-operations.md` — using Edge Worker API for remote git operations (browse, status, pull, checkout, push) across multiple repos; batch patterns, common pitfalls (divergent branches, tracking branch gone), integration with project profiles
- `references/distributed-management-patterns.md` — complete workflow patterns for multi-node deployments: install-final.sh (atomic install), update-all-nodes.sh (distributed update), monitor-performance.sh (health checks), config-performance.yaml (optimization)
- `references/multi-site-management.md` — Multi-site management architecture: site registration, heartbeat monitoring, load balancing strategies (round-robin/weighted/min-connections/performance), fault detection and task redistribution, architecture link verification pattern, multi-service deployment pitfalls
- `references/agent-team-multi-node.md` — Agent Team multi-node architecture: task pool manager, tree-structured KV cache, agent team manager, multi-model analyzer; includes usage patterns, performance metrics, and integration points
- `references/unified-architecture-pattern.md` — Unified gateway + manager + components pattern for integrating TaskScheduler, KnowledgeManager, ExperienceRatchet, RAGEngine into single entry point
- `references/architecture-refactoring-pattern.md` — Systematic approach to refactoring complex codebases: component analysis, core vs deprecated classification, feature migration, and validation. Use when simplifying architecture while preserving functionality.
