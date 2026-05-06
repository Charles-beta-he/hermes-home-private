#!/usr/bin/env python3
"""brainctl.py — local-first Hermes/Obsidian evidence memory control plane.

Canonical truth source: ~/Documents/brain (or HERMES_BRAIN_VAULT).
Derived state: ~/.hermes/memory/index.sqlite and ~/.hermes/memory/wal.jsonl.

This script deliberately keeps Obsidian CLI optional. Filesystem + SQLite FTS5
must work even when Obsidian is not installed/running.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import time
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Sequence

SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{16,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)\b(api[_-]?key|secret|token|password|passwd)\b\s*[:=]\s*['\"]?[^\s'\"]{8,}"),
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{16,}"),
]

DEFAULT_IGNORES = [
    ".obsidian/**",
    ".git/**",
    "99-hermes-notes/.git/**",
]


@dataclass(frozen=True)
class Paths:
    vault: Path
    memory_home: Path
    index: Path
    wal: Path
    sync_script: Path


@dataclass(frozen=True)
class Block:
    rel_path: str
    heading: str
    line_start: int
    line_end: int
    text: str
    content_hash: str
    excerpt: str


def resolve_paths() -> Paths:
    home = Path.home()
    vault = Path(os.environ.get("HERMES_BRAIN_VAULT", str(home / "Documents" / "brain"))).expanduser()
    memory_home = Path(os.environ.get("HERMES_MEMORY_HOME", str(home / ".hermes" / "memory"))).expanduser()
    index = Path(os.environ.get("HERMES_BRAIN_INDEX", str(memory_home / "index.sqlite"))).expanduser()
    wal = Path(os.environ.get("HERMES_BRAIN_WAL", str(memory_home / "wal.jsonl"))).expanduser()
    sync_script = Path(os.environ.get("HERMES_SYNC_BRAIN_SCRIPT", str(home / ".hermes" / "scripts" / "sync-brain.py"))).expanduser()
    return Paths(vault=vault, memory_home=memory_home, index=index, wal=wal, sync_script=sync_script)


def obsidian_cli() -> str | None:
    return shutil.which("obsidian") or shutil.which("obsidian-cli")


def now_ts() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def has_secret(text: str) -> bool:
    return any(pattern.search(text) for pattern in SECRET_PATTERNS)


def sanitize_value(value):
    if isinstance(value, str):
        redacted = value
        for pattern in SECRET_PATTERNS:
            redacted = pattern.sub("[REDACTED]", redacted)
        return redacted
    if isinstance(value, dict):
        return {str(k): sanitize_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize_value(v) for v in value]
    return value


def ensure_memory(paths: Paths) -> None:
    paths.memory_home.mkdir(parents=True, exist_ok=True)
    paths.index.parent.mkdir(parents=True, exist_ok=True)
    paths.wal.parent.mkdir(parents=True, exist_ok=True)


def append_wal(op: str, details: dict | None = None, *, paths: Paths | None = None) -> dict:
    paths = paths or resolve_paths()
    ensure_memory(paths)
    safe_details = sanitize_value(details or {})
    entry = {"ts": now_ts(), "op": op, "details": safe_details}
    with paths.wal.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
    return entry


def read_ignore_patterns(vault: Path) -> list[str]:
    patterns = list(DEFAULT_IGNORES)
    ignore_file = vault / ".brainignore"
    if ignore_file.exists():
        for raw in ignore_file.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            patterns.append(line)
    return patterns


def ignored(rel_path: str, patterns: Sequence[str]) -> bool:
    rel = rel_path.replace(os.sep, "/")
    for pattern in patterns:
        pat = pattern.strip().replace(os.sep, "/")
        if not pat:
            continue
        if fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch("/" + rel, pat):
            return True
        if pat.endswith("/**") and rel.startswith(pat[:-3].rstrip("/") + "/"):
            return True
    return False


def iter_markdown_files(vault: Path, patterns: Sequence[str]) -> Iterator[Path]:
    if not vault.exists():
        return
    for path in sorted(vault.rglob("*.md")):
        if not path.is_file():
            continue
        try:
            rel = path.relative_to(vault).as_posix()
        except ValueError:
            continue
        if ignored(rel, patterns):
            continue
        yield path


def heading_text(line: str) -> str | None:
    match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
    if not match:
        return None
    return match.group(2).strip()


def make_excerpt(text: str, limit: int = 320) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "…"


def blocks_from_file(path: Path, vault: Path) -> tuple[list[Block], int]:
    rel = path.relative_to(vault).as_posix()
    content = path.read_text(encoding="utf-8", errors="replace")
    lines = content.splitlines()
    current_heading = path.stem
    start_line = 1
    buf: list[str] = []
    blocks: list[Block] = []
    skipped_secret = 0

    def flush(end_line: int) -> None:
        nonlocal buf, start_line, skipped_secret
        text = "\n".join(buf).strip()
        if not text:
            buf = []
            return
        if has_secret(text):
            skipped_secret += 1
            buf = []
            return
        digest = sha256_text(f"{rel}\n{current_heading}\n{start_line}\n{end_line}\n{text}")
        blocks.append(
            Block(
                rel_path=rel,
                heading=current_heading,
                line_start=start_line,
                line_end=max(start_line, end_line),
                text=text,
                content_hash=digest,
                excerpt=make_excerpt(text),
            )
        )
        buf = []

    for idx, line in enumerate(lines, start=1):
        h = heading_text(line)
        if h is not None:
            flush(idx - 1)
            current_heading = h
            start_line = idx
            buf = [line]
        else:
            if not buf:
                start_line = idx
            buf.append(line)
    flush(len(lines))
    return blocks, skipped_secret


def connect_index(paths: Paths | None = None) -> sqlite3.Connection:
    paths = paths or resolve_paths()
    ensure_memory(paths)
    con = sqlite3.connect(paths.index)
    con.row_factory = sqlite3.Row
    return con


def init_schema(con: sqlite3.Connection) -> None:
    con.executescript(
        """
        create table if not exists blocks (
          id integer primary key,
          path text not null,
          heading text not null,
          line_start integer not null,
          line_end integer not null,
          content_hash text not null unique,
          excerpt text not null,
          body text not null,
          mtime real not null
        );
        create virtual table if not exists blocks_fts using fts5(
          path unindexed,
          heading,
          body,
          content='blocks',
          content_rowid='id'
        );
        create table if not exists metadata (
          key text primary key,
          value text not null
        );
        """
    )
    con.commit()


def reset_index(con: sqlite3.Connection) -> None:
    con.executescript(
        """
        drop table if exists blocks_fts;
        drop table if exists blocks;
        drop table if exists metadata;
        """
    )
    con.commit()
    init_schema(con)


def reindex(*, json_mode: bool = False) -> dict:
    paths = resolve_paths()
    ensure_memory(paths)
    patterns = read_ignore_patterns(paths.vault)
    con = connect_index(paths)
    indexed = 0
    skipped_secret = 0
    skipped_ignored = 0
    try:
        reset_index(con)
        for md in iter_markdown_files(paths.vault, patterns):
            rel = md.relative_to(paths.vault).as_posix()
            if ignored(rel, patterns):
                skipped_ignored += 1
                continue
            blocks, skipped = blocks_from_file(md, paths.vault)
            skipped_secret += skipped
            mtime = md.stat().st_mtime
            for block in blocks:
                cur = con.execute(
                    """
                    insert into blocks(path, heading, line_start, line_end, content_hash, excerpt, body, mtime)
                    values (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        block.rel_path,
                        block.heading,
                        block.line_start,
                        block.line_end,
                        block.content_hash,
                        block.excerpt,
                        block.text,
                        mtime,
                    ),
                )
                rowid = cur.lastrowid
                con.execute(
                    "insert into blocks_fts(rowid, path, heading, body) values (?, ?, ?, ?)",
                    (rowid, block.rel_path, block.heading, block.text),
                )
                indexed += 1
        con.execute("insert or replace into metadata(key, value) values('indexed_at', ?)", (now_ts(),))
        con.execute("insert or replace into metadata(key, value) values('vault', ?)", (str(paths.vault),))
        con.commit()
    finally:
        con.close()
    result = {
        "vault": str(paths.vault),
        "index": str(paths.index),
        "indexed_blocks": indexed,
        "skipped_secret_blocks": skipped_secret,
        "skipped_ignored_files": skipped_ignored,
    }
    append_wal(
        "reindex",
        {
            "vault": str(paths.vault),
            "indexed_blocks": indexed,
            "skipped_secret_blocks": skipped_secret,
            "skipped_ignored_files": skipped_ignored,
        },
        paths=paths,
    )
    if not json_mode:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def fts_query(query: str) -> str:
    # Keep FTS syntax conservative. Quote every token so punctuation-heavy
    # queries (for example secrets containing '-') cannot be parsed as column
    # filters or operators by FTS5.
    tokens = re.findall(r"[\w\u4e00-\u9fff]+", query, flags=re.UNICODE)
    if not tokens:
        return '""'
    return " ".join('"' + token.replace('"', '""') + '"' for token in tokens)


