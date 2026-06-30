#!/usr/bin/env python3
"""
Task Preflight — Adapter-aware preflight check

Task description -> parse -> plan -> ambiguity detection -> confirmation -> execute

Architecture:
  TaskAdapter.preflight(spec) -> PreflightResult
    |
    v
  Ambiguity detection (source-aware question formatting)
    |
    v
  HIGH -> auto-execute (30s cancel)
  MED  -> wait for confirmation
  LOW  -> answer questions first

Usage:
  # Adapter-aware check (preferred)
  python3 task_preflight.py check-adapter <task_id> --spec-file spec.json --adapter lark

  # Legacy check (backward compatible)
  python3 task_preflight.py check <task_id> --title "..." --description "..."

  # Approve/clarify/reject
  python3 task_preflight.py approve <task_id>
  python3 task_preflight.py clarify <task_id> --answer "..."
  python3 task_preflight.py status <task_id>
"""
import json
import os
import sys
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any

PREFLIGHT_DIR = Path(os.environ.get("HERMES_TASK_PREFLIGHT_DIR", str(Path.home() / ".hermes" / "task-preflight"))).expanduser()
OBSERVER_DIR = Path(os.environ.get("HERMES_TASK_OBSERVER_DIR", str(Path.home() / ".hermes" / "task-observer"))).expanduser()

# Try importing adapter types (optional dependency)
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from task_adapter import TaskSpec, TaskSource, TaskAdapter, PreflightResult, CompletionGate
    from task_registry import TaskRegistry
    HAS_ADAPTER = True
except ImportError:
    HAS_ADAPTER = False


def ensure_dir():
    PREFLIGHT_DIR.mkdir(parents=True, exist_ok=True)
    OBSERVER_DIR.mkdir(parents=True, exist_ok=True)


def get_path(task_id):
    return PREFLIGHT_DIR / f"{task_id}.json"


def load(task_id):
    path = get_path(task_id)
    if path.exists():
        return json.loads(path.read_text())
    return None


def save(task_id, data):
    ensure_dir()
    get_path(task_id).write_text(json.dumps(data, indent=2, ensure_ascii=False))


def local_brain_preflight_enabled() -> bool:
    raw = os.environ.get("HERMES_LOCAL_BRAIN_PREFLIGHT_ENABLED", "1").strip().lower()
    return raw not in {"0", "false", "no", "off", "never"}


def _split_env_paths(value: str) -> List[Path]:
    return [Path(part).expanduser() for part in value.split(os.pathsep) if part.strip()]


def run_local_brain_constraint(task_id: str, title: str, description: str, referenced_files: Optional[List[str]] = None) -> Optional[dict]:
    """Run the local-brain BrainConstraintGate for task preflight.

    This is local/read-only with respect to external systems. It may update local
    brain index/WAL state under the configured memory root.
    """
    if not local_brain_preflight_enabled():
        return None
    try:
        from local_brain_change_preflight import run_preflight, default_vaults
    except Exception as exc:
        return {
            "schema": "local_brain_change_preflight_v1",
            "dry_run": True,
            "error": f"local_brain_preflight_import_failed: {type(exc).__name__}: {exc}",
            "brain_constraint_record": {"verdict": {"status": "block", "reasons": ["import_failed"]}},
            "side_effects": {"external_dispatch": False, "lifecycle_write": False, "publish_deploy_push": False, "destructive": False, "credential_payment": False},
        }
    env_vaults = os.environ.get("HERMES_BRAIN_PREFLIGHT_VAULTS")
    vaults = _split_env_paths(env_vaults) if env_vaults else default_vaults()
    memory_root = Path(os.environ.get("HERMES_LOCAL_BRAIN_PREFLIGHT_MEMORY_ROOT", str(Path.home() / ".hermes" / "memory" / "local-brain-preflight"))).expanduser()
    evidence = [f"task_preflight:{task_id}"]
    return run_preflight(
        summary=f"{title}\n{description}",
        files=referenced_files or [],
        vaults=vaults,
        memory_root=memory_root,
        evidence=evidence,
        limit=8,
    )


def attach_local_brain_constraint(preflight: dict, referenced_files: Optional[List[str]] = None) -> dict:
    gate = run_local_brain_constraint(
        str(preflight.get("task_id", "task")),
        str(preflight.get("title", "")),
        str(preflight.get("description", "")),
        referenced_files or preflight.get("referenced_files") or preflight.get("plan", {}).get("scope") or [],
    )
    if gate is None:
        return preflight
    preflight["local_brain_constraint"] = gate
    verdict = gate.get("brain_constraint_record", {}).get("verdict", {}) if isinstance(gate, dict) else {}
    if verdict.get("status") == "block":
        preflight["status"] = "blocked_by_local_brain_constraint"
        preflight.setdefault("ambiguity_issues", []).append(
            {
                "category": "local_brain_constraint",
                "question": "Local brain BrainConstraintGate blocked this task; repair evidence or scope before approval.",
                "question_zh": "本地大脑 BrainConstraintGate 阻断该任务；需先补齐证据或收窄范围再批准。",
                "severity": "high",
                "formatted_question": "本地大脑 BrainConstraintGate 阻断该任务；需先补齐证据或收窄范围再批准。",
                "reasons": verdict.get("reasons", []),
            }
        )
    return preflight


