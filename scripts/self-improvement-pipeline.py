#!/usr/bin/env python3
"""
Self-Improvement Pipeline — 自进化优先调度层
统一信号聚合 → 优先级排序 → 自主执行

用法:
  # 查看所有信号源的分析和建议
  python3 ~/.hermes/scripts/self-improvement-pipeline.py

  # 全量分析 + 写入 action list
  python3 ~/.hermes/scripts/self-improvement-pipeline.py --write

  # 自主执行模式（自动 dispatch 到各 actuator）
  python3 ~/.hermes/scripts/self-improvement-pipeline.py --auto-exec

  # 只读模式查看当前优先级队列
  python3 ~/.hermes/scripts/self-improvement-pipeline.py --preview
"""

import os, sys, json, datetime, math, subprocess

# Phase 3a: Multi-Armed Bandit for strategy selection
sys.path.insert(0, os.path.expanduser("~/.hermes/scripts"))
try:
    from strategy_bandit import StrategyBandit, format_stats as bandit_format_stats
    _BANDIT_AVAILABLE = True
except ImportError:
    _BANDIT_AVAILABLE = False
# Phase 3b: Novelty Search for exploration targets
try:
    from novelty_search import generate_novelty_targets, novelty_targets_as_action_items
    _NOVELTY_AVAILABLE = True
except ImportError:
    _NOVELTY_AVAILABLE = False
# Phase 3c: Meta-Evolution for parameter self-tuning
try:
    from meta_evolution import meta_evolve, get_current_params as get_meta_params
    _META_EVOLUTION_AVAILABLE = True
except ImportError:
    _META_EVOLUTION_AVAILABLE = False
from collections import Counter, defaultdict
from pathlib import Path

NOTES_DIR = os.path.expanduser("~/.hermes/notes")
SIGNALS_PATH = os.path.join(NOTES_DIR, "improvement-signals.jsonl")
HEALTH_PATH = os.path.join(NOTES_DIR, "engineering-cybernetics", "health-history.jsonl")
PATTERNS_PATH = os.path.join(NOTES_DIR, "user-routine-patterns.json")
DARWIN_RESULTS = os.path.expanduser("~/.hermes/skills/darwin-skill/results.tsv")
ACTION_PATH = os.path.join(NOTES_DIR, "improvement-action-plan.json")
EVOLUTION_PATH = os.path.expanduser("~/.pua/evolution.md")
USAGE_SCORE_PATH = os.path.expanduser("~/.hermes/state/usage-score.json")
STALE_TRANSIENT_HOURS = 72
STALE_TRANSIENT_MAX_HOURS = 168
EVOLVE_LOG_PATH = os.path.expanduser("~/.hermes/logs/evolve.log")
DIAGNOSTICS_DIR = os.path.join(NOTES_DIR, "tool-failure-diagnostics")
ACTIONABLE_ROI_MIN = 2.0
ACTIONABLE_IMPACT_MIN = 4
# Phase 0 fix: cumulative ROI for recurring failures
# When a signal shows N occurrences, ROI = impact * min(N, 20) / effort
# This prevents high-frequency low-ROI items from being perpetually skipped.
CUMULATIVE_OCCURRENCE_CAP = 20
# Stuck-counter: auto-lower ROI threshold after N consecutive skips of same type
STUCK_COUNTER_THRESHOLD = 5
STUCK_COUNTER_ROI_DELTA = 0.3  # lower ROI by 0.3 per stuck cycle
# Proposal expiry: days before a "proposed" item generates a signal
PROPOSAL_EXPIRY_DAYS = 7

os.makedirs(NOTES_DIR, exist_ok=True)

