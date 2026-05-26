import asyncio
import json
import tempfile
import unittest
from pathlib import Path

import app


def _text_payload(text: str, user_id="long-term-user", message_id: str = "msg-1", metadata=None) -> app.RokidRequest:
    return app.RokidRequest(
        message_id=message_id,
        agent_id="hermes-rokid",
        user_id=user_id,
        message=[app.Message(role="user", type="text", text=text)],
        metadata=metadata,
    )


def _image_payload(image_url: str, text=None, user_id="long-term-user") -> app.RokidRequest:
    messages = [app.Message(role="user", type="image", image_url=image_url)]
    if text:
        messages.append(app.Message(role="user", type="text", text=text))
    return app.RokidRequest(
        message_id="img-1",
        agent_id="hermes-rokid",
        user_id=user_id,
        message=messages,
    )


def _decode_sse(chunks):
    events = []
    for chunk in chunks:
        event_name = None
        data = None
        for line in chunk.strip().splitlines():
            if line.startswith("event: "):
                event_name = line[len("event: "):]
            if line.startswith("data: "):
                data = json.loads(line[len("data: "):])
        if event_name and data is not None:
            events.append((event_name, data))
    return events


def _visible_answer(events):
    return "".join(
        str(data.get("answer_stream") or "")
        for event, data in events
        if event == "message"
    )


class DeviceContextContractTests(unittest.TestCase):
    def test_device_context_extracts_text_images_metadata_and_safe_session_fallback(self):
        from rokid_bridge.context import extract_device_context

        payload = app.RokidRequest(
            message_id="m-device-1",
            agent_id="hermes-rokid",
            user_id=None,
            message=[
                app.Message(role="user", type="image", image_url="https://example.com/a.jpg"),
                app.Message(role="user", type="text", text="帮我看看这个报错"),
            ],
            metadata={"context": {"location": "西安", "weather": "晴", "battery": "80%"}},
        )

        ctx = extract_device_context(payload)

        self.assertEqual(ctx.message_id, "m-device-1")
        self.assertEqual(ctx.user_text, "帮我看看这个报错")
        self.assertEqual(ctx.images, ["https://example.com/a.jpg"])
        self.assertEqual(ctx.device_context["location"], "西安")
        self.assertEqual(ctx.device_context["weather"], "晴")
        self.assertNotEqual(ctx.session_key, "hermes-rokid", "missing user_id must not collapse all public users into the agent_id session")
        self.assertIn("m-device-1", ctx.session_key)

    def test_location_status_is_read_only_and_uses_existing_device_context(self):
        from rokid_bridge.context import extract_device_context

        payload = app.RokidRequest(
            message_id="m-location-1",
            agent_id="hermes-rokid",
            user_id="user-location",
            message=[app.Message(role="user", type="text", text="我现在在哪？")],
            metadata={"context": {"location": "西安高新区", "latitude": 34.2, "longitude": 108.9, "accuracy": "30m", "timestamp": "2026-05-20T16:40:00Z"}},
        )

        status = extract_device_context(payload).get_location_status()

        self.assertTrue(status["is_read_only"])
        self.assertTrue(status["has_location"])
        self.assertTrue(status["has_coordinates"])
        self.assertEqual(status["location"], "西安高新区")
        self.assertEqual(status["latitude"], 34.2)
        self.assertEqual(status["longitude"], 108.9)

    def test_location_status_unknown_when_payload_has_no_location(self):
        from rokid_bridge.context import extract_device_context

        payload = app.RokidRequest(
            message_id="m-location-empty",
            agent_id="hermes-rokid",
            user_id="user-location",
            message=[app.Message(role="user", type="text", text="我在哪里？")],
            metadata={"context": {"battery": "80%"}},
        )

        status = extract_device_context(payload).get_location_status()

        self.assertTrue(status["is_read_only"])
        self.assertFalse(status["has_location"])
        self.assertEqual(status["location"], "unknown")
        self.assertEqual(status["source"], "none")

    def test_device_status_summarizes_battery_network_context_and_image_count(self):
        from rokid_bridge.context import extract_device_context

        payload = app.RokidRequest(
            message_id="m-device-status",
            agent_id="hermes-rokid",
            user_id="user-device",
            message=[
                app.Message(role="user", type="image", image_url="https://example.com/private.jpg"),
                app.Message(role="user", type="text", text="眼镜状态"),
            ],
            metadata={"context": {"battery": "80%", "network": "wifi", "device": "Rokid Glasses"}},
        )

        status = extract_device_context(payload).get_device_status()

        self.assertTrue(status["is_read_only"])
        self.assertEqual(status["battery"], "80%")
        self.assertEqual(status["network"], "wifi")
        self.assertEqual(status["image_count"], 1)
        self.assertNotIn("private.jpg", json.dumps(status, ensure_ascii=False))


class LongTermGlassesUxTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.old_queue = app.ROKID_UPGRADE_QUEUE_PATH
        self.old_manufacturing_cache = app.ROKID_MANUFACTURING_STATUS_CACHE
        self.old_budget = app.ROKID_MODEL_BUDGET_SECONDS
        self.old_sessions = dict(app.TASK_SESSIONS)
        self.old_bg_sessions = dict(app.BACKGROUND_CONTROL_SESSIONS)
        app.ROKID_UPGRADE_QUEUE_PATH = str(Path(self.tmpdir.name) / "pending_upgrades.jsonl")
        app.ROKID_MANUFACTURING_STATUS_CACHE = str(Path(self.tmpdir.name) / "manufacturing_status_cache.json")
        app.ROKID_MODEL_BUDGET_SECONDS = 0.2
        app.TASK_SESSIONS.clear()
        app.BACKGROUND_CONTROL_SESSIONS.clear()

    def tearDown(self):
        app.ROKID_UPGRADE_QUEUE_PATH = self.old_queue
        app.ROKID_MANUFACTURING_STATUS_CACHE = self.old_manufacturing_cache
        app.ROKID_MODEL_BUDGET_SECONDS = self.old_budget
        app.TASK_SESSIONS.clear()
        app.TASK_SESSIONS.update(self.old_sessions)
        app.BACKGROUND_CONTROL_SESSIONS.clear()
        app.BACKGROUND_CONTROL_SESSIONS.update(self.old_bg_sessions)
        self.tmpdir.cleanup()

    async def test_access_layer_naming_query_returns_l0_answer_and_does_not_enqueue(self):
        payload = _text_payload("眼镜端这个名字和技能层级是否太局限？", user_id="access-layer-user", message_id="access-layer-msg-1")

        chunks = [chunk async for chunk in app.stream_answer(payload)]
        answer = _visible_answer(_decode_sse(chunks))

        self.assertIn("收到，我在处理", answer)
        self.assertIn("入口脑是能力层", answer)
        self.assertIn("设备适配层", answer)
        self.assertIn("确认门", answer)
        self.assertFalse(Path(app.ROKID_UPGRADE_QUEUE_PATH).exists(), "access-layer naming query must not enqueue L2 work")

    async def test_location_status_query_returns_l0_answer_and_does_not_enqueue(self):
        payload = _text_payload(
            "我现在在哪？",
            user_id="location-user",
            message_id="location-msg-1",
            metadata={"context": {"location": "西安高新区", "latitude": 34.2, "longitude": 108.9, "accuracy": "30m"}},
        )

        chunks = [chunk async for chunk in app.stream_answer(payload)]
        answer = _visible_answer(_decode_sse(chunks))

        self.assertIn("收到，我在处理", answer)
        self.assertIn("西安高新区", answer)
        self.assertIn("经纬度", answer)
        self.assertIn("未写入后台", answer)
        self.assertFalse(Path(app.ROKID_UPGRADE_QUEUE_PATH).exists(), "read-only location query must not enqueue L2 work")

    async def test_location_status_query_without_location_does_not_guess_or_enqueue(self):
        payload = _text_payload(
            "我在哪里？",
            user_id="location-user",
            message_id="location-msg-2",
            metadata={"context": {"battery": "80%"}},
        )

        chunks = [chunk async for chunk in app.stream_answer(payload)]
        answer = _visible_answer(_decode_sse(chunks))

        self.assertIn("没有带定位信息", answer)
        self.assertIn("不会猜位置", answer)
        self.assertFalse(Path(app.ROKID_UPGRADE_QUEUE_PATH).exists(), "missing-location read-only query must not enqueue L2 work")

    async def test_get_local_location_phrase_uses_l0_coords_not_model_fallback(self):
        payload = _text_payload(
            "获取本地位置",
            user_id="location-user",
            message_id="location-msg-3",
            metadata={"context": {"lat": 34.34, "lng": 108.94}},
        )

        chunks = [chunk async for chunk in app.stream_answer(payload)]
        answer = _visible_answer(_decode_sse(chunks))

        self.assertIn("经纬度：34.34，108.94", answer)
        self.assertIn("未写入后台", answer)
        self.assertNotIn("无法直接获取", answer)
        self.assertFalse(Path(app.ROKID_UPGRADE_QUEUE_PATH).exists(), "local-location read-only query must not enqueue L2 work")

    async def test_nested_location_context_is_normalized_before_answering(self):
        payload = _text_payload(
            "本地位置",
            user_id="location-user",
            message_id="location-msg-4",
            metadata={"context": {"location": {"city": "西安", "latitude": 34.34, "longitude": 108.94, "accuracy": "20m"}}},
        )

        chunks = [chunk async for chunk in app.stream_answer(payload)]
        answer = _visible_answer(_decode_sse(chunks))

        self.assertIn("位置：西安", answer)
        self.assertIn("经纬度：34.34，108.94", answer)
        self.assertNotIn("{'city'", answer)
        self.assertFalse(Path(app.ROKID_UPGRADE_QUEUE_PATH).exists(), "nested location read-only query must not enqueue L2 work")

    async def test_top_level_rokid_metadata_location_is_normalized_before_answering(self):
        payload = _text_payload(
            "获取本地位置。",
            user_id="location-user",
            message_id="location-msg-5",
            metadata={
                "battery": "89",
                "current_time": "2026-05-22 18:44:28",
                "latitude": "30.24243",
                "location": "中国浙江省杭州市余杭区天目山路536-1号(留下地铁站B2口步行220米)",
                "longitude": "120.04926",
                "weather": "当前天气雾，24度",
            },
        )

        chunks = [chunk async for chunk in app.stream_answer(payload)]
        answer = _visible_answer(_decode_sse(chunks))

        self.assertIn("天目山路536-1号", answer)
        self.assertIn("经纬度：30.24243，120.04926", answer)
        self.assertIn("时间 2026-05-22 18:44:28", answer)
        self.assertNotIn("没有带定位信息", answer)
        self.assertFalse(Path(app.ROKID_UPGRADE_QUEUE_PATH).exists(), "top-level Rokid metadata location must stay read-only and not enqueue L2 work")

    async def test_device_status_query_returns_l0_answer_and_does_not_enqueue(self):
        payload = app.RokidRequest(
            message_id="device-status-msg-1",
            agent_id="hermes-rokid",
            user_id="device-user",
            message=[
                app.Message(role="user", type="image", image_url="https://example.com/private-image.jpg"),
                app.Message(role="user", type="text", text="眼镜状态怎么样？你收到什么上下文？"),
            ],
            metadata={"context": {"battery": "80%", "network": "wifi", "location": "西安"}},
        )

        chunks = [chunk async for chunk in app.stream_answer(payload)]
        answer = _visible_answer(_decode_sse(chunks))

        self.assertIn("收到，我在处理", answer)
        self.assertIn("电量：80%", answer)
        self.assertIn("网络：wifi", answer)
        self.assertIn("上下文", answer)
        self.assertIn("图片 1 张", answer)
        self.assertNotIn("private-image.jpg", answer)
        self.assertIn("未写入后台", answer)
        self.assertFalse(Path(app.ROKID_UPGRADE_QUEUE_PATH).exists(), "read-only device status query must not enqueue L2 work")

    async def test_device_status_query_without_context_is_unknown_not_guessed(self):
        payload = _text_payload("电量多少？网络怎么样？", user_id="device-user", message_id="device-status-msg-2")

        chunks = [chunk async for chunk in app.stream_answer(payload)]
        answer = _visible_answer(_decode_sse(chunks))

        self.assertIn("电量未知", answer)
        self.assertIn("网络未知", answer)
        self.assertIn("不会猜测", answer)
        self.assertFalse(Path(app.ROKID_UPGRADE_QUEUE_PATH).exists(), "missing device context query must not enqueue L2 work")

    async def test_manufacturing_status_query_returns_l0_cache_answer_and_does_not_enqueue(self):
        Path(app.ROKID_MANUFACTURING_STATUS_CACHE).write_text(
            json.dumps(
                {
                    "schema": "hermes_rokid_manufacturing_status_cache_v1",
                    "updated_at": "2026-05-21T10:50:00+08:00",
                    "status": "ok",
                    "summary": {
                        "device": "Bambu X2D",
                        "state": "RUNNING",
                        "percent": 42,
                        "remaining_minutes": 85,
                        "nozzle": 220,
                        "bed": 55,
                        "error_text": "暂无错误",
                    },
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        payload = _text_payload("X2D 状态怎么样，打印还要多久？", user_id="manufacturing-user", message_id="manufacturing-status-msg-1")

        chunks = [chunk async for chunk in app.stream_answer(payload)]
        answer = _visible_answer(_decode_sse(chunks))

        self.assertIn("收到，我在处理", answer)
        self.assertIn("进度 42%", answer)
        self.assertIn("剩余 85 分钟", answer)
        self.assertIn("云端安全缓存播报", answer)
        self.assertIn("未执行控制", answer)
        self.assertNotIn("未连接打印机", answer)
        self.assertFalse(Path(app.ROKID_UPGRADE_QUEUE_PATH).exists(), "read-only manufacturing status query must not enqueue L2 work")

    async def test_image_only_does_not_let_text_model_hallucinate_vision(self):
        async def hallucinating_model(_prompt: str) -> str:
            return "这是一只猫，正在桌子上。"

        old_run_fast_model = app.run_fast_model
        app.run_fast_model = hallucinating_model
        try:
            chunks = [chunk async for chunk in app.stream_answer(_image_payload("https://example.com/cat.jpg"))]
        finally:
            app.run_fast_model = old_run_fast_model

        answer = _visible_answer(_decode_sse(chunks))
        self.assertIn("收到，我在处理", answer)
        self.assertIn("图片", answer)
        self.assertRegex(answer, "还没启用视觉|不能可靠识别|请补充文字")
        self.assertNotIn("猫", answer)
        self.assertFalse(Path(app.ROKID_UPGRADE_QUEUE_PATH).exists(), "image-only placeholder should not create L2 work unless user asks for background analysis")

    async def test_high_impact_send_message_requires_confirmation_not_execution_claim(self):
        async def unsafe_model(_prompt: str) -> str:
            return "已发送 Telegram 给张三：十点开会。"

        old_run_fast_model = app.run_fast_model
        app.run_fast_model = unsafe_model
        try:
            chunks = [chunk async for chunk in app.stream_answer(_text_payload("帮我发 Telegram 给张三说十点开会"))]
        finally:
            app.run_fast_model = old_run_fast_model

        answer = _visible_answer(_decode_sse(chunks))
        self.assertNotIn("已发送", answer)
        self.assertNotIn("发送成功", answer)
        self.assertRegex(answer, "确认|需要你确认|请说")
        self.assertFalse(Path(app.ROKID_UPGRADE_QUEUE_PATH).exists(), "send-message intent must not enter L2 before explicit confirmation")

    async def test_glasses_photo_print_request_is_confirm_first_and_no_direct_print(self):
        async def unsafe_model(_prompt: str) -> str:
            return "已开始打印。"

        old_run_fast_model = app.run_fast_model
        app.run_fast_model = unsafe_model
        try:
            payload = app.RokidRequest(
                message_id="print-photo-1",
                agent_id="hermes-rokid",
                user_id="printer-user",
                message=[
                    app.Message(role="user", type="image", image_url="https://example.com/private-object.jpg"),
                    app.Message(role="user", type="text", text="把这个拍照直接打印出来"),
                ],
            )
            chunks = [chunk async for chunk in app.stream_answer(payload)]
        finally:
            app.run_fast_model = old_run_fast_model

        answer = _visible_answer(_decode_sse(chunks))
        self.assertIn("收到，我在处理", answer)
        self.assertNotIn("已开始打印", answer)
        self.assertNotIn("打印成功", answer)
        self.assertRegex(answer, "确认|预览|模型|切片|不能直接")
        self.assertFalse(Path(app.ROKID_UPGRADE_QUEUE_PATH).exists(), "glasses photo print must not enqueue or execute before explicit confirmation")

    async def test_print_execution_claim_is_clamped_to_confirmation(self):
        async def unsafe_model(_prompt: str) -> str:
            return "已执行打印，机器已经开始工作。"

        old_run_fast_model = app.run_fast_model
        app.run_fast_model = unsafe_model
        try:
            chunks = [chunk async for chunk in app.stream_answer(_text_payload("直接开始打印这个模型"))]
        finally:
            app.run_fast_model = old_run_fast_model

        answer = _visible_answer(_decode_sse(chunks))
        self.assertNotIn("已执行打印", answer)
        self.assertNotIn("已经开始工作", answer)
        self.assertRegex(answer, "确认|需要你确认|不能直接")
        self.assertFalse(Path(app.ROKID_UPGRADE_QUEUE_PATH).exists())

    async def test_screenshot_status_phrases_are_l0_and_do_not_fall_through_to_model(self):
        async def forbidden_model(_prompt: str) -> str:
            raise AssertionError("status phrases should be handled by deterministic L0 routes")

        old_run_fast_model = app.run_fast_model
        app.run_fast_model = forbidden_model
        try:
            for text, expected in (
                ("多脑架构什么状态", "收到，我在处理"),
                ("多模型进程状态是什么", "眼镜快答模型"),
                ("制造脑的进毒", "制造脑"),
                ("以前的图片，查看我眼前的图片", "没有收到图片"),
                ("查看一下本地电脑什么状态", "本地大脑正常"),
                ("任务池进度怎么样", "本地大脑正常"),
                ("最近两个任务进度", "本地大脑正常"),
                ("帮我看一下打印机状态", "制造脑"),
            ):
                chunks = [chunk async for chunk in app.stream_answer(_text_payload(text, message_id=f"msg-{hash(text)}"))]
                answer = _visible_answer(_decode_sse(chunks))
                self.assertIn(expected, answer)
        finally:
            app.run_fast_model = old_run_fast_model

    async def test_model_long_markdown_is_clamped_for_glasses_voice(self):
        long_markdown = "# 标题\n\n| 项 | 值 |\n|---|---|\n" + "这是很长的解释。" * 80

        async def long_model(_prompt: str) -> str:
            return long_markdown

        old_run_fast_model = app.run_fast_model
        app.run_fast_model = long_model
        try:
            chunks = [chunk async for chunk in app.stream_answer(_text_payload("详细解释一下人工智能发展史"))]
        finally:
            app.run_fast_model = old_run_fast_model

        answer = _visible_answer(_decode_sse(chunks))
        self.assertLessEqual(len(answer), 260, "glasses voice answer should be hard-clamped after model output, not only prompt-instructed")
        self.assertNotIn("| 项 |", answer)
        self.assertNotIn("|---|", answer)
        self.assertIn("需要长内容", answer)

    def test_missing_user_id_task_drafts_are_not_shared_by_agent_id(self):
        payload_a = _text_payload("帮我创建任务，研究眼镜入口", user_id=None, message_id="anonymous-a")
        payload_b = _text_payload("确认执行", user_id=None, message_id="anonymous-b")

        handled_a, answer_a = app.handle_task_dialogue(app.extract_user_text(payload_a), app.session_key_for(payload_a))
        handled_b, answer_b = app.handle_task_dialogue(app.extract_user_text(payload_b), app.session_key_for(payload_b))

        self.assertTrue(handled_a)
        self.assertIn("任务草稿", answer_a)
        self.assertFalse(handled_b, "another anonymous request must not confirm a draft created by a different message/session")
        self.assertFalse(Path(app.ROKID_UPGRADE_QUEUE_PATH).exists())

    def test_capability_text_is_voice_menu_with_examples_and_no_technical_jargon(self):
        answer = app.build_capability_text()
        self.assertLessEqual(len(answer), 120)
        for phrase in ("短问答", "今天任务", "日报", "记一下", "后台进度"):
            self.assertIn(phrase, answer)
        for forbidden in ("L0", "L1", "Intent Ledger", "SSE"):
            self.assertNotIn(forbidden, answer)


if __name__ == "__main__":
    unittest.main()