# === Ambiguity Detection Rules ===

AMBIGUITY_RULES = [
    {
        "category": "scope",
        "trigger": lambda desc: len(desc) < 20 and not any(c in desc for c in ["/", ".", "tsx", "vue", "py"]),
        "question": "Task description too short. Please specify: which page/component/file?",
        "severity": "high",
        "question_zh": "任务描述过短，请补充具体范围：哪个页面/组件/文件？",
    },
    {
        "category": "approach",
        "trigger": lambda desc: any(w in desc.lower() for w in ["optimize", "improve", "better"]) and not any(w in desc for w in ["改为", "使用", "替换为", "改成"]),
        "question": "Optimization task detected but no specific approach. What is the expected optimization direction?",
        "severity": "high",
        "question_zh": "检测到优化类任务，但缺少具体方案。期望的优化方向是什么？",
    },
    {
        "category": "acceptance",
        "trigger": lambda desc: "原型" in desc and "截图" not in desc and "1:1" not in desc,
        "question": "Task mentions prototype but no acceptance criteria. Screenshot comparison or functional alignment?",
        "severity": "medium",
        "question_zh": "任务提到原型但未指定验收标准。需要截图对比还是功能对齐？",
    },
    {
        "category": "scope_destructive",
        "trigger": lambda desc: any(w in desc for w in ["重构", "重写", "迁移", "替换所有", "全面"]),
        "question": "Large-scope change detected. Need phased execution? Confirm impact scope first.",
        "severity": "high",
        "question_zh": "检测到大范围变更任务。是否需要分阶段执行？先确认影响范围。",
    },
    {
        "category": "goal_vague",
        "trigger": lambda desc: any(w in desc for w in ["修复问题", "fix bug", "有bug", "不工作", "不好用"]) and not any(w in desc for w in ["因为", "原因是", "错误是", "报错"]),
        "question": "Vague problem description. What is the specific symptom? Reproduction steps? Expected behavior?",
        "severity": "high",
        "question_zh": "检测到模糊的问题描述。请补充：具体现象是什么？复现步骤？期望行为？",
    },
]

# Auto-resolvable patterns (don't ask)
AUTO_RESOLVE = [
    "file exists in codebase -> use that file",
    "framework convention -> follow existing patterns",
    "test framework -> infer from config",
    "linting/formatting -> use existing config",
    "git strategy -> branch from current",
    "build verification -> always run after changes",
    "import style -> follow codebase patterns",
    "naming conventions -> follow file being edited",
]


def _format_question(issue: Dict[str, Any], source: str) -> str:
    """Format question based on task source.

    Chinese for Lark (team context), English for brain/direct.
    """
    if source == "lark":
        return issue.get("question_zh", issue["question"])
    return issue["question"]


# === Bayesian Ambiguity Detection ===

# Prior: P(ambiguous) from historical task data
PRIOR_AMBIGUOUS = 0.3

# Likelihood table: P(feature_present | class)
# Each entry: feature_name -> (P(feat|ambiguous), P(feat|clear))
LIKELIHOOD_TABLE = {
    'short_desc':       (0.80, 0.10),  # desc_length < 20
    'no_file_refs':     (0.70, 0.20),  # file_refs == 0
    'no_action_verbs':  (0.60, 0.10),  # action_verbs == 0
    'no_screenshot':    (0.40, 0.30),  # screenshot_refs == 0
    'no_component':     (0.50, 0.20),  # component_refs == 0
    'vague_goal':       (0.85, 0.05),  # vague problem words, no root cause
    'destructive':      (0.75, 0.10),  # refactor/migrate/rewrite scope
    'optimization':     (0.70, 0.15),  # optimize/improve without approach
    'prototype_no_spec': (0.60, 0.15),  # prototype mentioned, no acceptance
}


