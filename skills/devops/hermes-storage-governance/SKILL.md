---
name: hermes-storage-governance
description: "Use when hermes 存储治理: state.db FTS 膨胀治理、会话 TTL、快照清理、自动 cron。防止多模型运行导致磁盘膨胀。."
triggers:
  - "storage cleanup"
  - "disk space"
  - "state.db"
  - "存储治理"
  - "磁盘清理"
  - "continuation backlog"
  - "packet backlog"
  - "continuation gc"
---

# Hermes 存储治理

## Overview

Hermes 存储治理: state.db FTS 膨胀治理、会话 TTL、快照清理、自动 cron。防止多模型运行导致磁盘膨胀。. It is organized as an evidence-grounded review gate: separate findings from preferences, cite the inspected artifact or state, and keep adjacent workflows out of scope.

## When to Use

Use this skill when the request matches the `hermes-storage-governance` trigger and the domain-specific boundaries in this skill apply.

Do not use it for:
- generic one-off questions that do not need this workflow;
- neighboring specialist workflows with a narrower matching skill;
- durable memory or project-profile writes unless this skill explicitly governs that landing zone.

## 问题
多模型运行导致 ~/.hermes 膨胀:
- state.db: FTS trigram 索引 5.5x 膨胀 (293MB 数据 → 1.6GB 索引)
- 会话无 TTL, 永久保留
- snapshots/checkpoints 无清理

## 清理脚本
~/.hermes/scripts/hermes-cleanup.py
```
--dry-run          预览
--session-ttl N    会话保留天数 (默认 7)
--snapshot-ttl N   快照保留天数 (默认 3)
--checkpoint-ttl N 检查点保留天数 (默认 3)
--log-ttl N        日志保留天数 (默认 7)
--aggressive       保留 1 天
```

## 自动 cron
已配置: 每天 4:00 AM 运行, 保留 7 天会话

## 手动清理
```bash
# 1. 删除旧会话
python3 ~/.hermes/scripts/hermes-cleanup.py --session-ttl 3

# 2. VACUUM state.db
sqlite3 ~/.hermes/state.db "VACUUM;"

# 3. 清理 WAL
sqlite3 ~/.hermes/state.db "PRAGMA wal_checkpoint(TRUNCATE);"

# 4. 清理旧快照/检查点
python3 ~/.hermes/scripts/hermes-cleanup.py --snapshot-ttl 1 --checkpoint-ttl 1
```

## 关键 Pitfalls

1. **WAL 文件膨胀**: state.db-wal 可能增长到 GB 级别。VACUUM 后必须执行 `PRAGMA wal_checkpoint(TRUNCATE)` 清空 WAL。

2. **Unix 时间戳**: sessions.started_at 存储 Unix 时间戳 (float), 不是 ISO 字符串。SQLite 比较用 `strftime('%s', 'now', '-3 days')` 而非 `datetime('now', '-3 days')`。

3. **FTS trigram 索引**: messages_fts_trigram 产生 ~4x 膨胀 (293MB 数据 → 1.2GB 索引)。监控: `sqlite3 state.db "SELECT name, SUM(pgsize) FROM dbstat WHERE name LIKE '%fts%' GROUP BY name"`。

4. **清理顺序**: 先删 messages, 再删 sessions (外键约束)。删完后 `INSERT INTO messages_fts(messages_fts) VALUES('rebuild')` 重建 FTS。

## 效果
Before: 9.3GB → After: 4.3GB (释放 5.0GB, -54%)

## state.db 构成分析
| 组件 | 大小 | 说明 |
|------|------|------|
| messages_fts_trigram_data | 815MB | 三元组 FTS 索引 (最大!) |
| messages_fts_trigram_content | 410MB | 三元组内容 |
| messages_fts_content | 410MB | 普通 FTS 内容 |
| messages_fts_data | 113MB | 普通 FTS 数据 |
| messages | 516MB | 实际消息数据 |
| sessions | 155MB | 会话元数据 |
| FTS 总计 | ~1.6GB | 293MB 数据 → 5.5x 膨胀 |