def search(query: str, *, limit: int = 10, json_mode: bool = False) -> list[dict]:
    paths = resolve_paths()
    if not paths.index.exists():
        reindex(json_mode=True)
    con = connect_index(paths)
    results: list[dict] = []
    try:
        init_schema(con)
        rows = con.execute(
            """
            select b.path, b.heading, b.line_start, b.line_end, b.content_hash, b.excerpt,
                   bm25(blocks_fts) as rank
            from blocks_fts
            join blocks b on b.id = blocks_fts.rowid
            where blocks_fts match ?
            order by rank
            limit ?
            """,
            (fts_query(query), limit),
        ).fetchall()
        for row in rows:
            results.append(
                {
                    "path": row["path"],
                    "heading": row["heading"],
                    "line_start": int(row["line_start"]),
                    "line_end": int(row["line_end"]),
                    "content_hash": row["content_hash"],
                    "excerpt": row["excerpt"],
                    "score": float(-row["rank"]),
                }
            )
    finally:
        con.close()
    append_wal(
        "search",
        {"query_hash": sha256_text(query), "limit": limit, "result_count": len(results), "query_redacted": has_secret(query)},
        paths=paths,
    )
    if not json_mode:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    return results


def evidence(query: str, *, limit: int = 10, json_mode: bool = False) -> list[dict]:
    return search(query, limit=limit, json_mode=json_mode)


