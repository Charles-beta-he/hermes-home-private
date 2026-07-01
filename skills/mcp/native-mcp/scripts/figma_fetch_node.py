#!/usr/bin/env python3
"""Fetch a Figma file or node from a copied Figma link without printing secrets.

Usage:
  set -a && source ~/.hermes/secrets/figma-mcp.env && set +a
  python3 figma_fetch_node.py 'https://www.figma.com/design/<FILE_KEY>/...?node-id=1-2' --out ./raw

Auth env:
  FIGMA_API_KEY      Personal access token, sent as X-Figma-Token
  FIGMA_OAUTH_TOKEN  OAuth bearer token, sent as Authorization: Bearer ***
"""
from __future__ import annotations

import argparse
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def parse_figma_link(link: str) -> tuple[str, str | None]:
    parsed = urllib.parse.urlparse(link)
    parts = [p for p in parsed.path.split('/') if p]
    file_key = None
    for marker in ('design', 'file'):
        if marker in parts:
            idx = parts.index(marker)
            if idx + 1 < len(parts):
                file_key = parts[idx + 1]
                break
    if not file_key:
        m = re.search(r'figma\.com/(?:design|file)/([^/?#]+)', link)
        if m:
            file_key = m.group(1)
    if not file_key:
        raise SystemExit('Could not parse Figma file key from link')

    query = urllib.parse.parse_qs(parsed.query)
    node_id = query.get('node-id', [None])[0]
    if node_id:
        node_id = node_id.replace('-', ':')
    return file_key, node_id


def request_json(url: str) -> dict:
    api_key = os.environ.get('FIGMA_API_KEY')
    oauth = os.environ.get('FIGMA_OAUTH_TOKEN')
    if not api_key and not oauth:
        raise SystemExit('Missing FIGMA_API_KEY or FIGMA_OAUTH_TOKEN in environment')
    headers = {'User-Agent': 'Hermes-FigmaIngest/1.0'}
    if oauth:
        headers['Authorization'] = f'Bearer {oauth}'
    else:
        headers['X-Figma-Token'] = api_key or ''
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            return json.loads(res.read().decode('utf-8'))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode('utf-8', 'ignore')[:500]
        raise SystemExit(f'Figma API HTTP {exc.code}: {body}') from exc


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('figma_link')
    parser.add_argument('--out', default='./raw')
    args = parser.parse_args()

    file_key, node_id = parse_figma_link(args.figma_link)
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if node_id:
        url = f'https://api.figma.com/v1/files/{file_key}/nodes?ids={urllib.parse.quote(node_id)}'
        out_file = out_dir / f"figma-node-{file_key}-{node_id.replace(':', '-')}.json"
    else:
        url = f'https://api.figma.com/v1/files/{file_key}'
        out_file = out_dir / f'figma-file-{file_key}.json'

    data = request_json(url)
    out_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'fileKey': file_key, 'nodeId': node_id, 'out': str(out_file)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