def calculate_specificity(text: str) -> float:
    """Calculate a 0-100 specificity score for the text.

    Higher = more specific / actionable.
    Based on presence of concrete references, numbers, paths, and action verbs.
    """
    score = 50.0  # neutral baseline

    # Boosts for specificity
    if re.search(r'\d+', text):
        score += 10  # has numbers (line refs, sizes, counts)
    if re.search(r'[\w/]+\.(tsx?|vue|py|json|md|css)', text):
        score += 15  # has file paths
    if re.search(r'[A-Z]\w+\.(tsx?|vue)', text):
        score += 10  # has component names
    if any(w in text for w in ['修改', '新增', '删除', '替换', '改为', '添加', '修复', '优化']):
        score += 10  # has action verbs
    if re.search(r'截图|原型|1:1|prototype', text):
        score += 5  # has acceptance criteria

    # Penalties for vagueness
    if len(text.strip()) < 20:
        score -= 25
    if any(w in text for w in ['修复问题', 'fix bug', '有bug', '不工作', '不好用']):
        if not any(w in text for w in ['因为', '原因是', '错误是', '报错', 'traceback', 'error']):
            score -= 20  # vague problem, no root cause
    if any(w in text for w in ['重构', '重写', '迁移', '替换所有', '全面']):
        score -= 10  # broad scope

    return max(0.0, min(100.0, score))


def extract_features(title: str, description: str) -> dict:
    """Extract measurable features from task description for Bayesian inference."""
    text = f'{title} {description}'
    desc_length = len(description)
    file_refs = len(re.findall(r'\w+\.(tsx?|vue|py|json)', text))
    action_verbs = sum(1 for w in ['修改', '新增', '删除', '替换', '改为', '添加', '修复', '优化'] if w in text)
    screenshot_refs = len(re.findall(r'截图|原型|1:1|prototype', text))
    component_refs = len(re.findall(r'[A-Z]\w+\.(tsx?|vue)', text))
    specificity = calculate_specificity(text)

    # Derive binary features for likelihood lookup
    vague_goal = any(w in text for w in ['修复问题', 'fix bug', '有bug', '不工作', '不好用']) \
        and not any(w in text for w in ['因为', '原因是', '错误是', '报错'])
    destructive = any(w in text for w in ['重构', '重写', '迁移', '替换所有', '全面'])
    optimization = any(w in text.lower() for w in ['optimize', 'improve', 'better']) \
        and not any(w in text for w in ['改为', '使用', '替换为', '改成'])
    prototype_no_spec = '原型' in text and '截图' not in text and '1:1' not in text

    return {
        'desc_length': desc_length,
        'file_refs': file_refs,
        'action_verbs': action_verbs,
        'screenshot_refs': screenshot_refs,
        'component_refs': component_refs,
        'specificity_score': specificity,
        # Binary features for Bayesian inference
        'short_desc': desc_length < 20,
        'no_file_refs': file_refs == 0,
        'no_action_verbs': action_verbs == 0,
        'no_screenshot': screenshot_refs == 0,
        'no_component': component_refs == 0,
        'vague_goal': vague_goal,
        'destructive': destructive,
        'optimization': optimization,
        'prototype_no_spec': prototype_no_spec,
    }


def bayesian_ambiguity_score(features: dict) -> dict:
    """Compute posterior P(ambiguous | features) using Bayesian inference.

    Uses naive Bayes: assumes feature independence given class.
    Returns dict with score, confidence label, likelihood_ratio, and details.
    """
    prior_amb = PRIOR_AMBIGUOUS
    prior_clear = 1.0 - prior_amb

    log_likelihood_amb = 0.0
    log_likelihood_clear = 0.0
    feature_details = []

    for feat_name, (p_amb, p_clear) in LIKELIHOOD_TABLE.items():
        feat_present = features.get(feat_name, False)
        if feat_present:
            log_likelihood_amb += _safe_log(p_amb)
            log_likelihood_clear += _safe_log(p_clear)
            feature_details.append({
                'feature': feat_name,
                'present': True,
                'p_ambig': p_amb,
                'p_clear': p_clear,
                'lr': p_amb / p_clear if p_clear > 0 else float('inf'),
            })

    # Posterior via log-sum-exp for numerical stability
    log_posterior_amb = _safe_log(prior_amb) + log_likelihood_amb
    log_posterior_clear = _safe_log(prior_clear) + log_likelihood_clear

    # Normalize
    max_log = max(log_posterior_amb, log_posterior_clear)
    posterior_amb = _exp(log_posterior_amb - max_log)
    posterior_clear = _exp(log_posterior_clear - max_log)
    total = posterior_amb + posterior_clear
    if total > 0:
        posterior_amb /= total
        posterior_clear /= total

    # Map to 0-100 score (higher = more ambiguous)
    score = round(posterior_amb * 100, 1)

    # Likelihood ratio
    lr = _exp(log_likelihood_amb - log_likelihood_clear) if log_likelihood_clear != 0 else float('inf')

    confidence = score_to_confidence(score)

    return {
        'score': score,
        'confidence': confidence,
        'likelihood_ratio': round(lr, 3),
        'posterior_ambiguous': round(posterior_amb, 4),
        'prior': prior_amb,
        'feature_details': feature_details,
    }


def _safe_log(x: float) -> float:
    """Safe log that returns -inf for 0."""
    import math
    return math.log(x) if x > 0 else -1e15


def _exp(x: float) -> float:
    """Safe exp with overflow guard."""
    import math
    if x < -500:
        return 0.0
    return math.exp(x)


