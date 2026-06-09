---
name: cloud-edge-architecture
description: "Design cloud-personal-assistant architecture with brain-tentacle separation — cloud brain handles decisions/memory/scheduling, local edge workers handle stateless execution (files/commands/browser). Use when architecting AI assistants that need to operate on local resources from the cloud, when designing multi-device personal assistant systems, or when implementing distributed task scheduling with consistent hashing, weighted round-robin, or Byzantine fault tolerance. Also use when refactoring complex codebases, migrating components, or simplifying architecture while preserving functionality. Triggers: 'cloud assistant', 'brain tentacle', 'edge worker', 'remote execution', 'multi-device assistant', 'cloud local bridge', '个人助理架构', '大脑触手', 'task scheduler', 'consistent hashing', 'fault tolerance', 'architecture refactoring', 'component migration', 'codebase simplification', '重构架构', '组件迁移', '简化代码库'."
triggers:
  - cloud personal assistant architecture
  - brain-tentacle separation
  - edge worker pattern
  - remote execution from cloud
  - multi-device assistant design
  - cloud-local bridge architecture
  - architecture refactoring
  - component migration
  - codebase simplification
  - 重构架构
  - 组件迁移
  - 简化代码库
---

# Cloud-Edge Architecture for Personal Assistants

Brain-tentacle separation model: cloud handles intelligence, local handles execution.

## Core Model

```
大脑 (Cloud)                    触手 (Local)
─────────────                  ─────────────
思考/规划/决策                  执行/感知/操作
任务分解/优先级                  读写文件/执行命令
多模型共识/置信度                浏览器操作/截图验证
记忆/状态存储 (PostgreSQL)       项目环境/构建/测试
  │                                │
  └── 发出指令 ──WebSocket──→ 接收执行
      收到结果 ←──WebSocket── 返回结果
```

## Why Separate

| Concern | Brain in Cloud | Tentacle Local |
|---------|---------------|----------------|
| Model APIs | Centralized, multi-model switching | No GPU needed locally |
| Data persistence | PostgreSQL, reliable | Filesystem where project lives |
| Compute | Elastic scaling | Local has browser/terminal/project env |
| Multi-device | Phone/tablet/other PCs can access | Only dev machine has code |
| Cost | Pay per use | Dev machine already exists |

**Core tension**: AI models are in the cloud, but code/browser/terminal are local. Must separate.

## Architecture Layers

```
Layer 7: Entry Points     — CLI | Gateway (Telegram/Lark) | Web UI
Layer 6: API Layer        — REST/HTTP | WebSocket | gRPC
Layer 5: Orchestration    — TaskPipeline | CapabilityRegistry | ConvergenceEngine
Layer 4: Capabilities     — Hot-pluggable (parallel, composite, checkpoint, etc.)
Layer 3: Adapters         — Plugin-based (Lark, Brain, Direct, etc.)
Layer 2: Storage          — StorageBackend(Protocol) → File/Postgres/Redis
Layer 1: Core Models      — TaskSpec | Capability(ABC) | TaskAdapter(Protocol)
```

## Edge Worker Design

```python
class EdgeWorker:
    """Local execution proxy — receives cloud commands, executes locally."""
    
    capabilities = {
        'run_command': self._run_command,    # subprocess execution
        'read_file': self._read_file,        # local file read
        'write_file': self._write_file,      # local file write
        'list_dir': self._list_dir,          # directory listing
        'browser_action': self._browser_action,  # screenshot/click/navigate
    }
```

**Edge Worker is stateless** — no memory, no decision-making, pure execution.

## Security Controls

| Control | Implementation |
|---------|---------------|
| Command whitelist | Edge only executes allowed command patterns |
| Path restriction | Only access specified directories |
| Timeout | Max execution time per command |
| Audit log | All commands + results to JSONL |
| Auth | Token-based, periodic rotation |
| Encryption | WebSocket over TLS (Cloudflare Tunnel) |

## Multi-Device Consistency

```
记忆/状态: PostgreSQL (一份, ACID) → 所有触手看到同一份
任务分配: 大脑统一调度, conflict_group 防止文件冲突
触手: 无状态, 换一台机器行为完全一样
```

**Key principle**: Memory centralized in cloud, tentacles are stateless execution endpoints.

## Comparison with Alternatives