## Pitfalls

1. **Unix timestamps**: `sessions.started_at` stores Unix timestamps (float), NOT ISO dates. Use `strftime('%s', 'now', '-3 days')` for SQLite comparisons, NOT `datetime('now', '-3 days')`. Wrong comparison: `started_at < '2026-05-10...'` always matches because string '1778668710' < '2026-05-10'.

2. **WAL file growth**: After heavy writes (multi-model runs), `state.db-wal` can grow to 2GB+. Always checkpoint after cleanup: `sqlite3 state.db "PRAGMA wal_checkpoint(TRUNCATE)"`. Check: `ls -lh ~/.hermes/state.db*`.

3. **FTS rebuild after pruning**: After DELETE operations, rebuild FTS indexes or they retain deleted data:
   ```sql
   INSERT INTO messages_fts(messages_fts) VALUES('rebuild');
   INSERT INTO messages_fts_trigram(messages_fts_trigram) VALUES('rebuild');
   ```

4. **VACUUM after DELETE**: SQLite doesn't reclaim space after DELETE. Must VACUUM: `sqlite3 state.db "VACUUM"`. Before VACUUM, check file size: `ls -lh ~/.hermes/state.db`.

5. **Snapshot cleanup order**: Clean snapshots BEFORE VACUUM. Snapshots reference state.db pages; cleaning them first avoids stale references.

## Brain 任务文件膨胀治理

### 问题
`~/Documents/brain/05-实践与项目/tasks/` 下的 `.md` 任务文件可能因 YAML frontmatter 中的转义爆炸膨胀到 60-120MB。

**已知触发字段**:
- `iceberg_signals`: 嵌套 JSON 字符串在 YAML 序列化时产生指数级反斜杠链，120MB 单行
- `evidence_bundle`: 包含 URL 的列表字段，类似转义爆炸

### 诊断
```bash
# 找出 >100KB 的任务文件
find ~/Documents/brain/05-实践与项目/tasks/ -name "*.md" -size +100k -exec wc -c {} \; | sort -rn

# 定位膨胀行（通常只有1行）
python3 -c "
with open('FILEPATH', 'r', errors='replace') as f:
    for i, line in enumerate(f, 1):
        if len(line) > 5000:
            print(f'Line {i}: {len(line)/1024/1024:.1f}MB | {line[:80]}...')
"
```

### 修复

**一键脚本**: `scripts/fix-task-escape-explosion.py`
```bash
# 扫描并修复所有 >100KB 的任务文件
python3 scripts/fix-task-escape-explosion.py

# 预览模式
python3 scripts/fix-task-escape-explosion.py --dry-run

# 指定文件
python3 scripts/fix-task-escape-explosion.py FILE1.md FILE2.md
```

### 防御
写入 `iceberg_signals` 或 `evidence_bundle` 时使用 YAML 列表而非嵌套 JSON 字符串:
```yaml
# 坏: 嵌套 JSON → 转义爆炸
iceberg_signals: '{"key": "value with \\"quotes\\""}'

# 好: 原生 YAML 列表
iceberg_signals:
  - key: value
    note: no nested quoting
```

## Continuation Packet Backlog (NEW — 2026-05)

### Problem
Multi-turn continuations generate packets in `~/.hermes/state/continuations/active/`. Without cleanup, these accumulate indefinitely. Observed: 1559 active + 953 archived packets.

### Scripts
```bash
# Dry-run (preview what would be archived/deleted)
python3 ~/.hermes/scripts/continuation-gc.py --dry-run

# Execute cleanup
python3 ~/.hermes/scripts/continuation-gc.py
```

### Policy
- Active packets >7 days → archived (with metadata.gced=true)
- Archived packets >30 days → deleted
- Backpressure: MAX_ACTIVE_CONTINUATIONS=100 in agent/continuation.py
- New packets exceeding cap → auto-archived with metadata.overflow_archived=true