def score_to_confidence(score: float) -> str:
    """Map ambiguity score to HIGH/MED/LOW confidence label.

    LOW score = HIGH confidence (task is clear).
    HIGH score = LOW confidence (task is ambiguous).
    """
    if score < 30:
        return 'HIGH'
    elif score < 60:
        return 'MED'
    else:
        return 'LOW'


def _collect_issues_from_features(features: dict, title: str, description: str) -> List[Dict[str, Any]]:
    """Generate backward-compatible issues list from detected features.

    Maps Bayesian features to the same issue format used by the old AMBIGUITY_RULES.
    """
    text = f"{title} {description}"
    issues = []

    for rule in AMBIGUITY_RULES:
        try:
            if rule["trigger"](text):
                issues.append({
                    "category": rule["category"],
                    "question": rule["question"],
                    "question_zh": rule.get("question_zh", rule["question"]),
                    "severity": rule["severity"],
                })
        except Exception:
            pass
    return issues


def detect_ambiguity(title, description):
    """Run Bayesian ambiguity detection. Returns list of issues (backward compat)."""
    features = extract_features(title, description)
    return _collect_issues_from_features(features, title, description)


def classify_confidence(issues, description):
    """Classify confidence using Bayesian inference.

    Ignores the legacy issues parameter for scoring (kept for interface compat).
    Returns HIGH/MED/LOW.
    """
    # We need title too; extract from context or use empty
    # This function is called with (issues, description) from legacy code
    # For Bayesian scoring, we re-extract features from description alone
    features = extract_features("", description)
    result = bayesian_ambiguity_score(features)
    return result['confidence']


def classify_confidence_from_title_desc(title: str, description: str) -> dict:
    """Full Bayesian classification with title and description.

    Returns the full Bayesian result dict (preferred over classify_confidence).
    """
    features = extract_features(title, description)
    result = bayesian_ambiguity_score(features)
    result['features'] = features
    result['issues'] = _collect_issues_from_features(features, title, description)
    return result


def compute_ambiguity_score(issues, description):
    """Compute a 0-100 ambiguity score from issues and description.

    Higher score = more ambiguous = more likely to need human input.
    Used by should_ask_human() for optimal stopping decisions.
    """
    score = 0.0

    # Base score from detected issues
    high_severity = sum(1 for i in issues if i["severity"] == "high")
    medium_severity = sum(1 for i in issues if i["severity"] == "medium")
    score += high_severity * 25  # each high issue adds 25 points
    score += medium_severity * 12  # each medium adds 12

    # Short description penalty
    if len(description) < 20:
        score += 30
    elif len(description) < 50:
        score += 15

    # File reference bonus (reduces ambiguity)
    has_file_ref = bool(re.search(r'\w+\.(tsx?|vue|py|md|json)', description))
    if has_file_ref:
        score -= 15

    # Specific action bonus
    has_specific_action = any(w in description for w in [
        "修改", "新增", "删除", "替换", "改为", "添加",
        "change", "add", "remove", "replace", "update"
    ])
    if has_specific_action:
        score -= 10

    # Component/type reference bonus
    has_component = bool(re.search(r'[A-Z]\w+\.(tsx?|vue)', description))
    if has_component:
        score -= 10

    return max(0, min(100, score))


def should_ask_human(features, confidence_score, context=None):
    """Decide whether to ask human using optimal stopping theory.

    Based on Wald's Sequential Probability Ratio Test (SPRT):
    - H0: task is clear enough to proceed
    - H1: task is ambiguous, needs human input
    - Decision rule: V(info) > C(ask) → ask human

    V(info) = expected loss from wrong decision if we proceed without asking
    C(ask)  = cost of asking (context switch, wait time, urgency tradeoff)

    References:
      Wald 1950: Statistical Decision Functions
      Ferguson 1967: Mathematical Statistics: A Decision Theoretic Approach

    Args:
        features: extracted features from task description
        confidence_score: 0-100 ambiguity score (higher = more ambiguous)
        context: optional dict with urgency, time_pressure, etc.

    Returns:
        dict with keys: ask_human, reason, V_info, C_ask, decision_boundary
    """
    # Tunable constants
    BASE_COST = 30       # base cost of interrupting human
    POTENTIAL_LOSS = 100  # max loss from proceeding with wrong interpretation
    URGENCY_FACTOR = 0.5  # how much urgency reduces the ask threshold

    # Value of information: expected loss if we proceed without clarification
    # confidence_score is ambiguity (0=clear, 100=fully ambiguous)
    V_info = (confidence_score / 100.0) * POTENTIAL_LOSS

    # Cost of asking: base cost adjusted by context
    C_ask = BASE_COST
    if context:
        urgency = context.get("urgency", 0.5)  # 0=relaxed, 1=urgent
        # Higher urgency → lower cost of asking (we'd rather ask than fail)
        # But also: urgency means human is busy, so there's a tradeoff
        # Net effect: moderate urgency slightly reduces ask cost
        C_ask *= (1 - urgency * URGENCY_FACTOR)

    # Decision: ask if value of information exceeds cost of asking
    ask_human = V_info > C_ask

    # Boundary classification for display/action mapping
    ratio = V_info / C_ask if C_ask > 0 else float("inf")
    if ratio < 0.5:
        boundary = "clear"       # clearly proceed
    elif ratio > 2.0:
        boundary = "ambiguous"   # clearly ask
    else:
        boundary = "boundary"    # grey zone — show plan, wait for go

    return {
        "ask_human": ask_human,
        "reason": f"V={V_info:.0f} vs C={C_ask:.0f} (ratio={ratio:.2f})",
        "V_info": round(V_info, 1),
        "C_ask": round(C_ask, 1),
        "decision_boundary": boundary,
    }


