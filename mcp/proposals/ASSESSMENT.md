# MCP Proposals — Agent Assessment (2026-04-26)

## 1. git_operations (56x, 11 skills)
**Decision: IMPLEMENTED**
- Created `~/.hermes/scripts/mcp-git-server.py` — MCP stdio server with 6 tools
- Registered in `~/.hermes/config.yaml` as `mcp_servers.git`
- Tools: git_status, git_log, git_diff, git_branch, git_commit, git_add
- Verdict: High frequency (56 occurrences) across critical skills (github-* suite)

## 2. http_requests (38x, 13 skills)
**Decision: REJECTED**
- Pattern is primarily `curl` calls in skills like arxiv (12x) and ascii-art (10x)
- Already covered by `web_search` + `web` toolset capabilities
- Building an HTTP client MCP would duplicate existing tool infrastructure
- The skills using curl do so for specific API calls that need custom headers/params
- Verdict: Low ROI — existing tools sufficient

## 3. package_manager (16x, 11 skills)
**Decision: REJECTED**
- Pattern is `npm install` / `pnpm add` / `yarn` one-liners
- Always runs inside `terminal` tool, not worth abstracting to MCP
- Wrapping one-line commands in MCP adds latency with no benefit
- Verdict: Terminal already handles this perfectly

## 4. python_packages (53x, 24 skills)
**Decision: REJECTED**
- Pattern is `pip install` / `pip3 install` in ML training skills
- Same reasoning as package_manager — one-line terminal commands
- 24 skills is high but each usage is just "pip install <package>"
- Verdict: Terminal handles this perfectly. MCP would add no value

## 5. file_searching (51x, 20 skills)
**Decision: REJECTED**
- The proposal itself says "已有 search_files 工具, 无需封装"
- Pattern is `grep` / `rg` which are already covered by `search_files` tool
- Verdict: Already solved. Redundant to re-implement as MCP

---
Summary: 1 implemented, 4 rejected. See `~/.hermes/scripts/mcp-git-server.py` and `~/.hermes/config.yaml` for the installed MCP server.
