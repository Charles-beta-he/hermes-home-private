#!/usr/bin/env python3
"""Multi-model review packet generator for Hermes upstream ratchet upgrades.

This is the semantic review layer above upstream-ratchet-watch.py. It does not
merge, rebase, checkout, push, or promote private/main. It builds a bounded
review packet for official upstream movement, asks the configured real
multi-model panel for review, and records the resulting packet as evidence.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HOME = Path.home()
HERMES_HOME = HOME / ".hermes"
DEFAULT_REPO = HERMES_HOME / "hermes-agent"
DEFAULT_WATCH_STATE = HERMES_HOME / "state" / "upstream-ratchet.json"
DEFAULT_REVIEW_STATE = HERMES_HOME / "state" / "upstream-ratchet-review.json"
DEFAULT_REPORT_DIR = HERMES_HOME / "reports" / "upstream-ratchet"
WATCHER_SCRIPT = HERMES_HOME / "scripts" / "upstream-ratchet-watch.py"
CONSULT_SCRIPT = HERMES_HOME / "scripts" / "consult_models.py"
SCHEMA = "hermes_private_upstream_ratchet_review_v1"
REDACTION = "[REDACTED]"
SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret|password|passwd|token|access[_-]?token|refresh[_-]?token)\s*[:=]\s*(['\"]?)[^'\"\s,}]{6,}\2"),
    re.compile(r"(?i)(authorization:\s*bearer\s+)[A-Za-z0-9._~+\-/=]{12,}"),
    re.compile(r"\bsk-[A-Za-z0-9]{16,}\b"),
    re.compile(r"\b[A-Za-z0-9_\-]{32,}\.[A-Za-z0-9_\-]{16,}\.[A-Za-z0-9_\-]{16,}\b"),
]


class ReviewError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default
    except json.JSONDecodeError as exc:
        raise ReviewError(f"bad JSON at {path}: {exc}") from exc


def write_json_atomic(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp-{os.getpid()}")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def run_git(repo: Path, args: list[str], *, timeout: int = 60, check: bool = True) -> str:
    proc = subprocess.run(["git", *args], cwd=repo, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    out = (proc.stdout or "").strip()
    err = (proc.stderr or "").strip()
    if check and proc.returncode != 0:
        raise ReviewError(f"git {' '.join(args)} failed ({proc.returncode}): {err or out}")
    return out


def load_watcher_module():
    spec = importlib.util.spec_from_file_location("upstream_ratchet_watch", WATCHER_SCRIPT)
    if not spec or not spec.loader:
        raise ReviewError(f"cannot load watcher script: {WATCHER_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def collect_watch_report(repo: Path, no_fetch: bool, watch_state: Path = DEFAULT_WATCH_STATE) -> dict[str, Any]:
    watcher = load_watcher_module()
    report, _ = watcher.collect(repo, watch_state, repo / "docs/private/overlay-registry.md", no_fetch=no_fetch)
    return report


def trunc(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n...<truncated {len(text) - limit} chars>"


def redact_text(text: str) -> str:
    redacted = text
    for pat in SECRET_PATTERNS:
        def repl(match: re.Match[str]) -> str:
            lower = match.group(0).lower()
            if "authorization:" in lower:
                return re.sub(r"(?i)(authorization:\s*bearer\s+).+", r"\1" + REDACTION, match.group(0))
            key_match = re.match(r"(?i)(api[_-]?key|secret|password|passwd|token|access[_-]?token|refresh[_-]?token)", match.group(0))
            if key_match:
                return f"{key_match.group(1)}={REDACTION}"
            return REDACTION
        redacted = pat.sub(repl, redacted)
    return redacted


def redact_obj(value: Any) -> Any:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        return [redact_obj(v) for v in value]
    if isinstance(value, dict):
        return {k: redact_obj(v) for k, v in value.items()}
    return value


def build_file_focus(repo: Path, base: str, head: str, paths: list[str], *, max_files: int = 12, per_file_chars: int = 4500) -> list[dict[str, Any]]:
    focus: list[dict[str, Any]] = []
    for path in paths[:max_files]:
        diff = run_git(repo, ["diff", "--find-renames", "--unified=40", f"{base}..{head}", "--", path], timeout=120, check=False)
        focus.append({"path": path, "diff_excerpt": trunc(diff, per_file_chars)})
    return focus


def unique_impacted_paths(watch: dict[str, Any]) -> list[str]:
    paths: list[str] = []
    for overlay in watch.get("impact_map", {}).get("impacted_overlays", []) or []:
        for path in overlay.get("matched_paths", []) or []:
            if path not in paths:
                paths.append(path)
    return paths


def build_review_state(repo: Path, watch: dict[str, Any], out_dir: Path) -> tuple[dict[str, Any], Path]:
    merge_base = watch["merge_base"]
    upstream_sha = watch["upstream_sha"]
    private_sha = watch["private_sha"]
    changed_paths = run_git(repo, ["diff", "--name-only", f"{merge_base}..{upstream_sha}"], timeout=120).splitlines()
    name_status = run_git(repo, ["diff", "--name-status", f"{merge_base}..{upstream_sha}"], timeout=120)
    diff_stat = run_git(repo, ["diff", "--stat", f"{merge_base}..{upstream_sha}"], timeout=120)
    commit_log = run_git(repo, ["log", "--oneline", "--decorate=no", f"{merge_base}..{upstream_sha}", "--"], timeout=120)
    impacted_paths = unique_impacted_paths(watch)
    focus_paths = impacted_paths or changed_paths[:12]
    focus_diffs = build_file_focus(repo, merge_base, upstream_sha, focus_paths)

    packet = redact_obj({
        "schema": SCHEMA,
        "generated_at": utc_now(),
        "repo": str(repo),
        "private_sha": private_sha,
        "upstream_sha": upstream_sha,
        "merge_base": merge_base,
        "range": f"{merge_base}..{upstream_sha}",
        "watch_report": watch,
        "changed_path_count": len(changed_paths),
        "changed_paths_sample": changed_paths[:180],
        "name_status_excerpt": trunc(name_status, 12000),
        "diff_stat": trunc(diff_stat, 12000),
        "commit_log_excerpt": trunc(commit_log, 18000),
        "focus_paths": focus_paths[:12],
        "focus_diffs": focus_diffs,
    })
    packet_path = out_dir / "review-input-packet.json"
    write_json_atomic(packet_path, packet)

    question = (
        "Review official upstream Hermes changes for a private fork ratchet upgrade. "
        "Decide risks and next actions without merging or promoting private/main. "
        "Return a concrete review packet: upstream feature summary, breaking changes, impacted private overlays, "
        "overlay decisions keep/replay/redesign/retire-candidate, required tests, safety blockers, and whether it is safe "
        "to create the proposed integrate branch. Be adversarial and evidence-bound."
    )
    state = redact_obj({
        "schema": "hermes_multimodel_task_v1",
        "question": question,
        "context": packet,
        "constraints": [
            "No auto-merge, no rebase, no checkout, no push, no private/main promotion.",
            "Path overlap alone cannot retire an overlay; require behavioral equivalence evidence.",
            "Dirty worktree and large divergence are blockers for starting integration, not blockers for review packet generation.",
            "If evidence is insufficient, request specific commands/files rather than claiming certainty.",
            "Output must distinguish deterministic evidence from model judgment.",
        ],
        "acceptance_criteria": [
            "Review identifies impacted overlays and required verification commands.",
            "Review states safe_to_create_integrate_branch true/false with reasons.",
            "Review provides no-action ratchet decision, not implementation patches that mutate private/main.",
            "Review has no secrets and does not instruct bypassing governance gates.",
        ],
        "implementation_target": {
            "files": ["docs/private/overlay-registry.md", "docs/private/upgrade-sop.md"],
            "verify_commands": [
                "python3 ~/.hermes/scripts/upstream-ratchet-watch.py --pretty --no-fetch",
                "python3 ~/.hermes/scripts/post-update-check.py --fix",
                "targeted pytest/doctor/smoke commands selected by impacted overlays",
            ],
            "forbidden_changes": ["private/main promotion without evidence", "automatic merge/rebase/push"],
        },
        "claims": [
            {"id": "C-001", "text": "The review is semantic multi-model review, not just path impact mapping.", "severity": 3},
            {"id": "C-002", "text": "The ratchet remains no-action until integration evidence is collected.", "severity": 3},
        ],
        "evidence": [
            {
                "id": "E-watch-report",
                "type": "watch_report",
                "kind": "orchestrator_evidence",
                "path": str(DEFAULT_WATCH_STATE),
                "supports": ["C-001", "C-002"],
                "summary": {k: watch.get(k) for k in ["upstream_sha", "private_sha", "merge_base", "safety_blockers", "proposed_integration_branch", "ratchet_stage"]},
            },
            {
                "id": "E-review-input-packet",
                "type": "review_input_packet",
                "kind": "orchestrator_evidence",
                "path": str(packet_path),
                "supports": ["C-001"],
            },
        ],
    })
    state_path = out_dir / "multimodel-state.json"
    write_json_atomic(state_path, state)
    return state, state_path


def summarize_model_output(merged: dict[str, Any]) -> dict[str, Any]:
    return {
        "certification_status": merged.get("certification_status") or merged.get("status"),
        "diagnosis_summary": (merged.get("diagnosis") or {}).get("summary") or merged.get("summary"),
        "patch_count": len(merged.get("patches") or []),
        "planner_patch_summary": merged.get("planner_patch_summary", {}),
        "fanout_certification": merged.get("fanout_certification", {}),
        "truth_assessment": merged.get("truth_assessment", {}),
        "discussion": merged.get("discussion", {}),
    }


def model_review_certified(merged: dict[str, Any], *, discussion_required: bool) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    fanout_raw = merged.get("fanout_certification")
    truth_raw = merged.get("truth_assessment")
    discussion_raw = merged.get("discussion")
    fanout = fanout_raw if isinstance(fanout_raw, dict) else {}
    truth = truth_raw if isinstance(truth_raw, dict) else {}
    discussion = discussion_raw if isinstance(discussion_raw, dict) else {}
    if fanout.get("certified") is not True:
        reasons.append("fanout_not_certified")
    if truth and truth.get("can_certify_truth") is False:
        reasons.append("truth_gate_rejected")
    if discussion_required and discussion.get("can_claim_complete_certification") is not True:
        reasons.append("discussion_not_certified")
    return (not reasons, reasons)


def run_multimodel(state_path: Path, *, tier: str, timeout: int, discussion: bool) -> dict[str, Any]:
    cmd = [sys.executable, str(CONSULT_SCRIPT), "run", str(state_path), "--tier", tier, "--keep", "--timeout", str(timeout)]
    if discussion:
        cmd.extend(["--discussion", "--max-rounds", "3"])
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=max(timeout * 8, 600))
    if proc.returncode != 0:
        raise ReviewError(f"consult_models failed ({proc.returncode}): {trunc(proc.stderr or proc.stdout, 4000)}")
    try:
        merged = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise ReviewError(f"consult_models returned non-JSON stdout: {exc}; stderr={trunc(proc.stderr, 2000)}") from exc
    return {
        "merged_plan": merged,
        "stdout_excerpt": trunc(proc.stdout, 2000),
        "stderr_excerpt": trunc(proc.stderr, 4000),
    }


def review_needed(review_state: dict[str, Any], upstream_sha: str, *, force: bool) -> bool:
    if force:
        return True
    reviewed = review_state.get("reviewed_upstream", {})
    return reviewed.get(upstream_sha, {}).get("status") != "reviewed"


def run_review(args: argparse.Namespace) -> tuple[dict[str, Any], bool]:
    repo = Path(args.repo).expanduser().resolve()
    review_state_path = Path(args.review_state).expanduser()
    watch_state_path = Path(getattr(args, "watch_state", DEFAULT_WATCH_STATE)).expanduser()
    review_state = read_json(review_state_path, {})
    watch = collect_watch_report(repo, no_fetch=args.no_fetch, watch_state=watch_state_path)
    upstream_sha = watch["upstream_sha"]
    out_dir = Path(args.report_dir).expanduser() / upstream_sha[:12]

    if args.only_if_needed and not review_needed(review_state, upstream_sha, force=args.force):
        return ({"schema": SCHEMA, "generated_at": utc_now(), "status": "no_review_needed", "upstream_sha": upstream_sha, "report_dir": str(out_dir)}, False)

    _, state_path = build_review_state(repo, watch, out_dir)
    if args.dry_run:
        model_result = {"merged_plan": {"status": "dry_run", "summary": "model calls skipped"}, "stdout_excerpt": "", "stderr_excerpt": ""}
    else:
        model_result = run_multimodel(state_path, tier=args.tier, timeout=args.timeout, discussion=args.discussion)

    review_certified, review_reasons = (
        (True, []) if args.dry_run else model_review_certified(model_result["merged_plan"], discussion_required=args.discussion)
    )
    packet_status = "dry_run_review_packet_built" if args.dry_run else ("reviewed" if review_certified else "review_not_certified")

    review_packet = redact_obj({
        "schema": SCHEMA,
        "generated_at": utc_now(),
        "status": packet_status,
        "review_certified": review_certified,
        "review_not_certified_reasons": review_reasons,
        "ratchet_stage": "semantic_multimodel_review_packet",
        "repo": str(repo),
        "upstream_sha": upstream_sha,
        "private_sha": watch["private_sha"],
        "merge_base": watch["merge_base"],
        "proposed_integration_branch": watch.get("proposed_integration_branch"),
        "safety_blockers": watch.get("safety_blockers", []),
        "impacted_overlays": watch.get("impact_map", {}).get("impacted_overlays", []),
        "review_input_state": str(state_path),
        "model_summary": summarize_model_output(model_result["merged_plan"]),
        "model_artifacts": {
            "consult_stderr_excerpt": model_result.get("stderr_excerpt"),
        },
        "next_steps": [
            "Use this packet as review evidence only; do not auto-promote private/main.",
            "If dirty_worktree_blocks_integration_branch_creation is present, clean/scope current work before branch creation.",
            "Create the proposed integrate branch only after reviewing this packet and batching large divergence if needed.",
            "Replay/retire overlays only with deterministic tests or explicit equivalence evidence.",
        ],
    })
    packet_path = out_dir / "review-packet.json"
    write_json_atomic(packet_path, review_packet)

    if not args.dry_run:
        reviewed = dict(review_state.get("reviewed_upstream") or {})
        reviewed_status = "reviewed" if review_certified else "not_certified"
        reviewed[upstream_sha] = {
            "status": reviewed_status,
            "reviewed_at": review_packet["generated_at"],
            "private_sha": watch["private_sha"],
            "merge_base": watch["merge_base"],
            "report_dir": str(out_dir),
            "packet_path": str(packet_path),
        }
        new_state = dict(review_state)
        new_state.update({
            "schema": SCHEMA,
            "last_reviewed_at": review_packet["generated_at"],
            "last_reviewed_upstream_sha": upstream_sha,
            "last_packet_path": str(packet_path),
            "reviewed_upstream": reviewed,
        })
        write_json_atomic(review_state_path, new_state)

    summary = {
        "schema": SCHEMA,
        "generated_at": review_packet["generated_at"],
        "status": review_packet["status"],
        "upstream_sha": upstream_sha,
        "private_sha": watch["private_sha"],
        "report_dir": str(out_dir),
        "packet_path": str(packet_path),
        "ratchet_stage": review_packet["ratchet_stage"],
        "safety_blockers": review_packet["safety_blockers"],
        "impacted_overlay_count": len(review_packet["impacted_overlays"]),
        "model_summary": review_packet["model_summary"],
        "review_certified": review_certified,
        "review_not_certified_reasons": review_reasons,
    }
    return summary, True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate semantic multi-model review packets for Hermes upstream ratchet upgrades")
    parser.add_argument("--repo", default=str(DEFAULT_REPO))
    parser.add_argument("--review-state", default=str(DEFAULT_REVIEW_STATE))
    parser.add_argument("--watch-state", default=str(DEFAULT_WATCH_STATE))
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--tier", default="T2")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--discussion", action="store_true")
    parser.add_argument("--no-fetch", action="store_true")
    parser.add_argument("--only-if-needed", action="store_true")
    parser.add_argument("--quiet-no-needed", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)

    try:
        report, should_print = run_review(args)
    except ReviewError as exc:
        err = {"schema": SCHEMA, "generated_at": utc_now(), "status": "error", "error": str(exc)}
        print(json.dumps(err, ensure_ascii=False, indent=2 if args.pretty else None))
        return 2
    if should_print or not args.quiet_no_needed:
        print(json.dumps(report, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