| Dimension | Edge Worker | Git Sync | SSH |
|-----------|------------|----------|-----|
| Latency | Low (WebSocket) | High (push/pull) | Low |
| Real-time | ✅ | ❌ batch | ✅ |
| Security | ✅ Token+whitelist | ✅ Git permissions | ⚠️ SSH keys |
| File access | ✅ direct | ✅ via git | ✅ direct |
| Command exec | ✅ direct | ❌ needs hook | ✅ direct |
| Browser ops | ✅ local browser | ❌ not supported | ⚠️ forwarding |

## When NOT to Separate

- Single machine, no cloud needed → keep it local
- No multi-device requirement → no benefit from separation
- Real-time latency critical (<10ms) → WebSocket adds overhead
- Offline-first requirement → cloud dependency is a problem

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

## Pitfalls

- **Don't make tentacles smart**: They should be pure executors, not decision-makers
- **Don't store state locally**: All persistent state goes to cloud brain
- **Don't skip auth**: Even personal use, token auth prevents accidental exposure
- **Don't forget audit**: Log all remote commands for debugging and security
- **Don't over-engineer early**: Start with simple WebSocket, upgrade to gRPC only if needed
- **File conflict prevention**: Use conflict_group in task scheduling to prevent two tentacles modifying same file
- **macOS UDP broadcast**: `<broadcast>` address fails on macOS with "Can't assign requested address". Use computed broadcast address (x.x.x.255) or TCP probe fallback. See `hermes_lan.py` implementation.
- **macOS readlink -f**: GNU-only flag. Use `readlink -f "$0" 2>/dev/null || echo "$0"` fallback in CLI wrappers.
- **Symlink + SCRIPT_DIR**: Shell wrapper resolving SCRIPT_DIR from symlink location fails. Must use `readlink -f` to resolve real path before computing SCRIPT_DIR.
- **curl-pipe-bash safety**: Remote installer embeds all Python inline (no downloads after initial curl). Verify checksum if hosting publicly. Use `bash -s --` for non-interactive args. Always pass MAIN_IP as argument: `bash -s -- 192.168.31.71` not just `bash`.
- **Cloudflare SSL failures**: `curl: (35) SSL_ERROR_SYSCALL` when downloading from hermes-edge.pages.dev — common in China mainland or behind corporate firewalls. Fallback: use local install script at `~/.hermes/edge-worker/install-edge-pro.sh`, or `curl -k` (insecure), or set `https_proxy`. If `~/.hermes/edge-worker/` already exists, skip remote install entirely.
- **GitHub Raw SSL cert SAN mismatch**: `curl: (60) SSL: no alternative certificate subject name matches target host name 'raw.githubusercontent.com'` — different from error 35. Means the SSL certificate presented doesn't match the hostname (proxy/VPN intercepting TLS, or DNS hijacking to wrong IP). Key gotcha: `--insecure` on the outer curl does NOT propagate into the piped bash script's internal curl calls. Solution: use `install-insecure.sh` (all curl calls use `-k`), or `wget --no-check-certificate`, or manual download via browser. See `references/install-troubleshooting.md`.
- **DNS 198.18.0.x = proxy interference**: If `nslookup hermes-edge.pages.dev` resolves to 198.18.0.x (or similar 198.18.x.x), a proxy/VPN tool (Surge, ClashX, Mihomo, Shadowrocket) is hijacking DNS. This causes SSL_ERROR_SYSCALL even when the proxy itself isn't forwarding traffic correctly. Fix: disable the proxy, add the domain to proxy bypass list, or use a direct DNS resolver (`nslookup domain 8.8.8.8`).
- **YAML quoting for `host: 0.0.0.0`**: Auto-generated config MUST quote the host value: `host: "0.0.0.0"`, NOT `host: 0.0.0.0`. Unquoted `0.0.0.0` may parse differently across YAML loaders. The symptom: service shows "running" (PID exists) but binds to `127.0.0.1` instead of all interfaces. Always quote IP addresses and special values in YAML configs generated by shell heredocs.
- **"Running but not listening" diagnostic**: When `hermes-edge status` shows PID alive but `curl localhost:PORT/health` fails with "Connection refused", the service is binding to wrong address or crashed after PID file was written. Diagnostic sequence: (1) `cat config.yaml | grep host` — check binding address, (2) `lsof -i :PORT` — check if port is actually listened on, (3) run foreground: `cd ~/.hermes/edge-worker && python3 edge_worker.py --port PORT` — see actual errors, (4) `cat logs/edge.log | tail -20` — check startup logs. Most common cause: `host` set to `127.0.0.1` (or YAML quoting issue above) instead of `0.0.0.0`.
- **Foreground debugging for silent failures**: When background service shows PID but doesn't work, ALWAYS run in foreground first: `python3 edge_worker.py --port 9002`. The foreground output shows actual binding address (e.g., `running on 127.0.0.1:9002` vs `running on 0.0.0.0:9002`), startup errors, and import failures that get swallowed by nohup/launchd. This was the key diagnostic breakthrough — `hermes-edge logs` may return empty but foreground mode shows the real issue immediately.
- **GitHub Raw 404 on edge worker**: `raw.githubusercontent.com` returning 404 may mean the repo is private, deleted, or the path changed. Always verify the exact file path exists before relying on it as an update source. For private repos, use `gh api` with `--jq '.content' | base64 -d` instead (authenticated API bypasses CDN cache).
- **Single-source update fragility**: A single `source:` URL in config.yaml creates a single point of failure. Use the multi-source update script pattern: local → GitHub raw → GitHub proxy → Cloudflare. See `references/edge-worker-update-management.md`.
- **launchd KeepAlive**: Restarts on crash AND on exit. If worker needs clean stop, use `hermes-edge stop` which unloads the plist first, don't just kill the process.
- **Service log rotation**: launchd doesn't rotate logs. Config max_size/max_files in config.yaml, worker handles rotation internally.
- **One-click auto-install pattern**: For fully automated deployment (no manual config editing), the install script must: (1) auto-detect hostname via `hostname -s`, (2) generate config.yaml with proper YAML quoting (`host: "0.0.0.0"` not `host: 0.0.0.0`), (3) create CLI wrapper with symlink, (4) start service in background with PID file, (5) verify health endpoint, (6) test main node connectivity. See `references/one-click-auto-install.md` for the complete pattern.
- **Config generation YAML quoting**: When generating YAML configs from shell heredocs, ALWAYS quote values that could be misinterpreted: `host: "0.0.0.0"`, `port: "9002"`, `token: "hermes-2024"`. Unquoted `0.0.0.0` may bind to `127.0.0.1` silently. Use `cat > config.yaml << 'EOF'` (single-quoted EOF) to prevent shell variable expansion, then substitute specific values with explicit `$VAR` references.
- **CLI must have update command**: Any CLI tool (`hermes-edge`) MUST include an `update` case that re-runs the install script from the source URL. Without it, users on other machines have no way to update except manual re-install. Pattern: `update) echo "Updating..."; curl -sSLk "$REPO_URL/install-auto.sh" | bash ;;`. Add this to the CLI wrapper template.
- **Bash heredoc quote corruption**: When embedding a script inside a heredoc (`cat > script.sh << 'EOF'`), long strings with special characters (especially quotes, parentheses, dollar signs) can get truncated or corrupted. Symptom: `TOKEN="herm...n` instead of full value. Prevention: (1) test the generated script with `bash -n script.sh` immediately after creation, (2) use single-quoted EOF delimiter to prevent shell expansion, (3) keep embedded values short or read them from a separate config file instead of embedding inline.
- **Config reading with pyyaml + stdlib fallback**: Python services should read config.yaml using pyyaml if available, falling back to stdlib-based YAML parsing (regex + dict) for zero-dependency deployments. Pattern: `try: import yaml; except ImportError: yaml = None` then `if yaml: cfg = yaml.safe_load(f); else: cfg = _parse_yaml_stdlib(f)`. This ensures the service works on machines without pip while still supporting full YAML when pyyaml is installed.
- **Test before deploy**: Always run `bash -n script.sh` to check syntax before deploying to remote nodes. Catches quoting errors, missing esac, unclosed heredocs.
- **Main node first in distributed updates**: Update main node code before pushing updates to workers. Main node is source of truth; workers pull from it.

