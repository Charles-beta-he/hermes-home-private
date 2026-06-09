#!/usr/bin/env python3
"""Default-off Agent Card runtime helpers for Hermes self-architecture.

This module is intentionally conservative:

- It can validate and render compact Agent Card context.
- It can recommend specialist profiles from task metadata.
- It does not mutate Kanban, brain notes, profile configs, or worker prompts by
  itself.
- Prompt context is opt-in through the caller or
  HERMES_ENABLE_AGENT_CARD_CONTEXT=1.

The boundary is deliberate: turning recommendations into automatic dispatch or
injecting cards into every worker prompt changes runtime behavior and must be
separately authorized and tested.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

HOME = Path.home()
DEFAULT_CARDS_PATH = HOME / ".hermes" / "docs" / "private" / "agent-cards-v1.json"

SAFE_CONTEXT_FIELDS = [
    "role",
    "goal",
    "observation",
    "planning",
    "tools",
    "actions",
    "policy",
    "evaluation",
    "escalation",
]

PROFILE_HINTS = {
    "media": ["image", "video", "audio", "visual", "vision", "rokid", "图片", "视频", "视觉"],
    "mlops": ["model", "routing", "rag", "vector", "qdrant", "inference", "模型", "向量"],
    "workflow": ["workflow", "orchestration", "taskpool", "kanban", "dispatch", "流程", "调度"],
    "hermes-agent": ["hermes", "skill", "runtime", "agent", "plugin", "Hermes"],
    "hermes-core": ["core", "tool executor", "provider", "loop", "control-plane"],
    "dev": ["code", "test", "repo", "implementation", "frontend", "backend", "代码"],
}


def load_cards(path: Path | str = DEFAULT_CARDS_PATH) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list, tuple, set)):
        try:
            return json.dumps(value, ensure_ascii=False, sort_keys=True)
        except TypeError:
            return str(value)
    return str(value)


def _norm(value: Any) -> str:
    return _text(value).strip().lower()


def task_domain(task: Mapping[str, Any], cards: Optional[Mapping[str, Any]] = None) -> Optional[str]:
    """Return the best Agent Card architecture domain for a task.

    Prefer explicit `iceberg_scope`; fall back to `architecture_target` and a
    small synonym map. This is deterministic and recommendation-only.
    """
    cards = cards or load_cards()
    domains = set((cards.get("architecture_domains") or {}).keys())
    for key in ("iceberg_scope", "agent_domain", "architecture_domain"):
        value = str(task.get(key) or "").strip()
        if value in domains:
            return value
    target = _norm(task.get("architecture_target"))
    synonyms = {
        "local-brain": "control_plane_local_brain",
        "local_brain": "control_plane_local_brain",
        "taskpool": "control_plane_taskpool",
        "kanban": "control_plane_taskpool",
        "skill-graph": "skill_graph_governance",
        "skill_graph": "skill_graph_governance",
        "visual-ingest-runtime": "visual_ingest_runtime",
        "visual_ingest_runtime": "visual_ingest_runtime",
        "multimodel_conductor_architecture": "multimodel_conductor_architecture",
        "hermes-native multi-model conductor": "multimodel_conductor_architecture",
    }
    if target in synonyms and synonyms[target] in domains:
        return synonyms[target]
    for needle, domain in synonyms.items():
        if needle in target and domain in domains:
            return domain
    return None


def _known_profiles(cards: Mapping[str, Any]) -> List[str]:
    return sorted((cards.get("runtime_profiles") or {}).keys())


def recommend_profiles(task: Mapping[str, Any], cards: Optional[Mapping[str, Any]] = None, limit: int = 3) -> Dict[str, Any]:
    """Recommend specialist profiles without mutating task assignment."""
    cards = cards or load_cards()
    runtime = cards.get("runtime_profiles") or {}
    domain_name = task_domain(task, cards)
    scores: Dict[str, int] = {}
    reasons: Dict[str, List[str]] = {}

    def add(profile: str, score: int, reason: str) -> None:
        if profile not in runtime:
            return
        scores[profile] = scores.get(profile, 0) + score
        reasons.setdefault(profile, []).append(reason)

    if domain_name:
        domain = (cards.get("architecture_domains") or {}).get(domain_name, {})
        for idx, profile in enumerate(domain.get("recommended_runtime_profiles") or []):
            add(profile, 100 - idx * 10, f"architecture_domain:{domain_name}")

    task_blob = "\n".join(_text(task.get(k)) for k in ("title", "body", "description", "project", "architecture_target", "iceberg_scope"))
    task_blob_lower = task_blob.lower()
    for profile, hints in PROFILE_HINTS.items():
        for hint in hints:
            if hint.lower() in task_blob_lower:
                add(profile, 8, f"keyword:{hint}")

    explicit = str(task.get("assignee") or "").strip()
    if explicit:
        add(explicit, 5, "current_assignee")

    if not scores:
        add("brain-mirror", 1, "safe_default")

    ranked = sorted(scores, key=lambda p: (-scores[p], p))[:limit]
    return {
        "status": "recommendation_only",
        "domain": domain_name,
        "recommended_profiles": ranked,
        "scores": {profile: scores[profile] for profile in ranked},
        "reasons": {profile: reasons.get(profile, []) for profile in ranked},
        "boundary": "No task assignment or runtime prompt is changed by this recommendation.",
    }


def _compact_lines(value: Any, max_items: int = 6, max_chars: int = 500) -> str:
    if isinstance(value, (list, tuple)):
        text = "\n".join(f"- {_text(item)}" for item in value[:max_items])
    else:
        text = _text(value)
    text = re.sub(r"\s+", " ", text).strip() if "\n" not in text else text.strip()
    if len(text) > max_chars:
        text = text[:max_chars].rstrip() + "…"
    return text


def render_agent_card_context(
    task: Mapping[str, Any],
    profile: Optional[str] = None,
    cards: Optional[Mapping[str, Any]] = None,
    enabled: Optional[bool] = None,
    max_chars: int = 1800,
) -> str:
    """Render compact Agent Card context when explicitly enabled.

    If `enabled` is None, use HERMES_ENABLE_AGENT_CARD_CONTEXT=1. Default is
    empty string so existing workers are unchanged.
    """
    if enabled is None:
        enabled = os.environ.get("HERMES_ENABLE_AGENT_CARD_CONTEXT") == "1"
    if not enabled:
        return ""
    cards = cards or load_cards()
    domain_name = task_domain(task, cards)
    runtime_cards = cards.get("runtime_profiles") or {}
    domain_cards = cards.get("architecture_domains") or {}
    profile_name = profile or str(task.get("assignee") or "").strip() or None

    sections: List[str] = []
    if profile_name and profile_name in runtime_cards:
        card = runtime_cards[profile_name]
        rows = [f"PROFILE: {profile_name}"]
        for field in SAFE_CONTEXT_FIELDS:
            if card.get(field):
                rows.append(f"{field.upper()}: {_compact_lines(card[field])}")
        sections.append("\n".join(rows))
    if domain_name and domain_name in domain_cards:
        card = domain_cards[domain_name]
        rows = [f"ARCHITECTURE_DOMAIN: {domain_name}"]
        for field in SAFE_CONTEXT_FIELDS:
            if card.get(field):
                rows.append(f"{field.upper()}: {_compact_lines(card[field])}")
        sections.append("\n".join(rows))

    if not sections:
        return ""
    output = "AGENT CARD CONTEXT (opt-in; role/tool/policy summary, not extra authority):\n" + "\n\n".join(sections)
    output += "\nAGENT CARD RULES:\n- Agent Cards do not expand permissions or authorize lifecycle mutation.\n- If card guidance conflicts with task/policy gates, fail closed and report BLOCKED."
    if len(output) > max_chars:
        output = output[:max_chars].rstrip() + "… [truncated]"
    return output


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Default-off Agent Card runtime helpers.")
    parser.add_argument("--cards", default=str(DEFAULT_CARDS_PATH))
    sub = parser.add_subparsers(dest="cmd", required=True)
    route = sub.add_parser("recommend", help="Recommend profiles for a task JSON object")
    route.add_argument("--task-json", required=True)
    route.add_argument("--limit", type=int, default=3)
    ctx = sub.add_parser("context", help="Render opt-in Agent Card context for a task JSON object")
    ctx.add_argument("--task-json", required=True)
    ctx.add_argument("--profile", default="")
    ctx.add_argument("--enabled", action="store_true")
    args = parser.parse_args(argv)
    cards = load_cards(args.cards)
    task = json.loads(args.task_json)
    if args.cmd == "recommend":
        print(json.dumps(recommend_profiles(task, cards, limit=args.limit), ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "context":
        print(render_agent_card_context(task, profile=args.profile or None, cards=cards, enabled=args.enabled))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