def decide_action(optimal_decision):
    """Map optimal stopping decision to user-facing action.

    Returns (action_label, should_block) tuple.
    """
    boundary = optimal_decision["decision_boundary"]
    if boundary == "clear":
        return "auto-execute (30s cancel window)", False
    elif boundary == "ambiguous":
        return "answer questions first", True
    else:  # boundary
        return "review plan, press go to continue", True


def generate_plan(title, description):
    """Generate execution plan from task description."""
    # Extract file references
    files = re.findall(r'[\w/]+\.(tsx?|vue|py|json|md)', description)
    files = list(set(files))

    # Extract action verbs
    actions = []
    for word in ["修改", "新增", "删除", "替换", "改为", "添加", "修复", "优化", "重构"]:
        if word in description:
            actions.append(word)

    # Generate steps based on patterns
    steps = []
    if files:
        steps.append({"name": "定位文件", "detail": f"确认 {', '.join(files[:3])} 的当前状态"})
    else:
        steps.append({"name": "定位目标", "detail": "根据描述找到需要修改的文件/组件"})

    if any(w in description for w in ["修改", "修复", "改为", "替换"]):
        steps.append({"name": "实现修改", "detail": "根据需求修改代码"})

    if any(w in description for w in ["新增", "添加"]):
        steps.append({"name": "新增代码", "detail": "添加新组件/功能"})

    steps.append({"name": "验证", "detail": "运行 build/test，确认无错误"})
    steps.append({"name": "截图对比", "detail": "浏览器截图与原型对比" if "原型" in description else "浏览器验证效果"})

    return {
        "goal": title,
        "scope": files[:5] if files else ["待确认"],
        "steps": steps,
        "auto_resolved": AUTO_RESOLVE[:3],
    }


# === Adapter-aware preflight (preferred) ===

def cmd_check_adapter(task_id, spec_data, adapter_name=None):
    """Run preflight using TaskAdapter.

    Args:
        task_id: task identifier
        spec_data: dict with TaskSpec fields
        adapter_name: optional adapter name for registry lookup
    """
    if not HAS_ADAPTER:
        print("Error: task_adapter module not available. Use legacy check.", file=sys.stderr)
        return

    ensure_dir()

    # Build TaskSpec from dict
    spec = TaskSpec.from_dict(spec_data)
    spec.task_id = task_id

    # Try to get adapter-specific preflight result
    adapter_preflight_result = None
    if adapter_name:
        try:
            registry = TaskRegistry()
            # Registry is empty here; caller should pass pre-computed result
            # This is a design point: adapter.preflight() is called by the orchestrator
        except Exception:
            pass

    # Run Bayesian ambiguity detection on spec fields
    result = classify_confidence_from_title_desc(spec.title, spec.description)
    issues = result['issues']
    confidence = result['confidence']
    score = result['score']
    features = result['features']
    plan = generate_plan(spec.title, spec.description)

    # Optimal stopping decision (uses Bayesian score)
    optimal = should_ask_human(features, score)
    action_label, should_block = decide_action(optimal)

    # Format questions based on source
    for issue in issues:
        issue["formatted_question"] = _format_question(issue, spec.source)

    preflight = {
        "task_id": task_id,
        "title": spec.title,
        "description": spec.description,
        "source": spec.source,
        "project": spec.project,
        "priority": spec.priority,
        "lane": spec.lane,
        "acceptance_criteria": spec.acceptance_criteria,
        "expected_screenshots": spec.expected_screenshots,
        "referenced_files": spec.referenced_files,
        "plan": plan,
        "confidence": confidence,
        "ambiguity_score": score,
        "likelihood_ratio": result['likelihood_ratio'],
        "features": features,
        "ambiguity_issues": issues,
        "optimal_stopping": {
            "ambiguity_score": score,
            "ask_human": optimal["ask_human"],
            "V_info": optimal["V_info"],
            "C_ask": optimal["C_ask"],
            "decision_boundary": optimal["decision_boundary"],
            "reason": optimal["reason"],
            "action": action_label,
        },
        "status": "pending_approval",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "approved_at": None,
        "clarifications": [],
    }

    attach_local_brain_constraint(preflight, referenced_files=spec.referenced_files)
    save(task_id, preflight)
    print_preflight(preflight)
    return preflight


