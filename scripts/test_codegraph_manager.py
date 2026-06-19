import importlib.util
import json
import os
import stat
import sys
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).parent / "codegraph_manager.py"
spec = importlib.util.spec_from_file_location("codegraph_manager", SCRIPT)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
sys.modules["codegraph_manager"] = mod
spec.loader.exec_module(mod)


class CodegraphManagerTests(unittest.TestCase):
    def fake_binary(self, root: Path) -> Path:
        path = root / "codebase-memory-mcp"
        path.write_text(
            """#!/usr/bin/env python3
import json, sys
if '--version' in sys.argv:
    print('codebase-memory-mcp fake-1.0')
    raise SystemExit(0)
if len(sys.argv) >= 4 and sys.argv[1] == 'cli':
    tool = sys.argv[2]
    payload = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
    if tool == 'index_repository':
        print(json.dumps({'project':'demo','status':'indexed','nodes':3,'edges':2}))
    elif tool == 'list_projects':
        print(json.dumps({'projects':[{'name':'demo','root_path':'/tmp/demo','nodes':3,'edges':2}]}))
    elif tool == 'search_graph':
        print(json.dumps({'total':1,'results':[{'name':'handler'}],'has_more':False}))
    elif tool == 'trace_path':
        print(json.dumps({'function':payload.get('function_name'),'callers':[{'name':'caller'}]}))
    else:
        print(json.dumps({'ok': True}))
    raise SystemExit(0)
print('bad invocation', sys.argv, file=sys.stderr)
raise SystemExit(2)
""",
            encoding="utf-8",
        )
        path.chmod(path.stat().st_mode | stat.S_IXUSR)
        return path

    def test_doctor_missing_binary_fails(self):
        with tempfile.TemporaryDirectory() as td:
            result = mod.doctor(str(Path(td) / "missing"), Path(td) / "home")
            self.assertFalse(result.ok)
            self.assertFalse(result.checks[0].ok)

    def test_enable_writes_snippet_activation_and_cache(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            binary = self.fake_binary(root)
            home = root / "home"
            result = mod.enable(str(binary), home, dry_run=False, force=False, merge_config=False)
            self.assertTrue(result.ok, result.checks)
            snippet = home / "config" / "codegraph-mcp.yaml"
            activation = home / "state" / "codegraph-activation.json"
            self.assertTrue(snippet.exists())
            self.assertTrue(activation.exists())
            self.assertIn("CBM_CACHE_DIR", snippet.read_text(encoding="utf-8"))
            self.assertFalse(json.loads(activation.read_text(encoding="utf-8"))["side_effects"]["ui_enabled"])

    def test_enable_dry_run_does_not_write(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            binary = self.fake_binary(root)
            home = root / "home"
            result = mod.enable(str(binary), home, dry_run=True, force=False, merge_config=False)
            self.assertTrue(result.ok)
            self.assertFalse((home / "config" / "codegraph-mcp.yaml").exists())

    def test_smoke_uses_fake_binary_and_repo(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            binary = self.fake_binary(root)
            home = root / "home"
            repo = root / "repo"
            repo.mkdir()
            (repo / "app.py").write_text("def handler(): pass\n", encoding="utf-8")
            result = mod.smoke(str(binary), home, repo, query="handler", function_name="handler", mode="fast")
            self.assertTrue(result.ok, result.checks)
            self.assertEqual(result.data["project"], "demo")
            self.assertTrue((home / "cache" / "codebase-memory-mcp").exists())


if __name__ == "__main__":
    unittest.main()
