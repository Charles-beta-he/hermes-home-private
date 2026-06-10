#!/usr/bin/env python3
"""
Hermes Social Distribution Adapter — local dry-run layer.

Reads a platform-neutral PublishPackage JSON, maps it to per-platform payloads,
checks adapter availability, and emits an evidence JSON bundle.

Red lines:
- `mode=publish` is REJECTED without a human_approval_token.
- AGPL/GPL adapters (MatrixMedia, Postiz) are invoked via external CLI boundaries only.
- No passwords, cookies, or account secrets are entered by this script.
- Missing binaries → status=unknown_binary_missing, not faked success.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ── constants ──────────────────────────────────────────────────────────
PLATFORM_MAP: Dict[str, Dict[str, Optional[str]]] = {
    "dy":   {"name": "抖音",    "matrixmedia": "dy",   "postiz": "tiktok"},
    "tt":   {"name": "头条",    "matrixmedia": "tt",   "postiz": None},
    "ks":   {"name": "快手",    "matrixmedia": "ks",   "postiz": None},
    "blbl": {"name": "B站",     "matrixmedia": "blbl", "postiz": "youtube"},
    "bjh":  {"name": "百家号",  "matrixmedia": "bjh",  "postiz": None},
    "sph":  {"name": "视频号",  "matrixmedia": "sph",  "postiz": None},
    "xhs":  {"name": "小红书",  "matrixmedia": "xhs",  "postiz": None},
    "x":    {"name": "X/Twitter", "matrixmedia": None, "postiz": "x"},
    "linkedin": {"name": "LinkedIn", "matrixmedia": None, "postiz": "linkedin"},
    "youtube":  {"name": "YouTube",  "matrixmedia": None, "postiz": "youtube"},
    "instagram":{"name": "Instagram","matrixmedia": None, "postiz": "instagram"},
    "facebook": {"name": "Facebook", "matrixmedia": None, "postiz": "facebook"},
    "reddit":   {"name": "Reddit",   "matrixmedia": None, "postiz": "reddit"},
    "tiktok":   {"name": "TikTok",   "matrixmedia": None, "postiz": "tiktok"},
}

MATRIXMEDIA_CLI = "matrixmedia"
POSTIZ_CLI = "postiz"

# Local checkout fallbacks when global CLI not installed
MATRIXMEDIA_REPO = Path(
    os.path.expanduser(
        "~/.hermes/runs/social-distribution-oss-verify-2026-06-10/hanliang97__MatrixMedia"
    )
)
POSTIZ_AGENT_REPO = Path(
    os.path.expanduser(
        "~/.hermes/runs/social-distribution-oss-verify-2026-06-10/gitroomhq__postiz-agent"
    )
)

# ── data structures ────────────────────────────────────────────────────

@dataclass
class AdapterStatus:
    available: bool = False
    binary: str = ""
    version: str = ""
    login_status: str = "unknown"  # logged_in | logged_out | unknown_binary_missing
    accounts: List[Dict[str, str]] = field(default_factory=list)

@dataclass
class PlatformPreview:
    platform: str
    platform_name: str
    adapter: str  # "matrixmedia" | "postiz" | "none"
    command_preview: str = ""
    mapped_payload: Dict[str, Any] = field(default_factory=dict)
    will_publish: bool = False
    warnings: List[str] = field(default_factory=list)
    available: bool = False

@dataclass
class Evidence:
    generated_at: str = ""
    package_path: str = ""
    package_valid: bool = False
    package_errors: List[str] = field(default_factory=list)
    mode: str = "dry-run"  # dry-run | draft | publish
    human_approval_token_provided: bool = False
    matrixmedia: AdapterStatus = field(default_factory=AdapterStatus)
    postiz: AdapterStatus = field(default_factory=AdapterStatus)
    platform_previews: List[PlatformPreview] = field(default_factory=list)
    red_lines_held: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

# ── package validation ─────────────────────────────────────────────────

def load_package(path: str) -> Tuple[Optional[Dict], List[str]]:
    """Load and validate a publish package JSON."""
    errors: List[str] = []
    try:
        with open(path) as f:
            pkg = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        return None, [f"load_failed: {e}"]

    if not isinstance(pkg, dict):
        return None, ["not_a_dict"]

    # required fields
    if not pkg.get("title"):
        errors.append("missing_required: title")
    if not pkg.get("media") or not isinstance(pkg["media"], list) or len(pkg["media"]) == 0:
        errors.append("missing_required: media (non-empty array)")

    # media validation
    for i, m in enumerate(pkg.get("media", [])):
        if not isinstance(m, dict):
            errors.append(f"media[{i}]: not_an_object")
            continue
        if m.get("type") not in ("image", "video"):
            errors.append(f"media[{i}]: invalid_type={m.get('type')}")
        mp = Path(m.get("path", ""))
        if not mp.exists():
            errors.append(f"media[{i}]: path_not_found={mp}")

    # tags
    tags = pkg.get("tags", [])
    if not isinstance(tags, list):
        errors.append("tags: must_be_array")

    return pkg if not errors else pkg, errors

# ── adapter detection ──────────────────────────────────────────────────

def check_adapter(name: str, binary: str, repo: Optional[Path] = None) -> AdapterStatus:
    """Check if an external CLI adapter is available."""
    status = AdapterStatus(binary=binary)

    which_path = shutil.which(binary)
    if which_path:
        status.available = True
        try:
            r = subprocess.run(
                [binary, "--version"], capture_output=True, text=True, timeout=10
            )
            status.version = (r.stdout or r.stderr).strip().split("\n")[0][:200]
        except Exception:
            status.version = "version_check_failed"
        return status

    # Try repo-local fallback
    if repo and repo.exists():
        pkg_json = repo / "package.json"
        if pkg_json.exists():
            try:
                pkg_info = json.loads(pkg_json.read_text())
                status.version = pkg_info.get("version", "unknown")
            except Exception:
                pass
        status.available = True  # repo exists, could be invoked via npx / node
        return status

    status.login_status = "unknown_binary_missing"
    return status

def _probe_matrixmedia_accounts() -> List[Dict[str, str]]:
    """Probe MatrixMedia accounts via CLI."""
    try:
        r = subprocess.run(
            [MATRIXMEDIA_CLI, "cli", "accounts"],
            capture_output=True, text=True, timeout=30,
        )
        if r.returncode == 0:
            # Best-effort parse; actual format is CLI-dependent
            return [{"raw": r.stdout[:2000]}]
    except Exception:
        pass
    return []

def _probe_postiz_auth() -> str:
    """Probe Postiz auth status."""
    try:
        r = subprocess.run(
            [POSTIZ_CLI, "auth:status"], capture_output=True, text=True, timeout=30
        )
        if r.returncode == 0 and "not authenticated" not in (r.stdout + r.stderr).lower():
            return "logged_in"
    except Exception:
        pass
    return "unknown_binary_missing"

# ── platform mapping ───────────────────────────────────────────────────

def map_payload(
    pkg: Dict, platform: str, adapter: str
) -> Tuple[Dict[str, Any], List[str]]:
    """Map platform-neutral package to per-platform payload."""
    warnings: List[str] = []
    overrides = (pkg.get("platformOverrides") or {}).get(platform, {}) or {}

    title = overrides.get("title") or pkg["title"]
    body = overrides.get("body") or pkg.get("body", "")
    tags = overrides.get("tags") or pkg.get("tags", [])

    # Platform-specific field limits
    limits = {
        "xhs": {"title": 20, "body": 1000},
        "dy": {"title": 55, "body": 5000},
        "x": {"body": 280},
        "linkedin": {"body": 3000},
    }

    lim = limits.get(platform, {})
    if lim.get("title") and len(title) > lim["title"]:
        warnings.append(f"title truncated: {len(title)}>{lim['title']}")
        title = title[: lim["title"]]
    if lim.get("body") and len(body) > lim["body"]:
        warnings.append(f"body truncated: {len(body)}>{lim['body']}")
        body = body[: lim["body"]]

    payload: Dict[str, Any] = {
        "title": title,
        "body": body,
        "tags": tags,
        "media": [
            {"type": m["type"], "path": m["path"]} for m in pkg.get("media", [])
        ],
    }
    if pkg.get("scheduleAt"):
        payload["schedule_at"] = pkg["scheduleAt"]

    return payload, warnings

def build_command_preview(
    payload: Dict, platform: str, adapter: str, pkg: Dict
) -> str:
    """Generate a human-readable CLI command preview (dry-run only)."""
    if adapter == "matrixmedia":
        mm_platform = PLATFORM_MAP.get(platform, {}).get("matrixmedia")
        if not mm_platform:
            return f"# MatrixMedia: platform '{platform}' not supported"
        media_paths = [m["path"] for m in payload.get("media", [])]
        title = payload["title"]
        tags = " ".join(f"#{t}" for t in payload.get("tags", []))
        cmd = (
            f"matrixmedia cli publish "
            f"-p {mm_platform} "
        )
        if media_paths:
            cmd += f'-f "{media_paths[0]}" '
        cmd += f'-t "{title}" '
        if tags:
            cmd += f'--tags "{tags}" '
        schedule = pkg.get("scheduleAt")
        if schedule:
            cmd += f'--publish-at "{schedule}" '
        cmd += "# DRY-RUN ONLY — will_publish=false"
        return cmd

    elif adapter == "postiz":
        pz_platform = PLATFORM_MAP.get(platform, {}).get("postiz")
        if not pz_platform:
            return f"# Postiz: platform '{platform}' not supported"
        cmd = (
            f"postiz posts:create "
            f'--title "{payload["title"]}" '
            f'--platforms {pz_platform} '
        )
        if payload.get("body"):
            cmd += f'--content "{payload["body"][:200]}" '
        cmd += "# DRY-RUN ONLY — requires Postiz instance + auth"
        return cmd

    return f"# No adapter available for platform '{platform}'"

# ── main logic ─────────────────────────────────────────────────────────

def run(
    package_path: str,
    mode: str = "dry-run",
    human_approval_token: Optional[str] = None,
    target_platforms: Optional[List[str]] = None,
    out: Optional[str] = None,
) -> Evidence:
    evidence = Evidence(
        generated_at=datetime.now(timezone.utc).isoformat(),
        package_path=os.path.abspath(package_path),
        mode=mode,
        human_approval_token_provided=bool(human_approval_token),
    )

    # ── red line: publish mode gate ──
    if mode == "publish":
        if not human_approval_token:
            evidence.errors.append(
                "RED_LINE: mode=publish rejected — human_approval_token required"
            )
            evidence.red_lines_held.append("publish_without_approval_token")
            _emit(evidence, out)
            return evidence
        evidence.red_lines_held.append("publish_approved_with_token")

    # ── load & validate package ──
    pkg, errors = load_package(package_path)
    if errors:
        evidence.package_errors = errors
        evidence.errors.append("package_validation_failed")
        _emit(evidence, out)
        return evidence
    evidence.package_valid = True
    evidence.red_lines_held.append("package_validated")

    # ── adapter discovery ──
    evidence.matrixmedia = check_adapter(
        "MatrixMedia", MATRIXMEDIA_CLI, MATRIXMEDIA_REPO
    )
    evidence.postiz = check_adapter("Postiz", POSTIZ_CLI, POSTIZ_AGENT_REPO)

    if evidence.matrixmedia.available:
        evidence.matrixmedia.accounts = _probe_matrixmedia_accounts()
        evidence.matrixmedia.login_status = (
            "logged_in" if evidence.matrixmedia.accounts else "unknown"
        )
    if evidence.postiz.available:
        evidence.postiz.login_status = _probe_postiz_auth()

    # ── platform mapping ──
    platforms_to_preview = target_platforms or list(PLATFORM_MAP.keys())
    for platform in platforms_to_preview:
        pinfo = PLATFORM_MAP.get(platform)
        if not pinfo:
            continue
        pname: str = pinfo.get("name", platform)

        # Pick best adapter: prefer MatrixMedia for Chinese platforms, Postiz for international
        adapter = "none"
        if pinfo.get("matrixmedia"):
            adapter = "matrixmedia"
        elif pinfo.get("postiz"):
            adapter = "postiz"

        mapped, map_warnings = map_payload(pkg, platform, adapter)
        cmd_preview = build_command_preview(mapped, platform, adapter, pkg)

        preview = PlatformPreview(
            platform=platform,
            platform_name=pname,
            adapter=adapter,
            command_preview=cmd_preview,
            mapped_payload=mapped,
            will_publish=(mode == "publish" and bool(human_approval_token)),
            warnings=map_warnings,
            available=(
                (adapter == "matrixmedia" and evidence.matrixmedia.available)
                or (adapter == "postiz" and evidence.postiz.available)
            ),
        )
        evidence.platform_previews.append(preview)

    evidence.red_lines_held.append("cli_boundary_preserved")
    evidence.red_lines_held.append("no_credentials_entered")
    evidence.red_lines_held.append(f"will_publish={'true' if mode=='publish' and human_approval_token else 'false'}")

    _emit(evidence, out)
    return evidence


def _emit(evidence: Evidence, out: Optional[str]) -> None:
    """Write evidence JSON to file or stdout."""
    result = asdict(evidence)
    if out:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"Evidence → {out}")
    else:
        json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
        print()


# ── CLI ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Hermes Social Distribution Adapter — dry-run layer"
    )
    parser.add_argument(
        "package", help="Path to publish-package.json"
    )
    parser.add_argument(
        "--mode", default="dry-run",
        choices=["dry-run", "draft", "publish"],
        help="Execution mode (default: dry-run)"
    )
    parser.add_argument(
        "--human-approval-token", default=None,
        help="Required for mode=publish"
    )
    parser.add_argument(
        "--platforms", default=None,
        help="Comma-separated platform list (default: all known)"
    )
    parser.add_argument(
        "--out", default=None,
        help="Output evidence JSON path (default: stdout)"
    )
    args = parser.parse_args()

    target = None
    if args.platforms:
        target = [p.strip() for p in args.platforms.split(",") if p.strip()]

    run(
        package_path=args.package,
        mode=args.mode,
        human_approval_token=args.human_approval_token,
        target_platforms=target,
        out=args.out,
    )


if __name__ == "__main__":
    main()