def cmd_check_with_preflight_result(task_id, spec, preflight_result):
    """Store a PreflightResult from an adapter.

    Args:
        task_id: task identifier
        spec: TaskSpec instance
        preflight_result: PreflightResult from adapter.preflight()
    """
    ensure_dir()

    # Build issues list from adapter questions
    issues = [{"category": "adapter", "question": q, "severity": "medium"} for q in preflight_result.questions]

    # Optimal stopping decision using adapter-provided score
    # Map HIGH/MED/LOW to a numeric ambiguity score
    conf_map = {"HIGH": 10, "MED": 50, "LOW": 80}
    ambiguity_score = conf_map.get(preflight_result.confidence, 50)
    features = extract_features(spec.title, spec.description)
    optimal = should_ask_human(features, ambiguity_score)
    action_label, should_block = decide_action(optimal)

    preflight = {
        "task_id": task_id,
        "title": spec.title,
        "description": spec.description,
        "source": spec.source,
        "project": spec.project,
        "priority": spec.priority,
        "lane": spec.lane,
        "acceptance_criteria": spec.acceptance_criteria,
        "expected_screenshots": spec.expected_screenshots,
        "referenced_files": spec.referenced_files,
        "plan": {"goal": spec.title, "steps": preflight_result.plan, "scope": spec.referenced_files[:5]},
        "confidence": preflight_result.confidence,
        "ambiguity_issues": issues,
        "auto_resolved": preflight_result.auto_resolved,
        "estimated_duration": preflight_result.estimated_duration,
        "optimal_stopping": {
            "ambiguity_score": ambiguity_score,
            "ask_human": optimal["ask_human"],
            "V_info": optimal["V_info"],
            "C_ask": optimal["C_ask"],
            "decision_boundary": optimal["decision_boundary"],
            "reason": optimal["reason"],
            "action": action_label,
        },
        "status": "pending_approval",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "approved_at": None,
        "clarifications": [],
    }

    attach_local_brain_constraint(preflight, referenced_files=spec.referenced_files)
    save(task_id, preflight)
    print_preflight(preflight)
    return preflight


# === Legacy check (backward compatible) ===

def cmd_check(task_id, title, description, verbose=False):
    """Generate preflight check with Bayesian inference."""
    ensure_dir()

    # Bayesian scoring
    result = classify_confidence_from_title_desc(title, description)
    issues = result['issues']
    confidence = result['confidence']
    score = result['score']
    features = result['features']
    likelihood_ratio = result['likelihood_ratio']
    plan = generate_plan(title, description)

    # Optimal stopping decision (uses Bayesian score)
    optimal = should_ask_human(features, score)
    action_label, should_block = decide_action(optimal)

    preflight = {
        "task_id": task_id,
        "title": title,
        "description": description,
        "source": "direct",
        "project": "",
        "priority": "P2",
        "lane": "work",
        "plan": plan,
        "confidence": confidence,
        "ambiguity_score": score,
        "likelihood_ratio": likelihood_ratio,
        "features": features,
        "ambiguity_issues": issues,
        "optimal_stopping": {
            "ambiguity_score": score,
            "ask_human": optimal["ask_human"],
            "V_info": optimal["V_info"],
            "C_ask": optimal["C_ask"],
            "decision_boundary": optimal["decision_boundary"],
            "reason": optimal["reason"],
            "action": action_label,
        },
        "status": "pending_approval",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "approved_at": None,
        "clarifications": [],
    }

    attach_local_brain_constraint(preflight)
    save(task_id, preflight)
    print_preflight(preflight, verbose=verbose)
    return preflight