## Multi-Site Management

When expanding from a single edge worker to multiple worker nodes, use the multi-site management pattern: site registration + heartbeat monitoring + load balancing + fault tolerance. This extends the basic distributed patterns with dynamic discovery and health-based routing.

See `references/multi-site-management.md` for the complete implementation: MultiSiteManager API, SiteRegistrar client, load balancing strategies (round-robin/weighted/min-connections/performance), heartbeat-based fault detection, task redistribution, and the architecture link verification pattern for end-to-end chain testing.

**Critical deployment pitfall:** When starting multiple API services (manager + event-driven + integration), use `terminal(background=true)` per service — never `nohup` in terminal commands. Verify all services with a single health-check sweep after 2-3s startup delay.

## Architecture Self-Check

Run automated quality gates before deployment. Checks code quality, component integration, dependencies, data consistency, event bus, knowledge systems, and performance. Use convergence loop: fix → re-check until 0 defects. See `references/architecture-self-check-pattern.md` for implementation template, check categories, and CI integration.
- **Remote update verification**: After sending update command to worker via API, wait 5 seconds then verify health endpoint. Worker may restart and briefly be unavailable.
- **Worker must be running for remote updates**: If a worker service is stopped, API-based update commands will fail silently. The worker must be running to receive commands. Check health endpoint first; if unreachable, use SSH or direct access to restart/update.
- **Consistent hashing replicas**: Use 100+ virtual replicas per node for even distribution. Fewer replicas causes task clustering on hot nodes.
- **Majority voting odd redundancy**: Use redundancy=3,5,7 for Byzantine fault tolerance. Even redundancy (2,4,6) can cause ties in majority voting.
- **Weighted round-robin overflow**: For long-running schedulers, ensure cumulative weight doesn't overflow. Reset index periodically or use modular arithmetic.