def parse_iso(ts):
    """Parse common ISO timestamps used by Hermes notes/logs."""
    if not ts:
        return None
    try:
        return datetime.datetime.fromisoformat(str(ts).replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def signal_age_hours(sig):
    t = parse_iso(sig.get("_parent_timestamp") or sig.get("timestamp"))
    if not t:
        return None
    return (datetime.datetime.now() - t).total_seconds() / 3600


def current_live_cron_health():
    """Return live cron-health-quarantine data when available.

    usage-score.json is a cached scorecard. The self-improvement queue should not
    keep emitting cron_degraded from that cache when the live quarantine check is
    already green; otherwise a repaired cron incident becomes a ghost action.
    """
    script = Path.home() / ".hermes" / "scripts" / "cron-health-quarantine.py"
    if not script.exists():
        return None
    try:
        proc = subprocess.run(
            [sys.executable, str(script)],
            text=True,
            capture_output=True,
            timeout=20,
            check=False,
        )
        if proc.returncode != 0 or not proc.stdout.strip():
            return None
        return json.loads(proc.stdout)
    except Exception:
        return None


def current_ops_healthy():
    """Return True when current operational checks show the old transient errors are closed."""
    live_cron = current_live_cron_health()
    if live_cron is not None:
        return int(live_cron.get("bad_count") or 0) == 0 and int(live_cron.get("stale_count") or 0) == 0
    try:
        data = json.loads(Path(USAGE_SCORE_PATH).read_text())
        cron = data.get("components", {}).get("cron_green", {})
        return data.get("grade") == "A" and int(cron.get("bad") or 0) == 0
    except Exception:
        return False


def is_stale_transient_signal(sig):
    """Suppress old tool-failure ghosts once closed, and always after 7d.

    Tool-failure autopsy records are point-in-time evidence. Keeping an old
    terminal failure HIGH forever creates a ghost queue: the pipeline keeps
    asking for work even after current traces/self-tests are healthy. Live
    failures will be re-emitted by fresh autopsy records inside the 7d window.
    """
    if sig.get("type") != "tool_failures":
        return False
    age = signal_age_hours(sig)
    if age is None:
        return False
    if age > STALE_TRANSIENT_MAX_HOURS:
        return True
    return current_ops_healthy() and age > STALE_TRANSIENT_HOURS


# ─── Signal Sources ───

def load_signals(max_age_days=30):
    """从 improvement-signals.jsonl 加载信号"""
    signals = []
    if not os.path.exists(SIGNALS_PATH):
        return signals
    cutoff = datetime.datetime.now() - datetime.timedelta(days=max_age_days)
    with open(SIGNALS_PATH, "r") as f:
        for line in f:
            try:
                s = json.loads(line)
                ts = s.get("timestamp", "")
                if ts:
                    try:
                        t = datetime.datetime.fromisoformat(ts)
                        if t < cutoff:
                            continue
                    except ValueError:
                        pass
                for sig in s.get("signals", []):
                    sig.setdefault("_parent_timestamp", ts)
                signals.append(s)
            except json.JSONDecodeError:
                continue
    return signals


def load_health_records(max_count=100):
    """从 health-history.jsonl 加载健康记录"""
    records = []
    if not os.path.exists(HEALTH_PATH):
        return records
    with open(HEALTH_PATH, "r") as f:
        for line in f:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records[-max_count:]


def load_patterns():
    """加载用户行为模式"""
    if not os.path.exists(PATTERNS_PATH):
        return {"task_types": {}, "time_slots": {}, "preferences": {}}
    with open(PATTERNS_PATH, "r") as f:
        return json.load(f)


def load_darwin_results(max_count=None):
    """加载 Darwin 优化记录。

    Use all rows by default: priority generation later collapses to the latest
    row per skill, and truncating raw rows can drop the actual latest accepted
    fix while retaining an older low baseline.
    """
    records = []
    if not os.path.exists(DARWIN_RESULTS):
        return records
    with open(DARWIN_RESULTS, "r") as f:
        # 跳过表头
        header = f.readline()
        for line in f:
            try:
                cols = line.strip().split("\t")
                if len(cols) >= 8:
                    records.append({
                        "timestamp": cols[0], "skill": cols[2],
                        "old_score": cols[3], "new_score": cols[4],
                        "status": cols[5], "note": cols[7] if len(cols) > 7 else "",
                    })
            except (IndexError, ValueError):
                continue
    return records[-max_count:] if max_count else records


# ─── Phase 0: New Signal Sources ───

PROPOSALS_PATH = os.path.expanduser("~/.hermes/pua-loop/proposals.jsonl")
BEHAVIORAL_RUNS_PATH = os.path.expanduser("~/.hermes/pua-loop/benchmark_runs.jsonl")
STUCK_COUNTER_PATH = os.path.join(NOTES_DIR, "pipeline-stuck-counter.json")


def load_operational_health_signals():
    """Generate signals from usage-score.json operational health degradation."""
    signals = []
    try:
        data = json.loads(Path(USAGE_SCORE_PATH).read_text())
    except Exception:
        return signals

    # Cron health degradation. Prefer the live quarantine check over the cached
    # usage-score component so repaired cron incidents do not remain queued as
    # stale medium-priority work.
    live_cron = current_live_cron_health()
    if live_cron is not None:
        bad_cron = int(live_cron.get("bad_count") or 0)
        stale_cron = int(live_cron.get("stale_count") or 0)
        if bad_cron > 0 or stale_cron > 0:
            count = bad_cron + stale_cron
            signals.append({
                "type": "operational_health",
                "subtype": "cron_degraded",
                "count": count,
                "impact": min(count + 3, 8),
                "detail": f"{bad_cron} cron jobs in bad state, {stale_cron} stale cron errors",
                "timestamp": datetime.datetime.now().isoformat(),
            })
    else:
        cron = data.get("components", {}).get("cron_green", {})
        bad_cron = int(cron.get("bad") or 0)
        if bad_cron > 0:
            signals.append({
                "type": "operational_health",
                "subtype": "cron_degraded",
                "count": bad_cron,
                "impact": min(bad_cron + 3, 8),  # 1 bad = impact 4, 5 bad = impact 8
                "detail": f"{bad_cron} cron jobs in bad state",
                "timestamp": datetime.datetime.now().isoformat(),
            })

    # Grade degradation
    grade = data.get("grade", "A")
    score = float(data.get("score") or 100)
    if grade not in ("A",) or score < 85:
        signals.append({
            "type": "operational_health",
            "subtype": "grade_degraded",
            "count": 1,
            "impact": 6,
            "detail": f"Health grade={grade}, score={score:.1f}",
            "timestamp": datetime.datetime.now().isoformat(),
        })

    return signals


def load_benchmark_regression_signals():
    """Generate signals when behavioral benchmarks show regressions."""
    signals = []
    if not os.path.exists(BEHAVIORAL_RUNS_PATH):
        return signals

    # Read last 3 runs
    runs = []
    with open(BEHAVIORAL_RUNS_PATH, "r") as f:
        for line in f:
            try:
                runs.append(json.loads(line.strip()))
            except json.JSONDecodeError:
                continue

    if len(runs) < 2:
        return signals

    latest = runs[-1]
    prev = runs[-2]

    # Check for pass rate regression
    latest_rate = latest.get("pass_rate", 1.0)
    prev_rate = prev.get("pass_rate", 1.0)
    if latest_rate < prev_rate:
        failed_names = [
            r["name"] for r in latest.get("results", [])
            if not r.get("passed")
        ]
        signals.append({
            "type": "benchmark_regression",
            "count": 1,
            "impact": 7,
            "detail": f"Benchmark pass rate regressed: {prev_rate:.0%} → {latest_rate:.0%}. Failed: {', '.join(failed_names[:3])}",
            "timestamp": datetime.datetime.now().isoformat(),
        })

    # Check for new failures
    prev_failed = {r["benchmark_id"] for r in prev.get("results", []) if not r.get("passed")}
    new_failures = [
        r for r in latest.get("results", [])
        if not r.get("passed") and r.get("benchmark_id") not in prev_failed
    ]
    if new_failures:
        signals.append({
            "type": "benchmark_new_failure",
            "count": len(new_failures),
            "impact": 6,
            "detail": f"{len(new_failures)} new benchmark failure(s): {', '.join(r['name'] for r in new_failures[:3])}",
            "timestamp": datetime.datetime.now().isoformat(),
        })

    return signals


def load_proposal_expiry_signals():
    """Generate signals for proposals stuck in 'proposed' status."""
    signals = []
    if not os.path.exists(PROPOSALS_PATH):
        return signals

    now = datetime.datetime.now()
    stuck_count = 0
    oldest_age_days = 0

    with open(PROPOSALS_PATH, "r") as f:
        for line in f:
            try:
                proposal = json.loads(line.strip())
                if proposal.get("status") != "proposed":
                    continue
                created = parse_iso(proposal.get("created_at"))
                if not created:
                    continue
                age_days = (now - created).days
                if age_days >= PROPOSAL_EXPIRY_DAYS:
                    stuck_count += 1
                    oldest_age_days = max(oldest_age_days, age_days)
            except (json.JSONDecodeError, ValueError):
                continue

    if stuck_count > 0:
        signals.append({
            "type": "stalled_proposals",
            "count": stuck_count,
            "impact": min(stuck_count + 4, 8),
            "detail": f"{stuck_count} proposals stuck in 'proposed' for up to {oldest_age_days} days",
            "timestamp": datetime.datetime.now().isoformat(),
        })

    return signals


def load_stuck_counter_state():
    """Load the stuck-counter state tracking consecutive skips per item type."""
    if not os.path.exists(STUCK_COUNTER_PATH):
        return {}
    try:
        return json.loads(Path(STUCK_COUNTER_PATH).read_text())
    except Exception:
        return {}


def save_stuck_counter_state(state):
    """Persist stuck-counter state."""
    os.makedirs(os.path.dirname(STUCK_COUNTER_PATH), exist_ok=True)
    Path(STUCK_COUNTER_PATH).write_text(json.dumps(state, indent=2, ensure_ascii=False))


def compute_effective_roi(item, stuck_state):
    """Compute effective ROI with cumulative occurrence boost and stuck-counter discount.

    Phase 0 fixes:
    1. Cumulative ROI: recurring failures get ROI * min(count, cap) multiplier
    2. Stuck-counter: items skipped N times get threshold lowered by delta * N
    """
    base_roi = item.roi

    # Cumulative boost from signal occurrence count
    occurrence_count = 1
    if hasattr(item, 'detail') and item.detail:
        try:
            detail = json.loads(item.detail)
            groups = detail.get("failure_groups", [])
            if groups:
                occurrence_count = sum(g.get("count", 1) for g in groups)
        except (json.JSONDecodeError, TypeError):
            pass
    cumulative_factor = min(occurrence_count, CUMULATIVE_OCCURRENCE_CAP)
    boosted_roi = base_roi * max(cumulative_factor, 1)

    # Stuck-counter discount
    item_key = item.act_type
    skip_count = stuck_state.get(item_key, 0)
    effective_threshold = max(
        ACTIONABLE_ROI_MIN - (skip_count * STUCK_COUNTER_ROI_DELTA),
        0.5  # floor
    )

    return boosted_roi, effective_threshold


# ─── Prioritization Engine ───

class ActionItem:
    """表示一个可执行的改进动作"""

    # Impact categories (higher = more valuable)
    IMPACT_LEVELS = {
        "critical": 10,   # 影响每次 session
        "high": 7,        # 影响多数 session
        "medium": 4,      # 偶尔有用
        "low": 2,         # 锦上添花
        "info": 1,        # 了解就行
    }

    # Effort categories (lower = easier)
    EFFORT_LEVELS = {
        "trivial": 1,     # 1 行改动
        "small": 2,       # 改一个文件
        "medium": 4,      # 改多个文件
        "large": 7,       # 新建脚本/skill
        "complex": 10,    # 跨模块改造
    }

    def __init__(self, act_type, summary, impact, effort,
                 detail="", suggestion="", source="", category=""):
        self.act_type = act_type
        self.summary = summary
        self.impact = self.IMPACT_LEVELS.get(impact, 3)
        self.impact_label = impact
        self.effort = self.EFFORT_LEVELS.get(effort, 3)
        self.effort_label = effort
        self.detail = detail
        self.suggestion = suggestion
        self.source = source
        self.category = category
        self.roi = self.impact / max(self.effort, 0.5)
        self.created_at = datetime.datetime.now().isoformat()

    def __repr__(self):
        sev = {10: "!!", 7: "! ", 4: "- ", 2: ". ", 1: "  "}.get(self.impact, "  ")
        return f"{sev} [roi={self.roi:.1f}] {self.summary} ({self.impact_label}/{self.effort_label})"


def aggregate_items(signals, health_records, patterns, darwin_records):
    """从所有信号源生成改进动作列表"""
    items = []

    # ── Source 1: Session Autopsy Signals ──
    # 按类型聚合
    type_signals = defaultdict(list)
    for s in signals:
        for sig in s.get("signals", []):
            type_signals[sig["type"]].append(sig)

    # 高频纠正 → memory/skill 动作
    correction_sigs = type_signals.get("frequent_corrections", [])
    if correction_sigs:
        total = sum(s.get("count", 0) for s in correction_sigs)
        items.append(ActionItem(
            "add_memory_or_skill", f"用户频繁纠正共 {total} 次，需补充对应记忆",
            "high", "small",
            detail=f"跨 {len(correction_sigs)} 个 session 累计 {total} 次纠正",
            suggestion="运行 post-session-autopsy.py --recent 10 查看具体纠正内容，确认是否需要补充 memory 或创建 skill",
            source="session_autopsy", category="user_experience"
        ))

    # 工具失败 → 配置/脚本修复
    failure_sigs = [s for s in type_signals.get("tool_failures", []) if not is_stale_transient_signal(s)]
    if failure_sigs:
        # Prefer structured failure groups. Keep old detail strings as fallback so
        # historical signals remain readable but no longer drive auto-config edits.
        grouped = Counter()
        group_payload = {}
        total_failures = sum(s.get("count", 0) for s in failure_sigs)
        for s in failure_sigs:
            groups = s.get("failure_groups") or []
            if isinstance(groups, list) and groups:
                for g in groups:
                    if not isinstance(g, dict):
                        continue
                    key = (
                        str(g.get("tool_name") or g.get("tool") or "unknown"),
                        str(g.get("error_signature") or "unknown"),
                        str(g.get("exit_code") if g.get("exit_code") is not None else ""),
                    )
                    count = int(g.get("count") or 1)
                    grouped[key] += count
                    merged = group_payload.setdefault(key, dict(g))
                    merged["count"] = grouped[key]
            else:
                detail = str(s.get("detail", "unknown_failure"))
                key = (detail[:80], "legacy_detail", "")
                grouped[key] += int(s.get("count") or 1)
                group_payload.setdefault(key, {
                    "tool_name": detail[:80],
                    "error_signature": "legacy_detail",
                    "exit_code": None,
                    "count": 0,
                    "stale_status": "unknown",
                })["count"] = grouped[key]
        if grouped:
            (tool, signature, exit_code), worst_count = grouped.most_common(1)[0]
            groups_out = []
            for key, count in grouped.most_common(10):
                g = dict(group_payload.get(key) or {})
                g.setdefault("tool_name", key[0])
                g.setdefault("error_signature", key[1])
                g.setdefault("exit_code", key[2] or None)
                g["count"] = count
                groups_out.append(g)
            detail_payload = json.dumps({"failure_groups": groups_out}, ensure_ascii=False, sort_keys=True)
            items.append(ActionItem(
                "fix_tool_config", f"工具失败 {total_failures} 次 ({tool}/{signature}: {worst_count} 次)",
                "high" if len(failure_sigs) >= 3 else "medium",
                "medium",
                detail=detail_payload,
                suggestion="生成只读工具失败诊断；不要在缺少精确 tool/error signature 前自动改配置",
                source="session_autopsy", category="reliability"
            ))

    # ── Source 2: Health Records ──
    if health_records:
        # 用户纠正率趋势
        recent = health_records[-20:]
        corr_counts = [r.get("user_corrections", 0) or 0 for r in recent]
        avg_corr = sum(corr_counts) / max(len(corr_counts), 1)
        if avg_corr >= 2:
            items.append(ActionItem(
                "improve_accuracy", f"近期平均纠正率 {avg_corr:.1f}/session，偏高",
                "medium", "medium",
                detail=f"最近 {len(recent)} 个 session 平均纠正 {avg_corr:.1f} 次",
                suggestion="检查 session 记录，识别最常出错的 task type",
                source="health_history", category="user_experience"
            ))

        # V 函数趋势
        v_values = [r.get("V", 1.0) for r in recent if r.get("V")]
        if len(v_values) >= 5:
            avg_v = sum(v_values) / len(v_values)
            if avg_v < 0.6:
                items.append(ActionItem(
                    "escalate_health", f"系统健康度 V={avg_v:.2f}，低于阈值 0.6",
                    "critical", "large",
                    detail=f"最近 {len(v_values)} 个 session 平均 V={avg_v:.2f}",
                    suggestion="运行 agent-health-monitor.py 诊断详细原因",
                    source="health_history", category="system_health"
                ))

    # ── Source 3: User Patterns ──
    task_types = patterns.get("task_types", {})
    if task_types:
        total_tasks = sum(task_types.values())
        # 检测新出现的频繁任务类型
        for ttype, count in sorted(task_types.items(), key=lambda x: x[1], reverse=True):
            ratio = count / max(total_tasks, 1)
            if ratio >= 0.3 and count >= 5:
                items.append(ActionItem(
                    "optimize_common_task", f"'{ttype}' 任务占比 {ratio:.0%} ({count}次)，应考虑 skill 优化",
                    "medium", "medium",
                    detail=f"高频任务类型，占比 {ratio:.0%}",
                    suggestion=f"检查是否有针对 '{ttype}' 的专用 skill",
                    source="user_patterns", category="task_coverage"
                ))

    # ── Source 4: Darwin Results ──
    if darwin_records:
        revert_count = sum(1 for r in darwin_records if r["status"] == "revert")
        if revert_count >= 3:
            items.append(ActionItem(
                "review_darwin_failures", f"Darwin 优化回滚 {revert_count} 次，需人工审查",
                "medium", "small",
                detail=f"最近 {len(darwin_records)} 条 Darwin 记录中 {revert_count} 次回滚",
                suggestion="检查 darwin-skill/results.tsv 了解具体回滚原因",
                source="darwin", category="skill_quality"
            ))

        # 低分 skill 列表：只看每个 skill 的最新 Darwin 记录，避免旧 baseline
        # 在已修复后继续产生幽灵优先级。
        latest_by_skill = {}
        for r in darwin_records:
            latest_by_skill[r.get("skill", "")] = r
        low_skills = set()
        for skill, r in latest_by_skill.items():
            if not skill:
                continue
            try:
                ns = int(r.get("new_score", 0))
                if ns < 60:
                    low_skills.add(skill)
            except (TypeError, ValueError):
                continue
        if low_skills:
            items.append(ActionItem(
                "improve_low_skills", f"{len(low_skills)} 个 skill 评分 < 60: {', '.join(list(low_skills)[:5])}",
                "medium", "medium",
                detail=f"低分 skill 列表: {', '.join(low_skills)}",
                suggestion="对最低分的 2-3 个 skill 执行 Darwin 优化",
                source="darwin", category="skill_quality"
            ))

    # 按 ROI 排序
    items.sort(key=lambda x: x.roi, reverse=True)

    # Phase 0: Process new signal types from operational_health and proposal_expiry
    ops_health_sigs = type_signals.get("operational_health", [])
    for sig in ops_health_sigs:
        subtype = sig.get("subtype", "unknown")
        count = sig.get("count", 1)
        impact = sig.get("impact", 4)
        detail = sig.get("detail", "")
        if subtype == "cron_degraded":
            items.append(ActionItem(
                "fix_cron_health", f"Cron 健康度下降: {detail}",
                "high" if count >= 3 else "medium", "small",
                detail=detail,
                suggestion="运行 cron-health-quarantine.py 诊断失败 cron jobs",
                source="operational_health", category="system_health"
            ))
        elif subtype == "grade_degraded":
            items.append(ActionItem(
                "escalate_health", f"系统健康度下降: {detail}",
                "high", "medium",
                detail=detail,
                suggestion="运行 agent-health-monitor.py 诊断",
                source="operational_health", category="system_health"
            ))

    stalled_sigs = type_signals.get("stalled_proposals", [])
    for sig in stalled_sigs:
        count = sig.get("count", 0)
        detail = sig.get("detail", "")
        items.append(ActionItem(
            "execute_stalled_proposals", f"提案积压: {detail}",
            "high", "medium",
            detail=detail,
            suggestion="审查 proposals.jsonl 中 'proposed' 状态的条目，决定是否执行或过期",
            source="proposal_expiry", category="evolution_momentum"
        ))

    # Phase 1: Benchmark regression signals
    benchmark_sigs = type_signals.get("benchmark_regression", []) + type_signals.get("benchmark_new_failure", [])
    for sig in benchmark_sigs:
        detail = sig.get("detail", "")
        impact = sig.get("impact", 6)
        items.append(ActionItem(
            "fix_benchmark_regression", f"基准回归: {detail}",
            "high" if impact >= 7 else "medium", "medium",
            detail=detail,
            suggestion="运行 behavioral-benchmark-runner.py 定位失败项并修复",
            source="behavioral_benchmark", category="system_health"
        ))

    # Re-sort after new items
    items.sort(key=lambda x: x.roi, reverse=True)
    return items


def deduplicate_items(items):
    """去重：合并相同 act_type + category 的动作"""
    seen = {}
    for item in items:
        key = (item.act_type, item.category)
        if key in seen:
            # 保留 ROI 更高的
            if item.roi > seen[key].roi:
                seen[key] = item
        else:
            seen[key] = item
    return list(seen.values())


# ─── Report Generation ───

def print_pipeline(items, signals_count=0, health_count=0):
    """打印管线报告"""
    print(f"\n{'=' * 60}")
    print(f"  Self-Improvement Pipeline — Priority Queue")
    print(f"{'=' * 60}")
    print(f"  Signal sources: {signals_count} autopsy | {health_count} health records")

    if not items:
        print(f"\n  ✓ 无待办改进项 — 系统健康")
        print(f"{'=' * 60}\n")
        return

    print(f"\n  {'ROI':<6} {'Impact':<10} {'Effort':<8} {'Category':<16} {'Action'}")
    print(f"  {'─'*5} {'─'*9} {'─'*7} {'─'*15} {'─'*40}")

    critical = [it for it in items if it.impact >= 9]
    high = [it for it in items if 6 <= it.impact < 9]
    medium = [it for it in items if 3 <= it.impact < 6]
    low = [it for it in items if it.impact < 3]

    for group, label in [(critical, "!! CRITICAL"), (high, "! HIGH"), (medium, "- MEDIUM"), (low, ". LOW")]:
        if group:
            print(f"\n  [{label}]")
            for it in group:
                s = {10: "!!", 7: "! ", 4: "- ", 2: ". ", 1: "  "}.get(it.impact, "  ")
                print(f"  {it.roi:>4.1f}x  {it.impact_label:<8} {it.effort_label:<7} {it.category:<15} {it.summary[:65]}")

    print(f"\n{'─' * 60}")
    print(f"  总计: {len(items)} 个改进动作")
    print(f"  {len(critical)} critical, {len(high)} high, {len(medium)} medium, {len(low)} low")
    print(f"{'=' * 60}\n")


def print_action_plan(items):
    """打印详细执行计划"""
    print(f"\n{'=' * 60}")
    print(f"  Improvement Action Plan")
    print(f"  Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'=' * 60}")

    for i, it in enumerate(items, 1):
        roi_bar = "▓" * min(int(it.roi), 10) + "░" * max(10 - min(int(it.roi), 10), 0)
        print(f"\n  #{i} [ROI {it.roi:.1f}x] {roi_bar}")
        print(f"  ├─ Type:     {it.act_type}")
        print(f"  ├─ Impact:   {it.impact_label} ({it.impact}/10)")
        print(f"  ├─ Effort:   {it.effort_label} ({it.effort}/10)")
        print(f"  ├─ Category: {it.category}")
        print(f"  ├─ Source:   {it.source}")
        print(f"  ├─ Detail:   {it.detail}")
        print(f"  └─ Action:   {it.suggestion}")


def _parse_item_failure_groups(item):
    """Extract structured failure groups from an ActionItem detail field."""
    detail = item.detail or ""
    try:
        payload = json.loads(detail)
        groups = payload.get("failure_groups") if isinstance(payload, dict) else None
        if isinstance(groups, list) and groups:
            return [g for g in groups if isinstance(g, dict)]
    except Exception:
        pass
    return [{
        "tool_name": detail[:80] or "unknown",
        "error_signature": "legacy_detail" if detail else "unknown",
        "exit_code": None,
        "count": 1,
        "stale_status": "unknown",
        "stderr_tail": detail[:500],
    }]


def _load_usage_health_context():
    try:
        data = json.loads(Path(USAGE_SCORE_PATH).read_text())
    except Exception:
        return {"usage_grade": "unknown"}
    cron = data.get("components", {}).get("cron_green", {})
    semantic = data.get("semantic_grades", {})
    operational = semantic.get("operational_health", {}) if isinstance(semantic, dict) else {}
    return {
        "usage_grade": data.get("grade", "unknown"),
        "operational_health_grade": operational.get("grade"),
        "cron_bad_count": cron.get("bad"),
        "cron_recent_24h": cron.get("recent_24h"),
        "fallback_used": any(
            (c or {}).get("fallback_used") for c in (data.get("components") or {}).values() if isinstance(c, dict)
        ),
    }


def write_tool_failure_diagnostic(item, status="pending_review", reason="not_auto_safe"):
    """Write a read-only diagnostic artifact for fix_tool_config.

    This intentionally does not edit config files. It turns vague queue items into
    evidence that a human or later safe actuator can review.
    """
    os.makedirs(DIAGNOSTICS_DIR, exist_ok=True)
    ts = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    safe_ts = ts.replace(":", "").replace("Z", "Z")
    path = os.path.join(DIAGNOSTICS_DIR, f"tool-failure-diagnostic-{safe_ts}.json")
    diagnostic = {
        "schema": "tool_failure_diagnostic_v1",
        "schema_version": "tool_failure_diagnostic_v1",
        "generated_at": ts,
        "source": item.source or "self-improvement-pipeline",
        "action_type": item.act_type,
        "summary": item.summary,
        "status": status,
        "auto_edit_config": False,
        "threshold": {"roi_min": ACTIONABLE_ROI_MIN, "impact_min": ACTIONABLE_IMPACT_MIN},
        "item": {
            "roi": round(item.roi, 2),
            "impact": item.impact,
            "impact_label": item.impact_label,
            "effort": item.effort,
            "effort_label": item.effort_label,
            "category": item.category,
        },
        "health_context": _load_usage_health_context(),
        "failures": _parse_item_failure_groups(item),
        "recommendation": {
            "safe_next_action": "human_review_or_targeted_fix",
            "reason": reason,
        },
        "safe_next_action": "human_review_or_targeted_fix",
    }
    Path(path).write_text(json.dumps(diagnostic, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def _action_state_summary(items, executed_actions=None, diagnostic_paths=None):
    executed_actions = executed_actions or []
    diagnostic_paths = diagnostic_paths or []
    # Phase 0: Use effective ROI/threshold
    actionable = []
    for it in items:
        effective_roi = getattr(it, '_effective_roi', it.roi)
        effective_threshold = getattr(it, '_effective_threshold', ACTIONABLE_ROI_MIN)
        if effective_roi >= effective_threshold and it.impact >= ACTIONABLE_IMPACT_MIN:
            actionable.append(it)
    skipped_below = [it for it in items if it not in actionable]
    pending_review_count = sum(1 for a in executed_actions if a.get("status") in {"pending_review", "manual", "needs_data"})
    executed_diagnostic_paths = {a.get("diagnostic_path") for a in executed_actions if a.get("diagnostic_path")}
    unlinked_diagnostic_count = sum(1 for p in diagnostic_paths if p not in executed_diagnostic_paths)
    # Diagnostic artifacts are evidence, not applied runtime changes.
    executed_count = sum(1 for a in executed_actions if a.get("status") in {"applied", "executed", "auto_fixed"})
    top = items[0] if items else None
    skipped_reason = None
    if top and top in skipped_below:
        if top.roi < ACTIONABLE_ROI_MIN:
            skipped_reason = "roi_below_threshold"
        elif top.impact < ACTIONABLE_IMPACT_MIN:
            skipped_reason = "impact_below_threshold"
        else:
            skipped_reason = "below_threshold"
    return {
        "generated_count": len(items),
        "actionable_count": len(actionable),
        "executed_count": executed_count,
        "pending_review_count": pending_review_count + unlinked_diagnostic_count,
        "skipped_below_threshold_count": len(skipped_below),
        "top_item_type": top.act_type if top else None,
        "top_item_roi": round(top.roi, 2) if top else None,
        "top_item_impact": top.impact if top else None,
        "skipped_reason": skipped_reason,
        "diagnostic_paths": diagnostic_paths,
        "actionable_threshold": {"roi_min": ACTIONABLE_ROI_MIN, "impact_min": ACTIONABLE_IMPACT_MIN},
        "useful_evolution": executed_count > 0,
    }


def append_evolution_closure(items, mode="run", execution_summary=None):
    """Append an observable closure/noop event for non-preview pipeline ticks."""
    os.makedirs(os.path.dirname(EVOLVE_LOG_PATH), exist_ok=True)
    high = sum(1 for it in items if 6 <= it.impact < 9)
    critical = sum(1 for it in items if it.impact >= 9)
    base_summary = _action_state_summary(items)
    summary = {**base_summary, **(execution_summary or {})}
    executed_count = int(summary.get("executed_count") or 0)
    if not items:
        eval_result = "noop"
        diagnosis = "no actionable improvement items"
        eval_applicable = False
    elif executed_count <= 0:
        eval_result = "not_evaluated_no_execution"
        diagnosis = f"priority queue has {len(items)} item(s), but no runtime patch executed; critical={critical}, high={high}"
        eval_applicable = False
    else:
        eval_result = "not_evaluated_execution_without_metric"
        diagnosis = f"{executed_count} action(s) executed, but no before/after eval metric was supplied"
        eval_applicable = False
    event = {
        "ts": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "source": "self-improvement-pipeline",
        "mode": mode,
        "eval_result": eval_result,
        "eval_applicable": eval_applicable,
        "useful_evolution": bool(summary.get("useful_evolution") and eval_applicable),
        "diagnosis": diagnosis,
        "steps_count": len(items),
        "critical": critical,
        "high": high,
        **summary,
    }
    with open(EVOLVE_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
    return event


def save_action_plan(items):
    """保存 action plan 到 JSON"""
    plan = {
        "generated_at": datetime.datetime.now().isoformat(),
        "total_items": len(items),
        "summary": {
            "critical": sum(1 for it in items if it.impact >= 9),
            "high": sum(1 for it in items if 6 <= it.impact < 9),
            "medium": sum(1 for it in items if 3 <= it.impact < 6),
            "low": sum(1 for it in items if it.impact < 3),
        },
        "items": [
            {
                "rank": i,
                "type": it.act_type,
                "summary": it.summary,
                "impact": it.impact_label,
                "impact_score": it.impact,
                "effort": it.effort_label,
                "effort_score": it.effort,
                "roi": round(it.roi, 2),
                "category": it.category,
                "source": it.source,
                "detail": it.detail,
                "suggestion": it.suggestion,
            }
            for i, it in enumerate(items, 1)
        ]
    }
    with open(ACTION_PATH, "w") as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)
    print(f"\n  Action plan saved to {ACTION_PATH}")


# ─── Auto-Execute Mode ───

def auto_execute(items):
    """自主执行模式 — dispatch 到各 actuator.

    Returns an action-state summary. Read-only diagnostics are allowed; runtime
    config edits are not performed from vague `fix_tool_config` aggregates.

    Phase 0: Uses effective ROI with cumulative boost and stuck-counter discount.
    """
    print(f"\n{'=' * 60}")
    print(f"  Auto-Execute Mode (Phase 0: cumulative ROI + stuck-counter)")
    print(f"{'=' * 60}")

    # Phase 0: Use effective ROI/threshold from compute_effective_roi
    actionable = []
    skipped_below = []
    for it in items:
        effective_roi = getattr(it, '_effective_roi', it.roi)
        effective_threshold = getattr(it, '_effective_threshold', ACTIONABLE_ROI_MIN)
        if effective_roi >= effective_threshold and it.impact >= ACTIONABLE_IMPACT_MIN:
            actionable.append(it)
        else:
            skipped_below.append(it)
    executed = []
    diagnostic_paths = []

    for it in skipped_below:
        if it.act_type == "fix_tool_config":
            path = write_tool_failure_diagnostic(it, status="pending_review", reason="roi_below_threshold_or_not_auto_safe")
            diagnostic_paths.append(path)
            print(f"  → Read-only diagnostic written: {path}")

    if not actionable:
        print("  No high-ROI actions to execute")
        return _action_state_summary(items, executed, diagnostic_paths)

    for it in actionable:
        print(f"\n  Executing: {it.summary}")

        if it.act_type == "add_memory_or_skill":
            # 运行 autopsy 获取详细内容
            print(f"  → Need more data: run autopsy to find exact correction patterns")
            executed.append({"action": it.act_type, "status": "needs_data", "detail": it.detail})

        elif it.act_type == "fix_tool_config":
            path = write_tool_failure_diagnostic(it, status="pending_review", reason="requires_precise_review_before_config_change")
            diagnostic_paths.append(path)
            print(f"  → Read-only diagnostic written: {path}")
            executed.append({"action": it.act_type, "status": "pending_review", "detail": it.detail, "diagnostic_path": path})

        elif it.act_type == "improve_low_skills":
            print(f"  → Could dispatch to Darwin skill optimizer")
            executed.append({"action": it.act_type, "status": "can_auto_optimize", "detail": it.detail})

        elif it.act_type == "fix_cron_health":
            print(f"  → Cron health degraded, scheduling diagnostic")
            executed.append({"action": it.act_type, "status": "diagnostic_queued", "detail": it.detail})

        elif it.act_type == "execute_stalled_proposals":
            print(f"  → Stale proposals detected, escalating for review")
            executed.append({"action": it.act_type, "status": "escalated", "detail": it.detail})

        else:
            print(f"  → Requires manual review")
            executed.append({"action": it.act_type, "status": "manual", "detail": it.detail})

    # Phase 0: Update stuck-counter state
    # Increment counter for skipped items, reset for executed items
    new_stuck_state = load_stuck_counter_state()
    for it in skipped_below:
        key = it.act_type
        new_stuck_state[key] = new_stuck_state.get(key, 0) + 1
    for a in executed:
        key = a.get("action")
        if key and key in new_stuck_state:
            del new_stuck_state[key]
    save_stuck_counter_state(new_stuck_state)

    # 记录执行日志
    exec_log = {
        "timestamp": datetime.datetime.now().isoformat(),
        "actions": executed,
        "diagnostic_paths": diagnostic_paths,
        "stuck_counter_state": new_stuck_state,
    }
    exec_path = os.path.join(NOTES_DIR, "improvement-execution-log.jsonl")
    with open(exec_path, "a") as f:
        f.write(json.dumps(exec_log, ensure_ascii=False) + "\n")

    print(f"\n  {len(executed)} actions logged to {exec_path}")
    print(f"  Auto-execution complete. Review suggestions above.")
    return _action_state_summary(items, executed, diagnostic_paths)


# ─── Evolutionary Baseline (PUA Pro integration) ───

def ensure_evolution_baseline():
    """确保 evolution.md 存在（pro skill 需要）"""
    evolution_dir = os.path.dirname(EVOLUTION_PATH)
    os.makedirs(evolution_dir, exist_ok=True)

    if not os.path.exists(EVOLUTION_PATH):
        baseline = f"""# PUA Self-Evolution Baseline
Created: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}

## Internalized Patterns (默认义务)
- [ ] 每次 session 结束自动运行 session-end-recorder
- [ ] 用户纠正 > 3 次时提出 memory/skill 建议
- [ ] 工具失败 > 5 次时检查配置

## Evolutionary Baseline (V函数初始值)
- V_initial: 1.0
- V_current: 1.0
- Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}

## KPI History
| Date | V | Corrections | Tool Failures | Score |
|------|---|------------|---------------|-------|
"""
        with open(EVOLUTION_PATH, "w") as f:
            f.write(baseline)
        print(f"  ✦ Created evolution baseline: {EVOLUTION_PATH}")
        return True
    return False


# ─── Main ───

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Self-Improvement Pipeline")
    parser.add_argument("--write", action="store_true", help="写入 action plan JSON")
    parser.add_argument("--auto-exec", action="store_true", help="自主执行模式")
    parser.add_argument("--preview", action="store_true", help="只读模式预览")
    parser.add_argument("--init-baseline", action="store_true", help="初始化进化基线")

    args = parser.parse_args()

    # 初始化基线（如果不存在）
    created = ensure_evolution_baseline()

    # Phase 3a: Multi-Armed Bandit strategy selection
    bandit = None
    selected_strategy = "signal_exploitation"  # default fallback
    if _BANDIT_AVAILABLE:
        bandit = StrategyBandit()
        selected_strategy = bandit.select_strategy()
        print(f"\n  Phase 3a: Bandit selected strategy: {selected_strategy}")
        stats = bandit.get_stats()
        print(bandit_format_stats(stats))
        bandit.save()  # persist the selection increment

    # Phase 3c: Meta-Evolution — adjust pipeline parameters before running
    if _META_EVOLUTION_AVAILABLE:
        meta_result = meta_evolve()
        if meta_result.get("applied"):
            print(f"\n  Meta-evolution adjusted {len(meta_result['applied'])} parameter(s)")
            for p, v in meta_result["applied"].items():
                print(f"    {p}: {v['old']} → {v['new']}")

    # 加载信号
    signals = load_signals()
    health_records = load_health_records()
    patterns = load_patterns()
    darwin_records = load_darwin_results()

    # Phase 0: New signal sources
    ops_health_signals = load_operational_health_signals()
    proposal_expiry_signals = load_proposal_expiry_signals()
    benchmark_regression_signals = load_benchmark_regression_signals()
    stuck_state = load_stuck_counter_state()

    # Inject new signals as synthetic signal entries
    for sig in ops_health_signals + proposal_expiry_signals + benchmark_regression_signals:
        signals.append({"signals": [sig], "timestamp": sig.get("timestamp")})

    # 聚合
    items = aggregate_items(signals, health_records, patterns, darwin_records)
    items = deduplicate_items(items)

    # Phase 0: Apply cumulative ROI and stuck-counter discount
    for item in items:
        boosted_roi, effective_threshold = compute_effective_roi(item, stuck_state)
        item._effective_roi = boosted_roi
        item._effective_threshold = effective_threshold

    # Phase 3b: Novelty Search — inject exploration targets when pipeline is idle
    # When no actionable items exist from reactive signals, novelty search
    # generates exploration targets from under-explored dimensions (Lehman & Stanley 2011).
    actionable_count = sum(
        1 for it in items
        if getattr(it, '_effective_roi', it.roi) >= ACTIONABLE_ROI_MIN
        and it.impact >= ACTIONABLE_IMPACT_MIN
    )
    if actionable_count == 0 and _NOVELTY_AVAILABLE:
        novelty_targets = generate_novelty_targets()
        if novelty_targets:
            print(f"\n  Phase 3b: Novelty search found {len(novelty_targets)} exploration target(s)")
            novelty_items = novelty_targets_as_action_items()
            for ni in novelty_items:
                items.append(ActionItem(
                    ni["act_type"], ni["summary"],
                    ni["impact"], ni["effort"],
                    detail=ni["detail"], suggestion=ni["suggestion"],
                    source=ni["source"], category=ni["category"],
                ))
            # Re-apply ROI for novelty items
            for item in items:
                if not hasattr(item, '_effective_roi'):
                    boosted_roi, effective_threshold = compute_effective_roi(item, stuck_state)
                    item._effective_roi = boosted_roi
                    item._effective_threshold = effective_threshold
            items.sort(key=lambda x: x.roi, reverse=True)

    if args.preview or args.write or args.auto_exec or not any([args.write, args.auto_exec]):
        # 默认或 --preview: 打印报告
        print_pipeline(items, len(signals), len(health_records))

        if args.write or args.auto_exec:
            save_action_plan(items)
            print_action_plan(items[:5])  # Top 5

        if args.auto_exec:
            execution_summary = auto_execute(items)

    # Phase 3a: Update bandit reward based on pipeline outcome
    if bandit is not None and not args.preview:
        exec_sum = locals().get("execution_summary")
        actionable_count = exec_sum.get("actionable_count", 0) if exec_sum else 0
        executed_count = exec_sum.get("executed_count", 0) if exec_sum else 0
        # Reward heuristic: 1.0 if executed, 0.5 if actionable but not executed, 0.1 if nothing actionable
        if executed_count > 0:
            reward = 1.0
        elif actionable_count > 0:
            reward = 0.5
        else:
            reward = 0.1
        bandit.update_reward(selected_strategy, reward)
        bandit.save()
        print(f"\n  Phase 3a: Bandit reward updated: {selected_strategy} -> {reward:.1f}")

    if not args.preview:
        event = append_evolution_closure(items, mode="auto_exec" if args.auto_exec else "write" if args.write else "run", execution_summary=locals().get("execution_summary"))
        print(f"\n  Evolution closure appended to {EVOLVE_LOG_PATH}: {event['eval_result']} ({event['steps_count']} item(s))")

    if created:
        print(f"\n  Next step: edit ~/.pua/evolution.md to add your first KPI entry")
        print(f"  Or run: python3 ~/.hermes/scripts/post-session-autopsy.py --recent 5 --write")


if __name__ == "__main__":
    main()
