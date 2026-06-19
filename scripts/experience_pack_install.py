#!/usr/bin/env python3
"""Install sanitized Hermes experience packs with safe, ready-to-use defaults.

The installer is intentionally more automatic than the inventory scanner: given a
clean pack, it copies missing templates/skills/scripts into a target HERMES_HOME,
creates an installed manifest, and keeps every side-effectful capability disabled
until the new user explicitly activates it.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

PACKS_ROOT = Path.home() / ".hermes" / "templates" / "experience-pack"
SANITIZER = Path.home() / ".hermes" / "scripts" / "experience_pack_sanitize.py"

COPY_DIRS = ("templates", "skills", "scripts", "examples")
NEVER_OVERWRITE = True


@dataclass
class Operation:
    action: str
    source: str
    destination: str
    reason: str = ""


@dataclass
class InstallResult:
    ok: bool
    pack: str
    pack_root: str
    target_home: str
    dry_run: bool
    operations: list[Operation]
    blocked: list[str]


def pack_root(name_or_path: str) -> Path:
    p = Path(name_or_path).expanduser()
    if p.exists():
        return p.resolve()
    return (PACKS_ROOT / name_or_path).resolve()


def list_packs(root: Path = PACKS_ROOT) -> list[dict]:
    if not root.exists():
        return []
    packs = []
    for child in sorted(root.iterdir()):
        if child.is_dir() and (child / "manifest.yaml").exists():
            packs.append({"name": child.name, "path": str(child), "manifest": str(child / "manifest.yaml")})
    return packs


def run_sanitizer(root: Path) -> tuple[bool, str]:
    if not SANITIZER.exists():
        return False, f"sanitizer not found: {SANITIZER}"
    proc = subprocess.run([sys.executable, str(SANITIZER), str(root), "--json"], text=True, capture_output=True)
    if proc.returncode != 0:
        return False, proc.stdout or proc.stderr
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return False, proc.stdout or proc.stderr
    if not payload.get("ok"):
        return False, json.dumps(payload, ensure_ascii=False, indent=2)
    return True, proc.stdout


def iter_payload_files(root: Path) -> Iterable[Path]:
    for rel_dir in COPY_DIRS:
        base = root / rel_dir
        if not base.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in {".git", "__pycache__", "node_modules"}]
            for name in filenames:
                yield Path(dirpath) / name
    for name in ("README.md", "manifest.yaml"):
        p = root / name
        if p.exists():
            yield p


def destination_for(root: Path, target_home: Path, source: Path) -> Path:
    rel = source.relative_to(root)
    if rel.parts and rel.parts[0] in {"README.md", "manifest.yaml"}:
        return target_home / "experience-packs" / root.name / rel
    # Preserve pack namespace to avoid polluting user templates/skills with a
    # raw owner layout. Activation/import can be layered later from this SSOT.
    return target_home / "experience-packs" / root.name / rel


def ensure_runtime_skeleton(target_home: Path, ops: list[Operation], dry_run: bool) -> None:
    for rel in ["experience-packs", "state", "logs", "locks"]:
        dest = target_home / rel
        ops.append(Operation("mkdir" if not dest.exists() else "exists", "", str(dest), "runtime skeleton"))
        if not dry_run:
            dest.mkdir(parents=True, exist_ok=True)
    activation = target_home / "state" / "experience-pack-activation.json"
    if not activation.exists():
        ops.append(Operation("write", "", str(activation), "all side-effectful modules disabled by default"))
        if not dry_run:
            activation.write_text(json.dumps({"schema":"hermes_experience_pack_activation_v1","enabled_modules":{},"cron_enabled":False,"hooks_enabled":False,"gateway_delivery_enabled":False,"taskpool_mutation_enabled":False}, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    else:
        ops.append(Operation("exists", "", str(activation), "preserve existing activation state"))


def install(name_or_path: str, target_home: Path, dry_run: bool = False, force: bool = False) -> InstallResult:
    root = pack_root(name_or_path)
    target_home = target_home.expanduser().resolve()
    blocked: list[str] = []
    operations: list[Operation] = []
    if not root.exists() or not root.is_dir():
        return InstallResult(False, name_or_path, str(root), str(target_home), dry_run, operations, [f"pack not found: {root}"])
    ok, detail = run_sanitizer(root)
    if not ok:
        return InstallResult(False, root.name, str(root), str(target_home), dry_run, operations, ["sanitizer failed", detail])

    ensure_runtime_skeleton(target_home, operations, dry_run)
    for src in iter_payload_files(root):
        dst = destination_for(root, target_home, src)
        if dst.exists() and not force:
            operations.append(Operation("skip", str(src), str(dst), "exists; no overwrite"))
            continue
        operations.append(Operation("copy" if not dst.exists() else "overwrite", str(src), str(dst), "sanitized pack payload"))
        if not dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    receipt = target_home / "state" / "experience-pack-install-receipts.jsonl"
    operations.append(Operation("append" if receipt.exists() else "write", "", str(receipt), "install receipt"))
    if not dry_run:
        receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt.write_text("", encoding="utf-8") if not receipt.exists() else None
        with receipt.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"pack": root.name, "pack_root": str(root), "operation_count": len(operations), "force": force}, ensure_ascii=False)+"\n")
    return InstallResult(True, root.name, str(root), str(target_home), dry_run, operations, blocked)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Hermes experience-pack installer")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    doctor_p = sub.add_parser("doctor")
    doctor_p.add_argument("pack")
    install_p = sub.add_parser("install")
    install_p.add_argument("pack")
    install_p.add_argument("--target-home", default=str(Path.home() / ".hermes"))
    install_p.add_argument("--dry-run", action="store_true")
    install_p.add_argument("--force", action="store_true")
    install_p.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if args.cmd == "list":
        print(json.dumps({"packs": list_packs()}, ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "doctor":
        root = pack_root(args.pack)
        ok, detail = run_sanitizer(root)
        print(detail if detail.strip().startswith("{") else json.dumps({"ok": ok, "detail": detail}, ensure_ascii=False, indent=2))
        return 0 if ok else 2
    if args.cmd == "install":
        result = install(args.pack, Path(args.target_home), dry_run=args.dry_run, force=args.force)
        payload = asdict(result)
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(("DRY-RUN " if result.dry_run else "") + ("PASS" if result.ok else "FAIL") + f": pack={result.pack} ops={len(result.operations)} blocked={len(result.blocked)}")
            for op in result.operations[:80]:
                print(f"- {op.action} {op.destination} {op.reason}")
            if len(result.operations) > 80:
                print(f"... {len(result.operations)-80} more operations")
            for b in result.blocked:
                print(f"BLOCKED: {b}")
        return 0 if result.ok else 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