def print_preflight(pf, verbose=False):
    """Print the preflight check block.

    Args:
        pf: preflight dict
        verbose: if True, show feature extraction details
    """
    confidence = pf["confidence"]
    plan = pf["plan"]
    issues = pf["ambiguity_issues"]
    opt = pf.get("optimal_stopping")
    score = pf.get("ambiguity_score")

    # Confidence icon — use optimal stopping boundary if available
    conf_icon = {"HIGH": "🟢", "MED": "🟡", "LOW": "🔴"}[confidence]
    if opt:
        boundary = opt["decision_boundary"]
        conf_action = opt["action"]
        boundary_icon = {"clear": "🟢", "boundary": "🟡", "ambiguous": "🔴"}[boundary]
    else:
        conf_action = {
            "HIGH": "auto-execute (30s cancel window)",
            "MED": "wait for confirmation",
            "LOW": "answer questions first",
        }[confidence]
        boundary_icon = conf_icon

    score_str = f" (score:{score}/100)" if score is not None else ""
    print(f"╭─ TASK PREFLIGHT ──────────────────────────────────────────╮")
    print(f"│ {conf_icon} Confidence: {confidence}{score_str} — {conf_action:<35} │")
    print(f"├───────────────────────────────────────────────────────────┤")
    print(f"│ Goal: {pf['title'][:52]:<52} │")
    if pf.get("source"):
        print(f"│ Source: {pf['source']:<50} │")
    if pf.get("project"):
        print(f"│ Project: {pf['project'][:49]:<49} │")
    scope = plan.get("scope", plan.get("steps", []))[:3]
    if scope and isinstance(scope[0], dict):
        scope = [s["name"] for s in scope[:3]]
    print(f"│ Scope: {', '.join(str(s) for s in scope)[:50]:<50} │")
    steps = plan.get("steps", [])
    if steps:
        print(f"│ Steps: {len(steps)} steps{' '*44}│")
        for i, step in enumerate(steps, 1):
            name = step["name"] if isinstance(step, dict) else step
            print(f"│   {i}. {name:<55}│")
    print(f"├───────────────────────────────────────────────────────────┤")

    if issues:
        print(f"│ ⚠️  Ambiguities ({len(issues)}):{' '*38}│")
        for issue in issues:
            sev = {"high": "🔴", "medium": "🟡"}[issue["severity"]]
            q = issue.get("formatted_question", issue["question"])[:48]
            print(f"│   {sev} {q:<54}│")
        print(f"├───────────────────────────────────────────────────────────┤")

    # Show optimal stopping decision if available
    if opt:
        boundary_sym = {"clear": "🟢", "boundary": "🟡", "ambiguous": "🔴"}[opt["decision_boundary"]]
        print(f"│ {boundary_sym} Decision: {opt['decision_boundary']:<46} │")
        print(f"│   V(info)={opt['V_info']:.0f}  C(ask)={opt['C_ask']:.0f}  {opt['reason']:<25} │")
        print(f"├───────────────────────────────────────────────────────────┤")

    # Verbose: show Bayesian feature details
    if verbose:
        features = pf.get("features", {})
        if features:
            print(f"│ 🔍 Features (verbose):{' '*36}│")
            print(f"│   desc_length:     {features.get('desc_length', '?'):<39} │")
            print(f"│   file_refs:       {features.get('file_refs', 0):<39} │")
            print(f"│   action_verbs:    {features.get('action_verbs', 0):<39} │")
            print(f"│   screenshot_refs: {features.get('screenshot_refs', 0):<39} │")
            print(f"│   component_refs:  {features.get('component_refs', 0):<39} │")
            print(f"│   specificity:     {features.get('specificity_score', 0):.1f}/100{' '*30} │")
            lr = pf.get("likelihood_ratio")
            if lr is not None:
                print(f"│   likelihood_ratio: {lr:<38} │")
            # Show binary features
            binary_on = [k for k in ['short_desc','no_file_refs','no_action_verbs','no_screenshot',
                         'no_component','vague_goal','destructive','optimization','prototype_no_spec']
                        if features.get(k, False)]
            if binary_on:
                for feat in binary_on[:5]:
                    print(f"│   ⚡ {feat:<52} │")
            print(f"├───────────────────────────────────────────────────────────┤")

    if pf.get("auto_resolved"):
        print(f"│ ✅ Auto-resolved:{' '*40}│")
        for item in pf["auto_resolved"][:3]:
            print(f"│   - {item[:53]:<53}│")
        print(f"├───────────────────────────────────────────────────────────┤")

    print(f"│ Action: go=approve | stop=cancel | input=clarify{' '*14}│")
    print(f"╰───────────────────────────────────────────────────────────╯")


def cmd_approve(task_id):
    """Approve the preflight and start execution."""
    pf = load(task_id)
    if not pf:
        print(f"Preflight not found: {task_id}")
        return

    pf["status"] = "approved"
    pf["approved_at"] = datetime.now(timezone.utc).isoformat()
    save(task_id, pf)

    # Copy to observer for monitoring (source-agnostic)
    observer_data = {
        "task_id": task_id,
        "title": pf["title"],
        "source": pf.get("source", "direct"),
        "project": pf.get("project", ""),
        "priority": pf.get("priority", "P2"),
        "lane": pf.get("lane", "work"),
        "acceptance_criteria": pf.get("acceptance_criteria", []),
        "expected_screenshots": pf.get("expected_screenshots", []),
        "referenced_files": pf.get("referenced_files", []),
        "plan": pf["plan"],
        "steps": [{"name": s["name"] if isinstance(s, dict) else s, "status": "pending"} for s in pf["plan"]["steps"]],
        "current_step_idx": 0,
        "events": [],
        "started_at": datetime.now(timezone.utc).isoformat(),
        "status": "running",
        "confidence": pf["confidence"],
        "clarifications": pf.get("clarifications", []),
        "gates": [],
    }
    OBSERVER_DIR.mkdir(parents=True, exist_ok=True)
    (OBSERVER_DIR / f"{task_id}.json").write_text(json.dumps(observer_data, indent=2, ensure_ascii=False))

    print(f"✅ Preflight approved. Execution plan ready.")
    steps = pf["plan"]["steps"]
    step_names = [s["name"] if isinstance(s, dict) else s for s in steps]
    print(f"   Steps: {' -> '.join(step_names)}")
    print(f"   Observer monitoring started.")


