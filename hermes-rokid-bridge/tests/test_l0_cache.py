import json
import tempfile
import unittest
from pathlib import Path

import app


class AccessBrainCoreTests(unittest.TestCase):
    def test_access_brain_core_is_adapter_neutral_and_importable_without_fastapi_app(self):
        from access_brain import ACCESS_BRAIN_TAXONOMY, SURFACE_ADAPTER_REGISTRY, build_access_layer_text

        self.assertEqual(ACCESS_BRAIN_TAXONOMY.layer_name, "入口脑")
        self.assertEqual(ACCESS_BRAIN_TAXONOMY.layer_id, "access_brain")
        self.assertIn("rokid_glasses", SURFACE_ADAPTER_REGISTRY)
        self.assertEqual(SURFACE_ADAPTER_REGISTRY["rokid_glasses"].surface_name, "眼镜端")
        self.assertEqual(SURFACE_ADAPTER_REGISTRY["rokid_glasses"].role, "device_adapter")
        answer = build_access_layer_text()
        self.assertIn("入口脑是能力层", answer)
        self.assertIn("眼镜端只是当前设备适配层", answer)
        self.assertIn("Access Brain > 设备适配器", answer)

    def test_access_brain_core_classifies_queries_without_app_imports(self):
        from access_brain import build_capability_text, handle_access_layer_query

        handled, answer = handle_access_layer_query("眼镜端这个名字和技能层级是否太局限？")
        self.assertTrue(handled)
        self.assertIn("入口脑是能力层", answer)
        self.assertIn("L0快答", answer)

        handled, answer = handle_access_layer_query("今天日报有什么")
        self.assertFalse(handled)
        self.assertEqual(answer, "")

        capability = build_capability_text()
        self.assertIn("入口脑", capability)
        self.assertIn("眼镜端只是当前设备适配器", capability)
        self.assertLessEqual(len(capability), 120)


class DailyBriefFormatterTests(unittest.TestCase):
    def test_formatter_is_cache_data_only_and_handles_summary_items_and_empty_cache(self):
        from daily_brief import build_daily_brief_text_from_cache

        summary_answer = build_daily_brief_text_from_cache({"summary": "今天重点：入口脑推进。", "updated_at": "2026-05-21 12:30"})
        self.assertIn("日报缓存：今天重点：入口脑推进。", summary_answer)
        self.assertIn("更新时间 2026-05-21 12:30", summary_answer)

        items_answer = build_daily_brief_text_from_cache({"items": ["A", "B", "C", "D"], "time": "noon"})
        self.assertIn("日报缓存：A；B；C", items_answer)
        self.assertNotIn("D", items_answer)
        self.assertIn("更新时间 noon", items_answer)

        self.assertEqual(
            build_daily_brief_text_from_cache({}),
            "日报缓存还没生成。你可以说“后台查日报”，我查完发 Telegram。",
        )
        self.assertEqual(
            build_daily_brief_text_from_cache({"items": []}),
            "日报缓存是空的。你可以说“后台查日报”，我查完发 Telegram。",
        )

    def test_formatter_truncates_long_summary_for_voice(self):
        from daily_brief import build_daily_brief_text_from_cache

        answer = build_daily_brief_text_from_cache({"text": "甲" * 240})

        self.assertTrue(answer.startswith("日报缓存："))
        self.assertIn("甲" * 180, answer)
        self.assertNotIn("甲" * 181, answer)


