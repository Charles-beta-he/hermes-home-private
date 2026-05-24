#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path
import unittest
from unittest import mock

MODULE_PATH = Path.home() / ".hermes" / "scripts" / "lark_task_reader.py"


def load_module():
    spec = importlib.util.spec_from_file_location("hermes_lark_task_reader", MODULE_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


class FakeClient:
    def __init__(self):
        self.calls = []

    def get(self, path, token, query=None):
        self.calls.append((path, dict(query or {})))
        if path == "/task/v2/tasks" and not query.get("page_token"):
            return {"code": 0, "data": {"items": [
                {"guid": "old-1", "summary": "旧项目任务", "completed_at": "0", "custom_fields": []},
            ], "has_more": True, "page_token": "P2"}}
        if path == "/task/v2/tasks" and query.get("page_token") == "P2":
            return {"code": 0, "data": {"items": [
                {"guid": "uv-1", "summary": "登录页修复", "description": "修复邮箱 OTP", "completed_at": "0", "url": "https://task/uv-1", "custom_fields": [{"name": "清单", "text_value": "UVISA-2.0新版开发"}]},
                {"guid": "done-1", "summary": "已完成", "completed_at": "171", "custom_fields": []},
                {"guid": "tracked-1", "summary": "已有状态", "completed_at": "0", "custom_fields": [{"name": "状态", "value": "已派发"}]},
            ], "has_more": False}}
        if path == "/task/v2/tasks/uv-1/comments":
            return {"code": 999, "msg": "wrong endpoint"}
        if path == "/task/v2/comments":
            rich = json.dumps([{"elements": [
                {"text_run": {"content": "补充描述"}},
                {"link": {"url": "https://uaecprod.sg.larksuite.com/docx/DocABC"}},
                {"image": {"image_key": "img_key_1234567890"}},
                {"file": {"name": "需求截图.zip"}},
            ]}], ensure_ascii=False)
            return {"code": 0, "data": {"items": [{"content": rich, "creator": {"name": "alice"}}], "has_more": False}}
        raise AssertionError(f"unexpected GET {path} {query}")


class EmptyThenFallbackClient(FakeClient):
    def get(self, path, token, query=None):
        if path == "/task/v2/tasks/uv-1/comments":
            self.calls.append((path, dict(query or {})))
            return {"code": 0, "data": {"items": [], "has_more": False}}
        return super().get(path, token, query)


class BinaryImageClient(FakeClient):
    def __init__(self, fail_first=False, fail_all=False):
        super().__init__()
        self.binary_calls = []
        self.fail_first = fail_first
        self.fail_all = fail_all

    def get_binary(self, path, token, query=None, max_bytes=0):
        self.binary_calls.append((path, dict(query or {}), max_bytes))
        if self.fail_all:
            raise RuntimeError("not found")
        if self.fail_first and len(self.binary_calls) == 1:
            raise RuntimeError("primary not found")
        return b"\x89PNG\r\nimage", {"content-type": "image/png"}


class BrokenBinaryClient(FakeClient):
    def __init__(self):
        super().__init__()
        self.binary_calls = []

    def get_binary(self, path, token, query=None, max_bytes=0):
        self.binary_calls.append((path, dict(query or {}), max_bytes))
        raise TimeoutError("slow")


class LarkTaskReaderTest(unittest.TestCase):
    def setUp(self):
        self.mod = load_module()

    def test_prioritize_defaults_to_uvisa_scope_and_annotates(self):
        tasks = [
            {"guid": "old-1", "summary": "旧项目任务"},
            {"guid": "uv-1", "summary": "登录页", "custom_fields": [{"name": "项目", "text_value": "UVISA-2.0新版开发"}]},
        ]
        selected = self.mod.prioritize_tasks(tasks)
        self.assertEqual([t["guid"] for t in selected], ["uv-1"])
        self.assertEqual(selected[0]["_lark_task_scope"], "UVISA-2.0新版开发")
        self.assertTrue(selected[0]["_lark_task_scope_match"]["matched"])

    def test_tasklist_name_enables_only_scope(self):
        tasks = [{"guid": "uv-1", "summary": "登录页", "tasklists": [{"tasklist_guid": "tl-1"}]}]
        class TasklistClient:
            def get(self, path, token, query=None):
                self.last = (path, query)
                if path == "/task/v2/tasklists":
                    return {"code": 0, "data": {"items": [{"guid": "tl-1", "name": "UVISA-2.0新版开发", "url": "https://tasklist"}], "has_more": False}}
                if path == "/task/v2/sections":
                    return {"code": 0, "data": {"items": [], "has_more": False}}
                raise AssertionError(f"unexpected GET {path} {query}")
        enriched = self.mod.enrich_tasks_with_tasklists(tasks, "tok", client=TasklistClient())
        selected = self.mod.prioritize_tasks(enriched, scope_mode="only")
        self.assertEqual([t["guid"] for t in selected], ["uv-1"])
        self.assertEqual(selected[0]["tasklist_names"], ["UVISA-2.0新版开发"])

    def test_section_enrichment_exposes_admin_group_name(self):
        tasks = [{"guid": "admin-1", "summary": "银行路由", "tasklists": [{"tasklist_guid": "tl-1", "section_guid": "sec-admin"}]}]
        class SectionClient:
            def get(self, path, token, query=None):
                if path == "/task/v2/tasklists":
                    return {"code": 0, "data": {"items": [{"guid": "tl-1", "name": "UVISA-2.0新版开发"}], "has_more": False}}
                if path == "/task/v2/sections":
                    self.section_query = dict(query or {})
                    return {"code": 0, "data": {"items": [{"guid": "sec-admin", "name": "admin端相关问题"}], "has_more": False}}
                raise AssertionError(f"unexpected GET {path} {query}")
        client = SectionClient()
        enriched = self.mod.enrich_tasks_with_tasklists(tasks, "tok", client=client)
        self.assertEqual(enriched[0]["section_names"], ["admin端相关问题"])
        self.assertEqual(enriched[0]["tasklists"][0]["section_name"], "admin端相关问题")
        self.assertEqual(client.section_query["resource_type"], "tasklist")
        self.assertEqual(client.section_query["resource_id"], "tl-1")

    def test_tasklist_enrichment_failure_is_visible(self):
        tasks = [{"guid": "uv-1", "summary": "登录页", "tasklists": [{"tasklist_guid": "tl-1"}]}]
        class BrokenTasklistClient:
            def get(self, path, token, query=None):
                raise RuntimeError("forbidden")
        enriched = self.mod.enrich_tasks_with_tasklists(tasks, "tok", client=BrokenTasklistClient())
        self.assertEqual(enriched[0]["tasklist_names"], [])
        self.assertIn("tasklist_enrichment_failed", enriched[0]["tasklist_scope_enrichment_warning"])

    def test_collect_readonly_returns_uvisa_task_description_comments_and_images(self):
        fake = FakeClient()
        payloads = self.mod.collect_tasks(token="tok", client=fake, scope_mode="prefer", include_comments=True, include_docs=False)
        self.assertEqual([p["lark_task_guid"] for p in payloads], ["uv-1"])
        p = payloads[0]
        self.assertEqual(p["summary"], "登录页修复")
        self.assertIn("修复邮箱 OTP", p["description"])
        self.assertIn("alice", p["comments"])
        self.assertIn("补充描述", p["comments"])
        self.assertIn("补充描述", p["issue_body"])
        self.assertIn("[图片:img_key_1234567", p["comments"])
        self.assertIn("[附件:需求截图.zip]", p["comments"])
        self.assertEqual(p["comment_image_keys"], ["img_key_1234567890"])
        self.assertEqual(p["lark_task_scope"], "UVISA-2.0新版开发")
        self.assertEqual(p["lark_url"], "https://task/uv-1")
        self.assertIn(("/task/v2/tasks", {"page_size": 100, "completed": "false"}), fake.calls)
        self.assertIn(("/task/v2/tasks", {"page_size": 100, "completed": "false", "page_token": "P2"}), fake.calls)
        self.assertIn(("/task/v2/tasks/uv-1/comments", {"page_size": 50}), fake.calls)
        self.assertIn(("/task/v2/comments", {"resource_id": "uv-1", "resource_type": "task", "page_size": 50}), fake.calls)

    def test_empty_first_comment_endpoint_falls_back(self):
        fake = EmptyThenFallbackClient()
        payloads = self.mod.collect_tasks(token="tok", client=fake, scope_mode="prefer", include_comments=True, include_docs=False)
        self.assertIn("补充描述", payloads[0]["comments"])

    def test_download_comment_images_success_and_payload_paths(self):
        fake = BinaryImageClient()
        with tempfile.TemporaryDirectory() as td:
            payloads = self.mod.collect_tasks(token="tok", client=fake, scope_mode="prefer", include_comments=True, include_docs=False, download_images=True, image_cache_dir=td)
            images = payloads[0]["comment_images"]
            self.assertEqual(len(images), 1)
            self.assertEqual(images[0]["status"], "downloaded")
            self.assertEqual(images[0]["content_type"], "image/png")
            self.assertTrue(Path(images[0]["local_path"]).exists())
            self.assertIn(images[0]["local_path"], payloads[0]["issue_body"])
            self.assertEqual(fake.binary_calls[0][0], "/im/v1/images/img_key_1234567890")
            self.assertEqual(fake.binary_calls[0][1], {"image_type": "message"})

    def test_download_comment_images_fallback_after_primary_failure(self):
        fake = BinaryImageClient(fail_first=True)
        with tempfile.TemporaryDirectory() as td:
            records = self.mod.download_comment_images("tok", ["img_key_1234567890"], cache_dir=td, client=fake)
        self.assertEqual(records[0]["status"], "downloaded")
        self.assertGreaterEqual(len(fake.binary_calls), 2)
        self.assertEqual(fake.binary_calls[1][0], "/im/v1/images/img_key_1234567890")
        self.assertEqual(fake.binary_calls[1][1], {})

    def test_download_comment_images_failure_does_not_abort(self):
        fake = BrokenBinaryClient()
        with tempfile.TemporaryDirectory() as td:
            records = self.mod.download_comment_images("tok", ["img_key_1234567890"], cache_dir=td, client=fake)
        self.assertEqual(records[0]["status"], "failed")
        self.assertEqual(records[0]["local_path"], "")
        self.assertIn("TimeoutError", records[0]["error"])

    def test_download_comment_images_uses_existing_cache(self):
        fake = BinaryImageClient()
        with tempfile.TemporaryDirectory() as td:
            path = self.mod._image_cache_path("img_key_1234567890", "image/png", td)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"cached")
            records = self.mod.download_comment_images("tok", ["img_key_1234567890"], cache_dir=td, client=fake)
        self.assertEqual(records[0]["status"], "cached")
        self.assertEqual(fake.binary_calls, [])

    def test_image_placeholder_without_key_is_preserved_as_unavailable(self):
        class PlaceholderClient(FakeClient):
            def get(self, path, token, query=None):
                if path == "/task/v2/comments":
                    return {"code": 0, "data": {"items": [{"content": "[Image]", "creator": {"name": "alice"}}], "has_more": False}}
                return super().get(path, token, query)
        fake = PlaceholderClient()
        payloads = self.mod.collect_tasks(token="tok", client=fake, scope_mode="prefer", include_comments=True, include_docs=False, download_images=True)
        p = payloads[0]
        self.assertEqual(p["comment_image_keys"], [])
        self.assertEqual(p["comment_image_placeholders"], 1)
        self.assertIn("[Image]", p["comments"])
        self.assertIn("评论图片待解析", p["issue_body"])
        self.assertEqual(p["comment_images"][0]["status"], "unavailable")
        self.assertIn("without image_key/file_token", p["comment_images"][0]["error"])

    def test_get_token_invokes_guard_on_missing_token_by_default(self):
        calls = {"count": 0}

        def fake_read(root):
            calls["count"] += 1
            if calls["count"] == 1:
                raise RuntimeError("Lark token unavailable: NO_TOKEN")
            return "tok-after-auth"

        with mock.patch.object(self.mod, "_read_lark_mcp_token", side_effect=fake_read), \
             mock.patch.object(self.mod, "_ensure_lark_auth", return_value={"ok": True}) as guard:
            token = self.mod.get_token(auto_auth=None, auto_authorize=True)
        self.assertEqual(token, "tok-after-auth")
        guard.assert_called_once_with(auto_authorize=True)

    def test_get_token_can_disable_auto_auth(self):
        with mock.patch.object(self.mod, "_read_lark_mcp_token", side_effect=RuntimeError("NO_TOKEN")), \
             mock.patch.object(self.mod, "_ensure_lark_auth") as guard:
            with self.assertRaises(RuntimeError):
                self.mod.get_token(auto_auth=False)
        guard.assert_not_called()

    def test_collect_tasks_passes_auto_auth_flags_to_token_reader(self):
        fake = FakeClient()
        with mock.patch.object(self.mod, "get_token", return_value="tok") as get_token:
            self.mod.collect_tasks(client=fake, scope_mode="prefer", include_comments=False, include_docs=False, auto_auth=True, auto_authorize=False)
        get_token.assert_called_once_with(auto_auth=True, auto_authorize=False)

    def test_only_mode_hard_filters_by_tasklist_and_off_mode_returns_all(self):
        tasks = [
            {"guid": "old-1", "summary": "新版开发 merely in title", "completed_at": "0", "custom_fields": []},
            {"guid": "empty-list", "summary": "新版开发", "tasklist_names": [], "completed_at": "0", "custom_fields": []},
            {"guid": "uv-1", "summary": "登录页", "tasklist_names": ["UVISA-2.0新版开发"], "completed_at": "0", "custom_fields": []},
        ]
        self.assertEqual([t["guid"] for t in self.mod.prioritize_tasks(tasks, scope_mode="only")], ["uv-1"])
        self.assertEqual([t["guid"] for t in self.mod.prioritize_tasks(tasks, scope_mode="off")], ["old-1", "empty-list", "uv-1"])

    def test_reader_has_no_lark_writeback_http_verbs(self):
        source = MODULE_PATH.read_text()
        verbs = ("POST", "PUT", "PATCH", "DELETE")
        forbidden = []
        for verb in verbs:
            forbidden.extend([f'method="{verb}"', "method='" + verb + "'", "." + verb.lower() + "("])
        for token in forbidden:
            self.assertNotIn(token, source)

    def test_reader_has_no_hardcoded_lark_secret_assignments(self):
        source = MODULE_PATH.read_text()
        forbidden_patterns = [
            "LARK" + "_USER_ACCESS_TOKEN" + " =",
            "FEISHU" + "_USER_ACCESS_TOKEN" + " =",
            "APP" + "_SECRET" + " =",
            "app" + "_secret" + " =",
            "api" + "_key" + " =",
            "pass" + "word" + " =",
        ]
        for pattern in forbidden_patterns:
            self.assertNotIn(pattern, source)

    def test_status_pending_values_are_not_skipped(self):
        for value in ("", "未开始", "待处理", "Todo", "Open"):
            self.assertTrue(self.mod.should_include_unprocessed({"completed_at": "0", "custom_fields": [{"name": "状态", "value": value}]}), value)
        for value in ("已派发", "处理中", "已完成", "Done", "Closed"):
            self.assertFalse(self.mod.should_include_unprocessed({"completed_at": "0", "custom_fields": [{"name": "状态", "value": value}]}), value)

    def test_rich_description_is_parsed_into_issue_body(self):
        rich = json.dumps([{"elements": [{"text_run": {"content": "富文本描述"}, "children": [{"text_run": {"content": "嵌套文本"}}]}]}], ensure_ascii=False)
        task = {"guid": "uv-2", "summary": "富文本", "description": rich, "completed_at": "0", "custom_fields": [{"name": "清单", "text_value": "UVISA-2.0新版开发"}]}
        p = self.mod.payload_from_task("tok", task, client=FakeClient(), include_comments=False, include_docs=False)
        self.assertIn("富文本描述", p["description"])
        self.assertIn("嵌套文本", p["description"])
        self.assertIn("富文本描述", p["issue_body"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