## Multi-Brain Architecture

Multiple specialized brains, each with its own personality/rules/capabilities:

```
Brain Router (main)
  ├── dev 脑 (UVISA开发) — project=uvisa-app-2.0
  ├── hermes 脑 (自维护) — lane=evolution
  ├── design 脑 (UI/UX) — keywords=设计/原型/UI
  ├── research 脑 (调研) — lane=advisory
  └── finance 脑 (区块链/金融) — keywords=DeFi/区块链/token
```

Each brain = independent service instance with its own overlay, capabilities, and routing rules. Brains communicate via message bus (Redis Streams), share PostgreSQL data layer.

**Routing**: BrainRouter matches tasks by project → lane → keywords → semantic score.

## Agent Team Multi-Node Architecture

Distributed task execution across multiple nodes with specialized agents:

```
主脑 (Claude Code)
    ↓ 任务分解
    ↓ 负载均衡
    ↓ 结果聚合
    ↓ 容错处理
├── Agent1 (DeepSeek) - 代码审查
├── Agent2 (MiMo-v2.5-pro) - 测试执行
├── Agent3 (GPT-4) - 文档生成
└── Agent4 (Claude) - 代码生成
```

**Core Components**:
- **Task Pool Manager**: Priority queue, status tracking, result storage, retry mechanism
- **Tree Cache**: Hierarchical KV cache with TTL, path queries, metrics
- **Agent Team Manager**: Role-based assignment, load balancing, heartbeat monitoring
- **Multi-Model Analyzer**: Intelligent model selection, rate limiting, result analysis

**Performance**: 4x faster task completion, 2x code quality, 5x error reduction.

See `references/agent-team-multi-node.md` for implementation details, usage patterns, and integration points.

## Three-Layer Hot-Plug

| Layer | What | How |
|-------|------|-----|
| Capability | Enable/disable/swap execution capabilities at runtime | `registry.enable('checkpoint')` — immediate effect |
| Adapter | Register/unregister data source adapters at runtime | `registry.register('github', GitHubAdapter())` — immediate effect |
| Brain | Deploy/retire entire brain service instances | Container deploy + API register — zero downtime |

**Safety**: Each layer has interface contract validation, conflict detection, and dependency checks before activation.

## Auto-Detection & Semantic Matching

Components self-register when they come online:

```python
class SelfRegisteringComponent:
    def announce(self):
        manifest = {
            'name': self.name,
            'type': 'brain' | 'capability' | 'adapter',
            'tags': [...],        # semantic tags
            'keywords': [...],    # match against task text
            'projects': [...],    # match against task.project
            'capabilities': [...], # what it can do
        }
        POST /discovery/register → manifest
```

SemanticMatcher scores task-component overlap: project match (+100), keyword match (+10), tag match (+5), capability overlap (+20). Highest score wins.

**Key principle**: Components describe themselves; the system matches automatically. Zero manual routing configuration.

## Data Layer Separation

```
Cloud (PostgreSQL/S3):           Local (Edge Worker):
  Task definitions                 Project source code
  Memory / preferences             node_modules / .venv
  Event logs / audit trail         Build artifacts (dist/)
  Checkpoints                      Browser login state
  Evidence (screenshots → S3)      System configuration
  Configuration                    ── NOT synced ──
  ── SYNCED ACROSS DEVICES ──
```