class ManufacturingStatusFormatterTests(unittest.TestCase):
    def test_formatter_is_cache_data_only_and_redacts_private_like_fields(self):
        from manufacturing_status import build_manufacturing_status_text_from_cache

        answer = build_manufacturing_status_text_from_cache(
            {
                "status": "ok",
                "updated_at": "2026-05-21T10:40:00+08:00",
                "BAMBU" "_ACCESS" "_CODE": "PRIVATE_VALUE_FOR_REDACTION_TEST",
                "summary": {
                    "device": "Bambu X2D",
                    "state": "RUNNING",
                    "percent": 42,
                    "remaining_minutes": 85,
                    "layer": 120,
                    "total_layers": 300,
                    "nozzle": 220,
                    "bed": 55,
                    "ams_tray_now": "2",
                    "error_text": "暂无错误",
                },
            }
        )

        self.assertIn("Bambu X2D", answer)
        self.assertIn("进度 42%", answer)
        self.assertIn("剩余 85 分钟", answer)
        self.assertIn("云端安全缓存播报", answer)
        self.assertIn("未执行控制", answer)
        self.assertNotIn("未连接打印机", answer)
        sensitive_key = "BAMBU" "_ACCESS" "_CODE"
        self.assertNotIn(sensitive_key, answer)
        self.assertNotIn("PRIVATE_VALUE_FOR_REDACTION_TEST", answer)

    def test_formatter_falls_back_from_raw_job_shape_without_filesystem_or_adapter(self):
        from manufacturing_status import build_manufacturing_status_text_from_cache

        answer = build_manufacturing_status_text_from_cache(
            {
                "status": "ok",
                "generated_at": "2026-05-21T10:41:00+08:00",
                "job": {"state": "IDLE", "percent": 0, "remaining_minutes": 0, "layer": 0, "total_layers": 0},
                "temperature": {"nozzle": 36, "bed": 31},
                "ams": {"tray_now": "1"},
                "errors": {"err": "暂无错误"},
            }
        )

        self.assertIn("X2D 状态", answer)
        self.assertIn("IDLE", answer)
        self.assertIn("喷嘴 36 度", answer)
        self.assertIn("热床 31 度", answer)
        self.assertIn("当前料盘 1", answer)


class L0RouteRegistryTests(unittest.TestCase):
    def test_adapter_neutral_registry_exposes_ordered_route_ids_without_app_imports(self):
        from l0_routes import L0_ROUTE_REGISTRY, route_ids

        ids = route_ids(L0_ROUTE_REGISTRY)

        self.assertLess(ids.index("access_layer"), ids.index("capability"))
        self.assertIn("manufacturing_status", ids)
        self.assertIn("daily_brief", ids)
        self.assertIn("local_brain_stats", ids)
        self.assertTrue(all(route.is_read_only for route in L0_ROUTE_REGISTRY))
        self.assertTrue(all(route.side_effect_scope == "none" for route in L0_ROUTE_REGISTRY))

    def test_text_only_route_matching_is_reusable_by_app(self):
        from l0_routes import L0_ROUTE_REGISTRY, match_text_route

        route = match_text_route("制造脑状态", L0_ROUTE_REGISTRY)
        self.assertIsNotNone(route)
        self.assertEqual(route.route_id, "manufacturing_status")
        self.assertTrue(route.matches("X2D 状态怎么样"))
        self.assertTrue(route.matches("多脑架构里的制造脑进度"))
        self.assertTrue(route.matches("制造脑的进毒"))
        self.assertTrue(route.matches("制造脑的净度"))
        self.assertTrue(route.matches("打印机装太怎么样"))
        self.assertFalse(route.matches("确认执行"))
        self.assertFalse(route.matches("今天想吃进度条"))


