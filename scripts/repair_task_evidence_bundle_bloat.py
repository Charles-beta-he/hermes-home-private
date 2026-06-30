#!/usr/bin/env python3
"""Repair task markdown frontmatter YAML escape explosions.

Moves original bloated files to an evidence quarantine directory, then rewrites a
sanitized copy at the original task path. The rewrite is streaming-safe for
multi-GB single-line frontmatter fields.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import shutil
from pathlib import Path

TASK_DIR = Path(os.path.expanduser('~/Documents/brain/05-实践与项目/tasks'))
EVIDENCE_DIR = Path(os.path.expanduser('~/taskpool-bloat-quarantine')) / dt.datetime.now().strftime('%Y%m%d-%H%M%S')
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

MAX_SIZE = 100 * 1024
MAX_BACKSLASHES_HEAD = 1000
FIELD_REPLACEMENTS = {
    b'evidence_bundle:': (
        b'evidence_bundle:\n'
        b'  - "proof:evidence_bundle_sanitized_due_yaml_escape_bloat; '
        b'original preserved in ~/taskpool-bloat-quarantine manifest"\n'
    ),
    b'dependency_order:': b'dependency_order: []\n',
    b'parallel_group:': b'parallel_group: ""\n',
    b'conflict_group:': b'conflict_group: ""\n',
    b'workspace_isolation:': b'workspace_isolation: ""\n',
}


def head_backslashes(path: Path, limit: int = 200_000) -> int:
    with path.open('rb') as f:
        data = f.read(limit)
    # only count likely frontmatter/head escape explosion; cheap and bounded
    return data.count(b'\\')


def has_evidence_bundle_head(path: Path, limit: int = 200_000) -> bool:
    with path.open('rb') as f:
        head = f.read(limit)
    return any(prefix in head for prefix in FIELD_REPLACEMENTS)


def candidate(path: Path) -> bool:
    try:
        size = path.stat().st_size
        bs = head_backslashes(path)
        return has_evidence_bundle_head(path) and (size > MAX_SIZE or bs > MAX_BACKSLASHES_HEAD)
    except OSError:
        return False


def sanitize_from_quarantine(src: Path, dst: Path) -> dict:
    tmp = dst.with_suffix(dst.suffix + '.repair-tmp')
    replaced_fields: list[str] = []
    skipped_bytes = 0
    line_start = True
    skipping = False
    with src.open('rb') as fin, tmp.open('wb') as fout:
        while True:
            chunk = fin.read(1024 * 1024)
            if not chunk:
                break
            i = 0
            n = len(chunk)
            while i < n:
                b = chunk[i:i+1]
                if skipping:
                    skipped_bytes += 1
                    if b == b'\n':
                        skipping = False
                        line_start = True
                    i += 1
                    continue

                if line_start:
                    hit = None
                    for prefix in FIELD_REPLACEMENTS:
                        if chunk[i:].startswith(prefix):
                            hit = prefix
                            break
                    if hit is not None:
                        fout.write(FIELD_REPLACEMENTS[hit])
                        replaced_fields.append(hit.decode('utf-8').rstrip(':'))
                        skipping = True
                        i += len(hit)
                        continue

                fout.write(b)
                line_start = (b == b'\n')
                i += 1
    if not replaced_fields:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f'No bloat-prone frontmatter field replaced in {src}')
    os.replace(tmp, dst)
    return {'replaced_fields': sorted(set(replaced_fields)), 'skipped_bytes': skipped_bytes, 'new_size': dst.stat().st_size}


def main() -> int:
    manifest = {
        'created_at': dt.datetime.now().isoformat(timespec='seconds'),
        'task_dir': str(TASK_DIR),
        'evidence_dir': str(EVIDENCE_DIR),
        'thresholds': {'size_bytes': MAX_SIZE, 'head_backslashes': MAX_BACKSLASHES_HEAD},
        'repaired': [],
        'skipped': [],
    }
    paths = sorted(TASK_DIR.glob('*.md'), key=lambda p: p.stat().st_size, reverse=True)
    for path in paths:
        size_before = path.stat().st_size
        bs_before = head_backslashes(path)
        if not (has_evidence_bundle_head(path) and (size_before > MAX_SIZE or bs_before > MAX_BACKSLASHES_HEAD)):
            continue
        qname = f'{path.name}.original'
        qpath = EVIDENCE_DIR / qname
        if qpath.exists():
            raise RuntimeError(f'quarantine exists: {qpath}')
        shutil.move(str(path), str(qpath))
        result = sanitize_from_quarantine(qpath, path)
        record = {
            'file': path.name,
            'path': str(path),
            'quarantine_original': str(qpath),
            'size_before': size_before,
            'head_backslashes_before': bs_before,
            **result,
        }
        manifest['repaired'].append(record)
        print(json.dumps(record, ensure_ascii=False))
    manifest_path = EVIDENCE_DIR / 'manifest.json'
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'manifest': str(manifest_path), 'repaired_count': len(manifest['repaired'])}, ensure_ascii=False))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