### Monitoring
```bash
# Active count
ls ~/.hermes/state/continuations/active/ 2>/dev/null | wc -l

# Archived count
ls ~/.hermes/state/continuations/archived/ 2>/dev/null | wc -l
```

### Academic Basis
Credit-based backpressure (Akidau et al., Streaming Systems, 2018). Reactive Streams (2015). See hermes-self-audit/references/self-healing-architecture.md for full framework.

## 完整健康检查流程 (8 步)

当用户要求"根因排查"或"全面健康检查"时，执行以下 8 步:

1. **state.db 清理**: 清理旧会话 → VACUUM → WAL checkpoint → integrity_check
2. **Memory 压缩**: 读取 MEMORY.md/USER.md，压缩到 80% 以下 (MEMORY=1760, USER=1100)
3. **.hermes 源泄露检测**: `find ~/.hermes/hermes-agent -name ".hermes" -type d 2>/dev/null` — 如果输出非空则有泄露
4. **Kanban 回收**: `find ~/.hermes -name "kanban.db.corrupt.*.bak" -o -name "kanban.db.bak.*"` → 移到 `~/.hermes/backups/kanban-corrupt-$(date +%Y%m%d)/`
5. **Selfcheck 修复**: 运行 `hermes_hook_registry_selfcheck.py`，修复 python3 路径解析 bug (见下文 Pitfall #6)
6. **Git 整理**: 备份分支 → stage → commit pending changes
7. **Cron 恢复**: 检查暂停的 cron jobs，恢复非废弃的 (保留 rokid 等已废弃的暂停)
8. **Profile 搭建**: 为 personal/work profile 创建 .env 文件

## 监控命令
```bash
# FTS 膨胀检查
sqlite3 ~/.hermes/state.db "SELECT name, SUM(pgsize)/1024/1024 || 'MB' FROM dbstat WHERE name LIKE '%fts%' GROUP BY name ORDER BY SUM(pgsize) DESC"

# WAL 大小检查
ls -lh ~/.hermes/state.db-wal

# 会话数量
sqlite3 ~/.hermes/state.db "SELECT COUNT(*) FROM sessions"

# 最旧会话
sqlite3 ~/.hermes/state.db "SELECT datetime(MIN(started_at), 'unixepoch', 'localtime') FROM sessions"

# Hook registry selfcheck (完整)
python3 ~/.hermes/scripts/hermes_hook_registry_selfcheck.py

# .hermes 源泄露
find ~/.hermes/hermes-agent -name ".hermes" -type d 2>/dev/null
```

## Pitfalls (续)

6. **selfcheck python3 路径解析 bug**: `hermes_hook_registry_selfcheck.py` 中 `command.split()[0]` 会把 `python3` 当作文件路径解析。当 shell hook 命令是 `python3 ~/.hermes/scripts/foo.py` 时，`command.split()[0]` 返回 `python3`，然后 `_expand("python3")` 变成 `CWD/python3`，不存在。修复: 用 `_resolve_script_path()` 跳过已知解释器 (`python3`, `python`, `bash`, `sh`, `node`, `ruby`, `/usr/bin/env`)。

7. **新 hook 脚本缺执行权限**: 添加新的 shell hook 脚本后必须 `chmod +x`。selfcheck 会检查 `os.access(cmd_path, os.X_OK)`，缺失会报 "not executable"。预防: 在 hook registry 中注册新脚本时同步设置权限。

## Verification Checklist

- [ ] Preconditions, scope, and tool availability were checked before following this workflow.
- [ ] The key output artifacts, commands, or side effects were verified by read-back or direct inspection.
- [ ] Any remaining uncertainty, blocker, or human handoff was stated explicitly.
- [ ] Findings include evidence, severity/rubric calibration, and false-positive controls.