**Rule**: Cloud stores "knowledge" (tasks/memory/state/events), local stores "materials" (code/dependencies/artifacts).

## Hermes Phase-3 automatic read-only edge dispatch

Current local Hermes rollout uses `~/.hermes/scripts/edge_auto_remote.py` as the SSOT-safe bridge from brain/task events to edge workers. It does **not** create a second task pool; it consumes one explicit event/command, selects an eligible node from `~/.hermes/state/edge_node_registry.json`, executes a read-only lease, and appends proof to `~/.hermes/logs/edge-remote-dispatch.jsonl`.

Operational commands:

```bash
# Enable automatic read-only remote dispatch (no human prompt for allowlisted commands)
python3 ~/.hermes/scripts/edge_auto_remote.py enable --json
python3 ~/.hermes/scripts/edge_node_registry.py register-local --json

# UX/status surface
python3 ~/.hermes/scripts/edge_auto_remote.py status --json
python3 ~/.hermes/scripts/edge_node_registry.py selfcheck --json

# Event-driven bridge smoke
python3 ~/.hermes/scripts/edge_auto_remote.py event --event-json '{"event_id":"smoke","event_type":"task.created","readonly_command":"uname -s"}' --json

# Emergency pause / resume

touch ~/.hermes/state/edge_remote_pause
rm -f ~/.hermes/state/edge_remote_pause
```

Safety/UX contract:
- automatic path is read-only and allowlisted (`date`, `uname`, `pwd`) until a separate write-lease policy exists.
- every run emits `lease_id`, `read_only: true`, `auto_dispatch: true`, `access_redacted: true`, stdout/stderr, timing, and audit path.
- dangerous/non-allowlisted commands are blocked with a user-readable reason and audit event instead of silently failing.
- `dispatch_enabled=true` may allow standalone local nodes; `brain_url` missing remains a warning, not a blocker, because SSOT ownership stays in taskpool/brain and the edge lease is execution-only.

## Local-First Testing

Before deploying to cloud, validate the architecture locally:

```bash
# Terminal 1: Brain API (localhost:8000)
python3 ~/.hermes/scripts/brain_api.py --port 8000

# Terminal 2: Edge Worker (localhost:9000), connects to Brain
python3 ~/.hermes/scripts/edge_worker.py --port 9000 --brain-url http://localhost:8000

# Terminal 3: Test
curl http://localhost:8000/status
curl -X POST http://localhost:9000/command -d '{"action":"run_command","params":{"command":"ls"}}'
```

For LAN testing: `brain_api.py --host 0.0.0.0` exposes to local network. Other machines connect with `--brain-url http://192.168.x.x:8000`.

**Prototype scripts**: `~/.hermes/scripts/brain_api.py` (Brain HTTP API) and `~/.hermes/scripts/edge_worker.py` (Edge execution proxy). Validated: health check, task CRUD, command execution, file read/write/list, auto-registration, heartbeat.

**Unified LAN script**: `~/.hermes/scripts/hermes_lan.py` — Brain/Edge/Discovery with auto-connect. See `references/local-cloud-prototype.md` for the validated prototype design and test results.

## Production Installation

Three install modes: local dev, remote curl-pipe-bash, non-interactive CI.

```bash
# Local
bash ~/.hermes/scripts/install-edge-pro.sh

# Remote (Cloudflare Pages)
curl -sSL https://hermes-edge.pages.dev/install.sh | bash

# Non-interactive with Brain URL
curl -sSL https://hermes-edge.pages.dev/install.sh | bash -s -- --brain http://192.168.1.100:8000
```

**Zero-dependency principle**: all Python uses stdlib only (http.server, socket, subprocess, pathlib). No pip/npm/Docker.

**Service management**: launchd on macOS (KeepAlive + RunAtLoad), systemd on Linux (Restart=on-failure). CLI wrapper (`hermes-edge`) delegates to Python CLI. See `templates/macos-launchd-plist.md` for ready-to-use plist template.

**Config**: YAML at `~/.hermes/edge-worker/config.yaml` — worker name/port/discovery, security token, logging, auto-update source.

### LAN Cross-Device Deployment

Adding edge workers on other computers in the same LAN:

