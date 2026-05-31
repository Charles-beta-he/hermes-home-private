#!/usr/bin/env python3
"""Certify Hermes multi-model autonomy and budget handoff readiness.

This is an explicit, bounded certification run. It spends one tiny call per
configured model, records sanitized quota/budget evidence, and writes a durable
certificate consumed by model-router readiness/P10 gates.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERMES_HOME = Path(os.environ.get("HERMES_HOME", "~/.hermes")).expanduser()
SCRIPT_DIR = Path(__file__).resolve().parent
CERT_PATH = HERMES_HOME / "state" / "multimodel_autonomy_certificate.json"
LOG_PATH = HERMES_HOME / "logs" / "multimodel-autonomy-certification.jsonl"

DEFAULT_PANEL = [
    ("openai-codex", "gpt-5.5", "primary"),
    ("claude-code", "claude-sonnet-4-6", "planner"),
    ("deepseek", "deepseek-v4-pro", "reviewer"),
    ("google-gemini-cli", "gemini-3.1-pro-preview", "planner"),
    ("xiaomi", "mimo-v2.5-pro", "low_cost_observer"),
]

PROBE_PROMPT = "只回复: HERMES_CERT_OK"
SUCCESS_TOKEN = "HERMES_CERT_OK"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def redact(text: Any) -> str:
    text = str(text or "")
    for marker in ("sk-", "Bearer ", "Authorization", "api_key", "token", "secret"):
        if marker.lower() in text.lower():
            return "[REDACTED_SENSITIVE_OUTPUT]"
    return text[-1200:]


def classify_error(text: str) -> str:
    low = (text or "").lower()
    if "429" in low or "rate limit" in low or "too many requests" in low or "out of extra usage" in low:
        return "rate_limit"
    if "401" in low or "unauthorized" in low or "auth" in low or "credential" in low:
        return "auth"
    if "quota" in low or "billing" in low or "insufficient" in low or "balance" in low:
        return "quota_or_billing"
    if "timeout" in low or "timed out" in low:
        return "timeout"
    if not low.strip():
        return "unknown"
    return "provider_error"


def import_model_quota():
    if str(SCRIPT_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPT_DIR))
    import model_quota  # type: ignore

    return model_quota


def record_success_quota(provider: str, model: str) -> dict:
    mq = import_model_quota()
    if provider == "deepseek":
        snap = mq.probe_deepseek_balance(model=model)
        if snap:
            return mq.record_snapshot(snap)
    snap = mq.snapshot_unobservable_success(
        model,
        provider,
        source="subprocess_success_no_quota_headers",
        quota_type="documented_no_quota_header_policy",
        evidence_note="multimodel_autonomy_certify successful minimal probe; provider exposes no safe quota headers through this route",
        confidence=0.49,
    )
    return mq.record_snapshot(snap)


def record_failure_quota(provider: str, model: str, error: str) -> dict:
    mq = import_model_quota()
    snap = mq.snapshot_from_error(model, provider, error)
    return mq.record_snapshot(snap, preserve_higher_confidence=False)


def run_probe(provider: str, model: str, timeout: int) -> dict:
    cmd = [
        "hermes",
        "chat",
        "--provider",
        provider,
        "-m",
        model,
        "-q",
        PROBE_PROMPT,
        "--quiet",
        "--max-turns",
        "1",
        "--ignore-rules",
        "--source",
        "tool",
    ]
    started = time.time()
    try:
        proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        latency_ms = int((time.time() - started) * 1000)
        output = (proc.stdout or "") + "\n" + (proc.stderr or "")
        ok = proc.returncode == 0 and SUCCESS_TOKEN in output
        probe = {
            "provider": provider,
            "model": model,
            "ok": ok,
            "returncode": proc.returncode,
            "latency_ms": latency_ms,
            "stdout_tail": redact(proc.stdout),
            "stderr_tail": redact(proc.stderr),
            "error_class": "" if ok else classify_error(output),
        }
    except subprocess.TimeoutExpired as exc:
        probe = {
            "provider": provider,
            "model": model,
            "ok": False,
            "returncode": None,
            "latency_ms": int((time.time() - started) * 1000),
            "stdout_tail": redact(getattr(exc, "stdout", "")),
            "stderr_tail": redact(getattr(exc, "stderr", "")),
            "error_class": "timeout",
        }
    except Exception as exc:  # fail-soft; certificate will fail closed
        probe = {
            "provider": provider,
            "model": model,
            "ok": False,
            "returncode": None,
            "latency_ms": int((time.time() - started) * 1000),
            "stdout_tail": "",
            "stderr_tail": redact(repr(exc)),
            "error_class": classify_error(repr(exc)),
        }
    try:
        failure_error = str(probe.get("stderr_tail") or probe.get("stdout_tail") or probe.get("error_class") or "unknown")
        probe["quota_snapshot"] = record_success_quota(provider, model) if probe["ok"] else record_failure_quota(provider, model, failure_error)
    except Exception as exc:
        probe["quota_record_error"] = type(exc).__name__
    return probe


def parse_panel(values: list[str]) -> list[tuple[str, str, str]]:
    if not values:
        return DEFAULT_PANEL
    panel = []
    for raw in values:
        parts = raw.split(":")
        if len(parts) < 2:
            raise SystemExit(f"invalid --model entry {raw!r}; expected provider:model[:role]")
        provider, model = parts[0], parts[1]
        role = parts[2] if len(parts) > 2 else "participant"
        panel.append((provider, model, role))
    return panel


def build_certificate(panel: list[tuple[str, str, str]], timeout: int, min_providers: int, require_primary: bool, dry_run: bool = False) -> dict:
    probes = []
    for provider, model, role in panel:
        if dry_run:
            probes.append({"provider": provider, "model": model, "role": role, "ok": True, "returncode": 0, "latency_ms": 0, "error_class": "", "dry_run": True})
        else:
            probe = run_probe(provider, model, timeout=timeout)
            probe["role"] = role
            probes.append(probe)
    passed = [p for p in probes if p.get("ok")]
    failed = [p for p in probes if not p.get("ok")]
    provider_passes = sorted({p.get("provider") for p in passed if p.get("provider")})
    primary_ok = any(p.get("ok") and p.get("role") == "primary" for p in probes)
    hard_failures = []
    if len(provider_passes) < min_providers:
        hard_failures.append("insufficient_distinct_provider_passes")
    if require_primary and not primary_ok:
        hard_failures.append("primary_model_probe_failed")
    status = "PASS" if not hard_failures else "FAIL_CLOSED"
    cert = {
        "schema_version": 1,
        "generated_at": now_iso(),
        "status": status,
        "ok": status == "PASS",
        "panel": [{"provider": p, "model": m, "role": r} for p, m, r in panel],
        "required_min_providers": min_providers,
        "require_primary": require_primary,
        "pass_count": len(passed),
        "failure_count": len(failed),
        "provider_pass_count": len(provider_passes),
        "provider_passes": provider_passes,
        "hard_failures": hard_failures,
        "probes": probes,
        "budget_handoff": {
            "status": status,
            "packet_required_on_failure": True,
            "route_mutation_allowed": False,
            "auto_purchase_quota": False,
            "evidence": "fresh minimal real-call probes plus sanitized quota snapshots",
        },
        "autonomy": {
            "can_certify_autonomy": status == "PASS",
            "can_promote_budget_handoff": status == "PASS",
            "automatic_rebalance_performed": False,
            "policy": "certificate proves available provider diversity for autonomy; it does not change active routes by itself",
        },
    }
    return cert


def write_certificate(cert: dict, path: Path = CERT_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(cert, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    tmp.replace(path)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": now_iso(), "event": "certificate", "status": cert.get("status"), "provider_passes": cert.get("provider_passes"), "hard_failures": cert.get("hard_failures")}, ensure_ascii=False, sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Certify multi-model autonomy and budget handoff readiness")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--gate", action="store_true", help="Exit non-zero if certificate is not PASS")
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--min-providers", type=int, default=3)
    parser.add_argument("--no-require-primary", action="store_true")
    parser.add_argument("--model", action="append", default=[], help="provider:model[:role]; repeat to override default panel")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    panel = parse_panel(args.model)
    cert = build_certificate(panel, timeout=args.timeout, min_providers=args.min_providers, require_primary=not args.no_require_primary, dry_run=args.dry_run)
    if not args.dry_run:
        write_certificate(cert)
    if args.json:
        print(json.dumps(cert, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print(f"multimodel_autonomy_certificate: {cert['status']} providers={cert['provider_pass_count']} passes={cert['pass_count']} failures={cert['failure_count']}")
        for p in cert["probes"]:
            mark = "✓" if p.get("ok") else "✗"
            print(f"  {mark} {p.get('provider')}::{p.get('model')} role={p.get('role')} latency={p.get('latency_ms')}ms error={p.get('error_class') or '-'}")
        print(f"certificate: {CERT_PATH}")
    return 0 if cert.get("ok") or not args.gate else 2


if __name__ == "__main__":
    raise SystemExit(main())
