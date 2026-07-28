#!/usr/bin/env python3
"""Zero-data-access readiness doctor for the guarded WeChat export skill."""

from __future__ import annotations

import argparse
import json
import plistlib
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, Optional

APP_PATH = Path("/Applications/WeChat.app")
INFO_PLIST = APP_PATH / "Contents" / "Info.plist"
KNOWN_UNSUPPORTED = {
    "4.1.11": "pinned reviewed extractor reports automatic key extraction not working",
}
SOURCE_STATE = {
    "orchestration_recipe": "pinned_and_reviewed",
    "query_server": "pinned_and_reviewed",
    "bulk_export_dependency": "unavailable_at_review_time",
}


def _read_app_version() -> Optional[str]:
    try:
        with INFO_PLIST.open("rb") as handle:
            value = plistlib.load(handle).get("CFBundleShortVersionString")
        return value if type(value) is str and value else None
    except (OSError, plistlib.InvalidFileException):
        return None


def build_report(
    *,
    app_present: bool,
    app_version: Optional[str],
    sqlcipher_path: Optional[str],
    brew_path: Optional[str],
    python_version: str,
) -> Dict[str, Any]:
    blockers = []
    if not app_present:
        blockers.append("wechat_app_absent")
    elif not app_version:
        blockers.append("wechat_version_unreadable")
    elif app_version in KNOWN_UNSUPPORTED:
        blockers.append("exact_version_key_extraction_unsupported")
    else:
        blockers.append("exact_version_compatibility_unverified")
    if not sqlcipher_path:
        blockers.append("sqlcipher_absent")
    if SOURCE_STATE["bulk_export_dependency"] != "pinned_and_reviewed":
        blockers.append("bulk_export_implementation_unavailable")

    return {
        "schema": "hermes.wechat_local_export.doctor.v1",
        "mode": "doctor",
        "app": {
            "present": app_present,
            "version": app_version,
            "known_unsupported_reason": KNOWN_UNSUPPORTED.get(app_version or ""),
        },
        "tools": {
            "brew": brew_path,
            "sqlcipher": sqlcipher_path,
            "python": python_version,
        },
        "source_state": dict(SOURCE_STATE),
        "ready_for_export": False,
        "doctor_available": True,
        "blockers": blockers,
        "data_access_attempted": False,
        "process_memory_access_attempted": False,
        "app_signature_modified": False,
        "mcp_registration_attempted": False,
        "network_access_attempted": False,
        "writes_attempted": False,
        "next_gate": "review_supported_pinned_implementation",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit compact JSON")
    args = parser.parse_args()
    report = build_report(
        app_present=APP_PATH.is_dir(),
        app_version=_read_app_version(),
        sqlcipher_path=shutil.which("sqlcipher"),
        brew_path=shutil.which("brew"),
        python_version=sys.version.split()[0],
    )
    if args.json:
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