class L0CacheTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.old_cache = app.ROKID_DAILY_BRIEF_CACHE
        self.old_manufacturing_cache = app.ROKID_MANUFACTURING_STATUS_CACHE
        app.ROKID_DAILY_BRIEF_CACHE = str(Path(self.tmpdir.name) / "daily_brief_cache.json")
        app.ROKID_MANUFACTURING_STATUS_CACHE = str(Path(self.tmpdir.name) / "manufacturing_status_cache.json")

    def tearDown(self):
        app.ROKID_DAILY_BRIEF_CACHE = self.old_cache
        app.ROKID_MANUFACTURING_STATUS_CACHE = self.old_manufacturing_cache
        self.tmpdir.cleanup()

    def test_capability_query_is_answered_from_l0(self):
        handled, answer = app.handle_l0_query("你能做什么")
        self.assertTrue(handled)
        self.assertIn("入口脑", answer)
        self.assertIn("眼镜端只是当前设备适配器", answer)
        self.assertIn("确认执行", answer)

    def test_access_layer_query_names_glasses_as_adapter_not_architecture_boundary(self):
        handled, answer = app.handle_l0_query("眼镜端这个名字和技能层级是否太局限？")
        self.assertTrue(handled)
        self.assertIn("入口脑是能力层", answer)
        self.assertIn("眼镜端只是当前设备适配层", answer)
        self.assertIn("L0快答", answer)
        self.assertIn("L2后台升级", answer)

    def test_daily_brief_query_uses_local_cache(self):
        Path(app.ROKID_DAILY_BRIEF_CACHE).write_text(
            json.dumps({"summary": "今天三条重点：模型延迟、任务池、眼镜入口", "updated_at": "2026-05-20 19:30"}, ensure_ascii=False),
            encoding="utf-8",
        )
        handled, answer = app.handle_l0_query("今天日报有什么")
        self.assertTrue(handled)
        self.assertIn("模型延迟", answer)
        self.assertIn("2026-05-20", answer)

    def test_manufacturing_status_query_uses_readonly_cache(self):
        Path(app.ROKID_MANUFACTURING_STATUS_CACHE).write_text(
            json.dumps(
                {
                    "schema": "hermes_rokid_manufacturing_status_cache_v1",
                    "updated_at": "2026-05-21T10:40:00+08:00",
                    "source": "bambu_x2d.py status --timeout 6",
                    "status": "ok",
                    "summary": {
                        "device": "Bambu X2D",
                        "state": "RUNNING",
                        "percent": 42,
                        "remaining_minutes": 85,
                        "layer": 120,
                        "total_layers": 300,
                        "nozzle": 220,
                        "bed": 55,
                        "ams_tray_now": "2",
                        "error_text": "暂无错误",
                    },
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        handled, answer = app.handle_l0_query("X2D 状态怎么样，打印还要多久？")

        self.assertTrue(handled)
        self.assertIn("X2D", answer)
        self.assertIn("进度 42%", answer)
        self.assertIn("剩余 85 分钟", answer)
        self.assertIn("喷嘴 220 度", answer)
        self.assertIn("热床 55 度", answer)
        self.assertIn("云端安全缓存", answer)
        sensitive_key = "BAMBU" "_ACCESS" "_CODE"
        self.assertNotIn(sensitive_key, answer)

    def test_manufacturing_status_query_without_cache_fails_soft(self):
        handled, answer = app.handle_l0_query("制造脑状态")

        self.assertTrue(handled)
        self.assertIn("制造脑状态缓存还没生成", answer)

    def test_manufacturing_status_error_hides_env_internals_for_voice(self):
        Path(app.ROKID_MANUFACTURING_STATUS_CACHE).write_text(
            json.dumps({
                "status": "error",
                "updated_at": "2026-05-21T10:40:00+08:00",
                "error": "Missing " + ("BAMBU" "_ACCESS" "_CODE") + " env var; refusing to use stored printer private value",
            }, ensure_ascii=False),
            encoding="utf-8",
        )

        handled, answer = app.handle_l0_query("制造脑的进毒")

        self.assertTrue(handled)
        self.assertIn("本机缺少 Bambu 只读访问码", answer)
        sensitive_key = "BAMBU" "_ACCESS" "_CODE"
        self.assertNotIn(sensitive_key, answer)
        self.assertNotIn("stored printer private value", answer)

    def test_brain_architecture_status_query_uses_local_brain_stats_not_model(self):
        handled, answer = app.handle_l0_query("多脑架构什么状态")

        self.assertTrue(handled)
        self.assertRegex(answer, "本地脑|待办|任务|pending")


if __name__ == "__main__":
    unittest.main()