def cmd_clarify(task_id, answer):
    """Record a clarification from the human."""
    pf = load(task_id)
    if not pf:
        print(f"Preflight not found: {task_id}")
        return

    pf["clarifications"].append({
        "ts": datetime.now(timezone.utc).isoformat(),
        "answer": answer,
    })

    # Re-analyze with Bayesian inference
    combined_desc = f"{pf['description']} {answer}"
    result = classify_confidence_from_title_desc(pf["title"], combined_desc)
    issues = result['issues']
    new_confidence = result['confidence']
    score = result['score']

    pf["ambiguity_issues"] = issues
    pf["confidence"] = new_confidence
    pf["ambiguity_score"] = score
    pf["features"] = result['features']
    pf["likelihood_ratio"] = result['likelihood_ratio']
    save(task_id, pf)

    print(f"Clarification recorded. New confidence: {new_confidence} (score: {score}/100)")
    if issues:
        print(f"Remaining issues: {len(issues)}")
        for issue in issues:
            q = issue.get("formatted_question", issue["question"])
            print(f"  ⚠️ {q}")
    else:
        print(f"✅ All ambiguities resolved. Ready to execute.")
        print(f"   Run: python3 task_preflight.py approve {task_id}")


def cmd_reject(task_id, reason):
    """Reject the preflight."""
    pf = load(task_id)
    if not pf:
        print(f"Preflight not found: {task_id}")
        return

    pf["status"] = "rejected"
    pf["rejected_at"] = datetime.now(timezone.utc).isoformat()
    pf["rejection_reason"] = reason
    save(task_id, pf)

    print(f"❌ Preflight rejected: {reason}")


def cmd_status(task_id):
    """Show preflight status."""
    pf = load(task_id)
    if not pf:
        print(f"Preflight not found: {task_id}")
        return

    print(f"Task: {pf['title']}")
    print(f"Source: {pf.get('source', 'unknown')}")
    print(f"Project: {pf.get('project', 'unknown')}")
    print(f"Status: {pf['status']}")
    print(f"Confidence: {pf['confidence']}")
    print(f"Clarifications: {len(pf.get('clarifications', []))}")
    if pf.get("ambiguity_issues"):
        print(f"Open issues: {len(pf['ambiguity_issues'])}")


def main():
    if len(sys.argv) < 2:
        print("Usage: task_preflight.py <command> [args]")
        print("Commands: check, check-adapter, approve, clarify, reject, status")
        print("Options: --verbose (show Bayesian feature details)")
        return

    verbose = "--verbose" in sys.argv
    cmd = sys.argv[1]

    if cmd == "check":
        task_id = sys.argv[2]
        title = ""
        desc = ""
        for i, arg in enumerate(sys.argv):
            if arg == "--title" and i + 1 < len(sys.argv): title = sys.argv[i + 1]
            if arg == "--description" and i + 1 < len(sys.argv): desc = sys.argv[i + 1]
        pf = cmd_check(task_id, title, desc, verbose=verbose)

    elif cmd == "check-adapter":
        task_id = sys.argv[2]
        spec_file = None
        adapter_name = None
        for i, arg in enumerate(sys.argv):
            if arg == "--spec-file" and i + 1 < len(sys.argv): spec_file = sys.argv[i + 1]
            if arg == "--adapter" and i + 1 < len(sys.argv): adapter_name = sys.argv[i + 1]
        spec_data = {}
        if spec_file and os.path.exists(spec_file):
            with open(spec_file) as f:
                spec_data = json.load(f)
        cmd_check_adapter(task_id, spec_data, adapter_name)

    elif cmd == "approve":
        cmd_approve(sys.argv[2])

    elif cmd == "clarify":
        task_id = sys.argv[2]
        answer = ""
        for i, arg in enumerate(sys.argv):
            if arg == "--answer" and i + 1 < len(sys.argv): answer = sys.argv[i + 1]
        cmd_clarify(task_id, answer)

    elif cmd == "reject":
        task_id = sys.argv[2]
        reason = sys.argv[3] if len(sys.argv) > 3 else "no reason"
        cmd_reject(task_id, reason)

    elif cmd == "status":
        cmd_status(sys.argv[2])

    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
