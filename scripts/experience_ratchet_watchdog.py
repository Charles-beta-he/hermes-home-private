#!/usr/bin/env python3
"""Local-only Experience Ratchet watchdog.

Checks the external dev-brain experience-ratchet overlay without mutating
skills, memory, profiles, taskpool, project docs, or external systems.

Default cron behavior: success-silent, print JSON only when unhealthy/actionable.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "hermes_experience_ratchet_watchdog_v1"
DEFAULT_TAGS = {
    "pwa", "rn", "react-native", "react_native", "mobile", "frontend",
    "compatibility", "safe-area", "service-worker", "webview",
}
PWA_KEYWORDS = [
    "pwa", "service worker", "service-worker", "manifest", "installed pwa",
    "home screen", "webapk", "safe-area", "missing chunk", "cache", "web push",
    "standalone", "safari", "android chrome", "beforeinstallprompt",
]
RN_KEYWORDS = [
    "react native", "expo", "ios simulator", "android emulator",
    "native bridge", "native module", "pod install", "gradle", "permission",
    "camera", "microphone", "photo library", "asyncstorage", "keychain",
    "keystore", "deep link", "push token", "real device",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default
    except json.JSONDecodeError as exc:
        return {"_error": f"json_decode_error:{exc}", "_path": str(path)}


def run_validate(script: Path, home: Path, timeout: int) -> dict[str, Any]:
    if not script.exists():
        return {"ok": False, "checked": 0, "exit_code": 127, "error": f"missing script: {script}"}
    try:
        proc = subprocess.run(
            ["python3", str(script), "--home", str(home), "validate"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return {"ok": False, "checked": 0, "exit_code": 124, "error": f"validate timeout after {timeout}s", "stdout_tail": (exc.stdout or "")[-1000:] if isinstance(exc.stdout, str) else ""}
    payload: dict[str, Any]
    try:
        payload = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        payload = {"ok": False, "checked": 0, "error": "validate emitted non-json", "stdout_tail": (proc.stdout or "")[-1000:]}
    payload["exit_code"] = proc.returncode
    if proc.stderr:
        payload["stderr_tail"] = proc.stderr[-1000:]
    if proc.returncode != 0:
        payload["ok"] = False
    return payload


def parse_iso(value: str | None) -> float | None:
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value).timestamp()
    except Exception:
        return None


def atom_time(atom: dict[str, Any]) -> float | None:
    source = atom.get("source") or {}
    candidates: list[str | None] = []
    for item in reversed(atom.get("history") or []):
        if isinstance(item, dict):
            candidates.append(item.get("at"))
    candidates.append(source.get("captured_at"))
    for value in candidates:
        ts = parse_iso(value)
        if ts is not None:
            return ts
    return None


def load_atoms(home: Path) -> list[dict[str, Any]]:
    atoms_dir = home / "atoms"
    atoms: list[dict[str, Any]] = []
    if not atoms_dir.exists():
        return atoms
    for path in sorted(atoms_dir.glob("*.json")):
        atom = read_json(path, {})
        if isinstance(atom, dict):
            atom["_path"] = str(path)
            atoms.append(atom)
    return atoms


def list_proposals(home: Path) -> list[Path]:
    proposals = home / "proposals"
    if not proposals.exists():
        return []
    return sorted(p for p in proposals.glob("*.json") if p.is_file())


def text_blob(atom: dict[str, Any]) -> str:
    parts = [atom.get("title"), atom.get("claim_text")]
    cls = atom.get("classification") or {}
    parts.extend(cls.get("domain_tags") or [])
    parts.append(cls.get("pattern_type"))
    src = atom.get("source") or {}
    parts.append(src.get("project"))
    return " ".join(str(p or "") for p in parts).lower()


def has_any(text: str, needles: list[str] | set[str]) -> bool:
    return any(n.lower() in text for n in needles)


def staged_skill_candidate_keys(staging_dir: Path) -> set[str]:
    keys: set[str] = set()
    if not staging_dir.exists():
        return keys
    for path in list(staging_dir.glob("*.json")) + list(staging_dir.glob("*.md")):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        keys.update(re.findall(r"[a-z0-9][a-z0-9._-]+-[0-9a-f]{12}", text.lower()))
        if path.suffix == ".json":
            try:
                payload = json.loads(text)
            except Exception:
                payload = {}
            title = str(payload.get("title") or "").strip().lower()
            if title:
                keys.add(title)
    return keys


def summarize_atoms(atoms: list[dict[str, Any]], now_ts: float, stale_days: int, staged_keys: set[str]) -> dict[str, Any]:
    by_status = Counter(str(a.get("status") or "unknown") for a in atoms)
    by_landing = Counter(str((a.get("classification") or {}).get("target_landing_zone") or "unknown") for a in atoms)
    stale_cutoff = now_ts - stale_days * 86400
    stale: list[dict[str, Any]] = []
    actionable_skill: list[dict[str, Any]] = []
    pwa_rn: list[dict[str, Any]] = []
    missing_guards: list[dict[str, Any]] = []
    for atom in atoms:
        status = str(atom.get("status") or "unknown")
        cls = atom.get("classification") or {}
        guards = atom.get("guards") or {}
        landing = cls.get("target_landing_zone")
        ts = atom_time(atom)
        item = {
            "atom_id": atom.get("atom_id"),
            "title": atom.get("title"),
            "status": status,
            "landing_zone": landing,
            "path": atom.get("_path"),
        }
        if status in {"captured", "normalized", "challenged", "validated", "promoted_candidate"} and ts is not None and ts < stale_cutoff:
            stale.append({**item, "age_days": round((now_ts - ts) / 86400, 1)})
        is_staged = str(atom.get("atom_id") or "").lower() in staged_keys or str(atom.get("title") or "").strip().lower() in staged_keys
        if landing == "skill" and status in {"validated", "promoted_candidate"} and not is_staged:
            actionable_skill.append(item)
        if status in {"validated", "promoted_candidate", "promoted"}:
            if not guards.get("falsifiers") or not guards.get("anti_conditions") or not atom.get("evidence_refs"):
                missing_guards.append({**item, "has_falsifier": bool(guards.get("falsifiers")), "has_anti_conditions": bool(guards.get("anti_conditions")), "has_evidence": bool(atom.get("evidence_refs"))})
        blob = text_blob(atom)
        tags = set(cls.get("domain_tags") or [])
        if tags.intersection(DEFAULT_TAGS) or has_any(blob, PWA_KEYWORDS + RN_KEYWORDS):
            suggested = []
            if has_any(blob, PWA_KEYWORDS):
                suggested.append("mobile-frontend-delivery:references/pwa-cross-end-compatibility.md")
            if has_any(blob, RN_KEYWORDS):
                suggested.append("mobile-frontend-delivery:references/react-native-cross-platform-delivery.md")
            pwa_rn.append({**item, "suggested_targets": suggested or ["mobile-frontend-delivery"]})
    return {
        "by_status": dict(sorted(by_status.items())),
        "by_landing_zone": dict(sorted(by_landing.items())),
        "stale_atoms": stale,
        "actionable_skill_candidates": actionable_skill,
        "pwa_rn_mobile_candidates": pwa_rn,
        "missing_promotion_guards": missing_guards,
    }


def active_watchdog_jobs(cron_jobs_path: Path) -> list[dict[str, Any]]:
    cron = read_json(cron_jobs_path, {"jobs": []})
    jobs = cron.get("jobs", []) if isinstance(cron, dict) else []
    out = []
    for job in jobs:
        if not isinstance(job, dict) or not job.get("enabled", True):
            continue
        hay = " ".join(str(job.get(k) or "") for k in ["name", "script", "prompt"])
        if "experience_ratchet_watchdog" in hay or "experience-ratchet" in hay.lower():
            out.append({
                "id": job.get("id"),
                "name": job.get("name"),
                "script": job.get("script"),
                "schedule": job.get("schedule_display"),
                "last_status": job.get("last_status"),
                "next_run_at": job.get("next_run_at"),
                "no_agent": job.get("no_agent"),
                "deliver": job.get("deliver"),
            })
    return out


def build_watchdog_report(args: argparse.Namespace) -> dict[str, Any]:
    hermes_home = Path(args.hermes_home).expanduser().resolve()
    experience_home = Path(args.experience_home).expanduser().resolve()
    script = hermes_home / "scripts" / "experience-ratchet-maze.py"
    now_ts = time.time()
    atoms = load_atoms(experience_home)
    proposals = list_proposals(experience_home)
    validate = run_validate(script, experience_home, args.timeout_seconds)
    staged_keys = staged_skill_candidate_keys(hermes_home / "evidence" / "skill-evolution-candidates")
    atom_summary = summarize_atoms(atoms, now_ts, args.stale_days, staged_keys)
    watchdog_jobs = active_watchdog_jobs(hermes_home / "cron" / "jobs.json")

    issues: list[dict[str, Any]] = []
    if not experience_home.exists():
        issues.append({"issue_id": "experience_home_missing", "severity": "high", "detail": str(experience_home)})
    if not validate.get("ok"):
        issues.append({"issue_id": "validate_failed", "severity": "high", "detail": validate.get("error") or validate.get("stderr_tail") or "validate returned non-ok"})
    if len(atom_summary["stale_atoms"]) > args.max_stale_atoms:
        issues.append({"issue_id": "stale_atom_backlog", "severity": "medium", "count": len(atom_summary["stale_atoms"]), "threshold": args.max_stale_atoms})
    if len(atom_summary["actionable_skill_candidates"]) > args.max_skill_candidates:
        issues.append({"issue_id": "skill_candidate_backlog", "severity": "medium", "count": len(atom_summary["actionable_skill_candidates"]), "threshold": args.max_skill_candidates})
    if len(atom_summary["missing_promotion_guards"]) > 0:
        issues.append({"issue_id": "promotion_guard_gap", "severity": "medium", "count": len(atom_summary["missing_promotion_guards"])})
    if args.require_cron and not watchdog_jobs:
        issues.append({"issue_id": "watchdog_cron_missing", "severity": "low", "detail": "no enabled cron job references experience_ratchet_watchdog.py"})

    status = "ok" if not issues else "actionable"
    return {
        "schema": SCHEMA,
        "generated_at": utc_now(),
        "status": status,
        "side_effects": "local_read_only",
        "write_policy": "proposal_only_no_direct_mutation",
        "forbidden_side_effects": ["direct_memory_write", "direct_skill_edit", "direct_profile_edit", "direct_taskpool_add", "external_send", "push", "deploy", "delete", "credential_entry"],
        "paths": {
            "hermes_home": str(hermes_home),
            "experience_home": str(experience_home),
            "experience_cli": str(script),
        },
        "validate": {"ok": validate.get("ok"), "checked": validate.get("checked"), "exit_code": validate.get("exit_code"), "error": validate.get("error"), "stderr_tail": validate.get("stderr_tail")},
        "summary": {
            "atoms": len(atoms),
            "proposals": len(proposals),
            "issues": len(issues),
            "watchdog_jobs": len(watchdog_jobs),
            "stale_atoms": len(atom_summary["stale_atoms"]),
            "actionable_skill_candidates": len(atom_summary["actionable_skill_candidates"]),
            "pwa_rn_mobile_candidates": len(atom_summary["pwa_rn_mobile_candidates"]),
            "missing_promotion_guards": len(atom_summary["missing_promotion_guards"]),
        },
        "atoms": atom_summary,
        "watchdog_jobs": watchdog_jobs,
        "issues": issues,
        "next_local_actions": [
            "validate/fix invalid atom JSON before relying on promotion proposals" if any(i["issue_id"] == "validate_failed" for i in issues) else None,
            "stage landing_zone=skill promoted candidates through skill_candidate_staging.py, not direct skill edits" if atom_summary["actionable_skill_candidates"] else None,
            "route PWA/RN/mobile candidates to mobile-frontend-delivery references after guard review" if atom_summary["pwa_rn_mobile_candidates"] else None,
            "add/verify no-agent local cron for experience_ratchet_watchdog.py if long-term monitoring is desired" if not watchdog_jobs else None,
        ],
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Local-only watchdog for Hermes experience-ratchet overlay")
    parser.add_argument("--hermes-home", default=os.path.expanduser("~/.hermes"))
    parser.add_argument("--experience-home", default=os.path.expanduser("~/.hermes/experience-ratchet"))
    parser.add_argument("--timeout-seconds", type=int, default=45)
    parser.add_argument("--stale-days", type=int, default=14)
    parser.add_argument("--max-stale-atoms", type=int, default=0)
    parser.add_argument("--max-skill-candidates", type=int, default=0)
    parser.add_argument("--require-cron", action="store_true", help="Report missing cron coverage as an issue")
    parser.add_argument("--json", action="store_true", help="Always print JSON, even when ok")
    parser.add_argument("--quiet-success", action="store_true", help="Print nothing when status=ok")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = build_watchdog_report(args)
    report["next_local_actions"] = [x for x in report["next_local_actions"] if x]
    if args.json or not (args.quiet_success and report["status"] == "ok"):
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["validate"].get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
