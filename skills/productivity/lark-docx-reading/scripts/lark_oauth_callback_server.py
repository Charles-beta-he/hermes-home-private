#!/usr/bin/env python3
"""Minimal localhost OAuth callback catcher for Lark user-identity OAuth.

Writes only query parameters to /tmp/lark-oauth-callback.json. Do not print or
commit the resulting file; it may contain a one-time OAuth code.
"""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

OUT = Path('/tmp/lark-oauth-callback.json')


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 - stdlib callback name
        parsed = urlparse(self.path)
        query = {k: v[0] if len(v) == 1 else v for k, v in parse_qs(parsed.query).items()}
        OUT.write_text(json.dumps({'path': parsed.path, 'query': query}, ensure_ascii=False, indent=2), encoding='utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write('Lark OAuth callback captured. You can close this tab.\n'.encode('utf-8'))

    def log_message(self, fmt, *args):
        return


if __name__ == '__main__':
    HTTPServer(('127.0.0.1', 8765), Handler).serve_forever()