def wal_tail(*, limit: int = 20, json_mode: bool = False) -> list[dict]:
    paths = resolve_paths()
    if not paths.wal.exists():
        entries: list[dict] = []
    else:
        lines = paths.wal.read_text(encoding="utf-8", errors="replace").splitlines()[-limit:]
        entries = []
        for line in lines:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                entries.append({"malformed": True, "line_hash": sha256_text(line)})
    if not json_mode:
        print(json.dumps(entries, ensure_ascii=False, indent=2))
    return entries


def status(*, json_mode: bool = False) -> dict:
    paths = resolve_paths()
    cli = obsidian_cli()
    indexed_at = None
    block_count = 0
    if paths.index.exists():
        try:
            con = connect_index(paths)
            init_schema(con)
            row = con.execute("select value from metadata where key='indexed_at'").fetchone()
            indexed_at = row[0] if row else None
            block_count = con.execute("select count(*) from blocks").fetchone()[0]
            con.close()
        except sqlite3.Error:
            indexed_at = None
    data = {
        "vault": str(paths.vault),
        "vault_exists": paths.vault.exists(),
        "legacy_vault": str(Path.home() / "Documents" / "Obsidian Vault"),
        "index": str(paths.index),
        "index_exists": paths.index.exists(),
        "indexed_at": indexed_at,
        "indexed_blocks": block_count,
        "wal": str(paths.wal),
        "wal_exists": paths.wal.exists(),
        "sync_script": str(paths.sync_script),
        "sync_script_exists": paths.sync_script.exists(),
        "obsidian_cli": cli,
        "obsidian_cli_available": bool(cli),
        "mode": "obsidian_cli_available" if cli else "filesystem_fallback",
    }
    if not json_mode:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    return data


def sync(*, json_mode: bool = False) -> dict:
    paths = resolve_paths()
    if not paths.sync_script.exists():
        result = {"exit_code": 127, "stdout": "", "stderr": f"sync script not found: {paths.sync_script}"}
    else:
        proc = subprocess.run(
            [sys.executable, str(paths.sync_script)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=120,
            check=False,
        )
        result = {"exit_code": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}
    append_wal("sync", {"exit_code": result["exit_code"], "stdout_hash": sha256_text(result["stdout"]), "stderr_hash": sha256_text(result["stderr"])}, paths=paths)
    if not json_mode:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def open_note(path: str, *, json_mode: bool = False, launch: bool = False) -> dict:
    paths = resolve_paths()
    rel = Path(path).as_posix().lstrip("/")
    target = paths.vault / rel
    uri = f"obsidian://open?path={target.as_posix()}"
    cli = obsidian_cli()
    launched = False
    if launch:
        if cli:
            subprocess.run([cli, "open", str(target)], check=False)
            launched = True
        else:
            webbrowser.open(uri)
            launched = True
    result = {"path": str(target), "uri": uri, "obsidian_cli_available": bool(cli), "launched": launched}
    append_wal("open", {"path": rel, "launched": launched}, paths=paths)
    if not json_mode:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Hermes local brain control plane")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="show local brain status")
    sub.add_parser("reindex", help="rebuild SQLite FTS5 evidence index")

    p_search = sub.add_parser("search", help="search evidence index")
    p_search.add_argument("query")
    p_search.add_argument("--limit", type=int, default=10)

    p_evidence = sub.add_parser("evidence", help="search and return evidence objects")
    p_evidence.add_argument("query")
    p_evidence.add_argument("--limit", type=int, default=10)

    p_wal = sub.add_parser("wal", help="show WAL tail")
    p_wal.add_argument("--tail", type=int, default=20)

    sub.add_parser("sync", help="run existing sync-brain.py")

    p_open = sub.add_parser("open", help="print or launch Obsidian URI for a note")
    p_open.add_argument("path")
    p_open.add_argument("--launch", action="store_true")
    return parser


def emit_cli(result, json_mode: bool) -> None:
    if json_mode:
        print(json.dumps(result, ensure_ascii=False, indent=2))


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == "status":
        emit_cli(status(json_mode=True), args.json)
    elif args.cmd == "reindex":
        emit_cli(reindex(json_mode=True), args.json)
    elif args.cmd == "search":
        emit_cli(search(args.query, limit=args.limit, json_mode=True), args.json)
    elif args.cmd == "evidence":
        emit_cli(evidence(args.query, limit=args.limit, json_mode=True), args.json)
    elif args.cmd == "wal":
        emit_cli(wal_tail(limit=args.tail, json_mode=True), args.json)
    elif args.cmd == "sync":
        result = sync(json_mode=True)
        emit_cli(result, args.json)
        return int(result.get("exit_code", 1))
    elif args.cmd == "open":
        emit_cli(open_note(args.path, json_mode=True, launch=args.launch), args.json)
    else:
        raise AssertionError(args.cmd)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