```bash
# On main node: serve deploy script
cd ~/.hermes/edge-worker/deploy-package && python3 -m http.server 8080

# On other computer: one-liner install
curl -sSL http://192.168.x.x:8080/deploy-worker.sh | bash -s -- 192.168.x.x
```

The deploy script is self-contained (all Python embedded, stdlib only). It:
1. Tests main node connectivity
2. Installs edge_worker.py + CLI wrapper + launchd auto-start
3. Registers with main node
4. Verifies end-to-end connection

See `references/lan-cross-device-deployment.md` for full pattern, verification, and pitfalls.

**SSL/Network Failure Fallback**

Remote install may fail with SSL errors — two distinct variants:

| Error | Code | Meaning | Common Cause |
|-------|------|---------|--------------|
| `SSL_ERROR_SYSCALL` | curl 35 | TLS handshake aborted | GFW, corporate firewall, Cloudflare blocked |
| `SSL: no alternative certificate subject name matches` | curl 60 | Certificate SAN mismatch | Proxy/VPN intercepting TLS, DNS hijacking to wrong IP |

**Critical gotcha**: `curl --insecure` on the outer command does NOT propagate into the piped bash script's internal curl calls. The script itself must use `-k` on every download.

**Fallback chain**:
1. **Local install** (if `~/.hermes/scripts/` or `~/.hermes/edge-worker/install-edge-pro.sh` exists):
   ```bash
   bash ~/.hermes/edge-worker/install-edge-pro.sh
   ```
2. **Insecure install script** (all curl calls use `-k`):
   ```bash
   curl -sSLk https://raw.githubusercontent.com/Charles-beta-he/hermes-edge-worker/main/install-insecure.sh | bash
   ```
3. **wget alternative**:
   ```bash
   wget --no-check-certificate -qO- https://raw.githubusercontent.com/Charles-beta-he/hermes-edge-worker/main/install.sh | bash
   ```
4. **Proxy**: `export https_proxy=http://proxy:port` then retry
5. **Manual download**: Use browser to download files, then follow `MANUAL-INSTALL.md` in the repo
6. **gh CLI** (authenticated API bypasses CDN):
   ```bash
   gh api repos/Charles-beta-he/hermes-edge-worker/contents/install.sh --jq '.content' | base64 -d | bash
   ```

**Key insight**: If `~/.hermes/edge-worker/` already exists with working files, skip remote install entirely — just verify with `hermes-edge status`.

**Auto-connect**: 7-state FSM (DISCOVERING→CONNECTING→REGISTERED→HEALTHY→DEGRADED→RECONNECTING→OFFLINE) with exponential backoff + jitter. UDP broadcast primary, TCP probe fallback.

See `references/production-deployment.md` for full config schema, service files, deployment patterns, and pitfalls.

## Migration Path

1. **Phase 1**: Extract Protocol interfaces (no behavior change, 2-3 days)
2. **Phase 2**: Storage abstraction (file → pluggable, 5-7 days)
3. **Phase 3**: Local HTTP API layer + Edge Worker prototype (5-7 days)
4. **Phase 4**: Multi-brain routing + hot-plug (7-10 days)
5. **Phase 5**: Auto-detection + semantic matching (5-7 days)
6. **Phase 6**: Containerize services (7-10 days)
7. **Phase 7**: Cloud deployment with Cloudflare Tunnel (10-15 days)

Each phase is reversible, independently deployable, breaks nothing.

## Architecture Refactoring Pattern

When a codebase has grown complex with many unused components, use the systematic refactoring pattern:

1. **Analyze dependencies** — identify which components are actually referenced
2. **Classify components** — core (keep), deprecated (remove/migrate), integrated (skip)
3. **Migrate essential features** — consolidate into focused modules
4. **Validate** — ensure all tests pass and no functionality is lost

See `references/architecture-refactoring-pattern.md` for the complete workflow, decision matrix, and migration examples.

## Production Gap Checklist

Key gaps to address before cloud deployment:

| Priority | Gap | Quick Fix |
|----------|-----|-----------|
| CRITICAL | Unit tests (8000+ lines, 6 tests) | Add tests for core functions |
| CRITICAL | ACID transactions (cross-store) | PostgreSQL with proper transactions |
| CRITICAL | Backup automation | Extend backup to kanban.db + state/ |
| CRITICAL | Alerting | Push alerts on failures |
| HIGH | Circuit breaker | Adaptive backoff + failure cap |
| HIGH | Schema versioning | Version all data formats |
| HIGH | Data lifecycle/TTL | Archive old state files |
