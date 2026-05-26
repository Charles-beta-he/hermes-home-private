import unittest

import app


def _text_payload(text: str, user_id="runtime-user", message_id: str = "runtime-msg", metadata=None) -> app.RokidRequest:
    return app.RokidRequest(
        message_id=message_id,
        agent_id="hermes-rokid",
        user_id=user_id,
        message=[app.Message(role="user", type="text", text=text)],
        metadata=metadata,
    )


def _text_image_payload(text: str, image_url: str, user_id="runtime-user", message_id: str = "runtime-img", metadata=None) -> app.RokidRequest:
    return app.RokidRequest(
        message_id=message_id,
        agent_id="hermes-rokid",
        user_id=user_id,
        message=[
            app.Message(role="user", type="text", text=text),
            app.Message(role="user", type="image", image_url=image_url),
        ],
        metadata=metadata,
    )


class RouteRuntimeContractTests(unittest.IsolatedAsyncioTestCase):
    def test_runtime_contract_declares_ordered_route_classes_and_side_effect_scopes(self):
        from route_runtime import RUNTIME_ROUTE_CHAIN, route_ids

        ids = route_ids(RUNTIME_ROUTE_CHAIN)

        self.assertEqual(
            ids,
            [
                "text_l0",
                "location_status",
                "device_status",
                "camera_view",
                "sensor_analysis",
                "sensor_result_status",
                "model_process_status",
                "photo_print_confirm",
                "x2d_print_intent",
                "image_placeholder",
                "kanban_view",
                "background_task_control",
                "local_brain_stats_legacy",
                "lingzhu_plugin",
                "high_impact_confirm",
                "task_dialogue",
                "orphan_action_confirmation",
                "model_fallback",
            ],
        )
        side_effects = {route.route_id: route.side_effect_scope for route in RUNTIME_ROUTE_CHAIN}
        self.assertEqual(side_effects["text_l0"], "none")
        self.assertEqual(side_effects["location_status"], "none")
        self.assertEqual(side_effects["device_status"], "none")
        self.assertEqual(side_effects["camera_view"], "none")
        self.assertEqual(side_effects["sensor_analysis"], "background_queue")
        self.assertEqual(side_effects["sensor_result_status"], "none")
        self.assertEqual(side_effects["model_process_status"], "none")
        self.assertEqual(side_effects["photo_print_confirm"], "confirmation_only")
        self.assertEqual(side_effects["x2d_print_intent"], "background_queue")
        self.assertEqual(side_effects["background_task_control"], "session_queue_mutation")
        self.assertEqual(side_effects["lingzhu_plugin"], "confirmation_only")
        self.assertEqual(side_effects["task_dialogue"], "session_draft_mutation")
        self.assertEqual(side_effects["orphan_action_confirmation"], "confirmation_only")
        self.assertEqual(side_effects["model_fallback"], "model_or_l2_enqueue")

    def test_runtime_contract_exposes_handler_requirements_for_stream_refactor(self):
        from route_runtime import RUNTIME_ROUTE_CHAIN

        requirements = {route.route_id: set(route.requires) for route in RUNTIME_ROUTE_CHAIN}

        self.assertEqual(requirements["text_l0"], {"user_text"})
        self.assertEqual(requirements["location_status"], {"payload", "user_text"})
        self.assertEqual(requirements["camera_view"], {"payload", "user_text"})
        self.assertEqual(requirements["sensor_analysis"], {"payload", "user_text"})
        self.assertEqual(requirements["sensor_result_status"], {"user_text"})
        self.assertEqual(requirements["model_process_status"], {"user_text"})
        self.assertEqual(requirements["x2d_print_intent"], {"payload", "user_text", "session_key"})
        self.assertEqual(requirements["kanban_view"], {"user_text", "session_key"})
        self.assertEqual(requirements["background_task_control"], {"user_text", "session_key"})
        self.assertEqual(requirements["lingzhu_plugin"], {"payload", "user_text"})
        self.assertEqual(requirements["orphan_action_confirmation"], {"user_text", "session_key"})
        self.assertEqual(requirements["model_fallback"], {"prompt", "user_text", "session_key"})
        self.assertTrue(all(route.metrics_bucket for route in RUNTIME_ROUTE_CHAIN))

    def test_app_runtime_handlers_cover_declared_route_chain(self):
        from route_runtime import RUNTIME_ROUTE_CHAIN, route_ids

        self.assertEqual(set(app.RUNTIME_ROUTE_HANDLERS), set(route_ids(RUNTIME_ROUTE_CHAIN)))

    async def test_resolve_runtime_route_matches_text_l0_before_device_or_model(self):
        from route_runtime import RouteContext

        payload = _text_payload("你能做什么")
        ctx = RouteContext(
            payload=payload,
            prompt=app.extract_user_prompt(payload),
            user_text=app.extract_user_text(payload),
            session_key=app.session_key_for(payload),
        )

        result = await app.resolve_runtime_route(ctx)

        self.assertTrue(result.handled)
        self.assertEqual(result.route_id, "text_l0")
        self.assertEqual(result.metrics_bucket, "l0_hits")
        self.assertIn("入口脑", result.answer)

    async def test_resolve_runtime_route_preserves_payload_context_route_order(self):
        from route_runtime import RouteContext

        payload = _text_payload(
            "我现在在哪？电量多少？",
            metadata={"context": {"location": "西安高新区", "battery": "88%", "network": "wifi"}},
        )
        ctx = RouteContext(
            payload=payload,
            prompt=app.extract_user_prompt(payload),
            user_text=app.extract_user_text(payload),
            session_key=app.session_key_for(payload),
        )

        result = await app.resolve_runtime_route(ctx)

        self.assertTrue(result.handled)
        self.assertEqual(result.route_id, "location_status")
        self.assertEqual(result.metrics_bucket, "l0_hits")
        self.assertIn("西安高新区", result.answer)

    async def test_camera_view_without_image_is_handled_before_model(self):
        from route_runtime import RouteContext

        payload = _text_payload("现在能看到什么？查看我眼前的图片")
        ctx = RouteContext(
            payload=payload,
            prompt=app.extract_user_prompt(payload),
            user_text=app.extract_user_text(payload),
            session_key=app.session_key_for(payload),
        )

        result = await app.resolve_runtime_route(ctx)

        self.assertTrue(result.handled)
        self.assertEqual(result.route_id, "camera_view")
        self.assertIn("没有收到图片", result.answer)
        self.assertIn("没有开启实时摄像头", result.answer)

    async def test_background_image_analysis_creates_sensor_job_before_generic_background(self):
        from route_runtime import RouteContext
        import tempfile
        from pathlib import Path
        from unittest.mock import patch

        payload = _text_image_payload("后台分析图片", "https://example.com/scene.jpg")
        with tempfile.TemporaryDirectory() as td, patch.dict("os.environ", {"ROKID_SENSOR_JOBS_DIR": td}, clear=False):
            ctx = RouteContext(
                payload=payload,
                prompt=app.extract_user_prompt(payload),
                user_text=app.extract_user_text(payload),
                session_key=app.session_key_for(payload),
            )
            result = await app.resolve_runtime_route(ctx)
            jobs = list(Path(td).glob("vision_*.json"))

        self.assertTrue(result.handled)
        self.assertEqual(result.route_id, "sensor_analysis")
        self.assertIn("后台视觉分析", result.answer)
        self.assertEqual(len(jobs), 1)

    async def test_audio_review_creates_whisper_job_without_requiring_dependency(self):
        from route_runtime import RouteContext
        import tempfile
        from pathlib import Path
        from unittest.mock import patch

        payload = _text_payload("复核语音识别", metadata={"context": {"audio_url": "file:///tmp/voice.wav", "asr_text": "进毒"}})
        with tempfile.TemporaryDirectory() as td, patch.dict("os.environ", {"ROKID_SENSOR_JOBS_DIR": td}, clear=False):
            ctx = RouteContext(
                payload=payload,
                prompt=app.extract_user_prompt(payload),
                user_text=app.extract_user_text(payload),
                session_key=app.session_key_for(payload),
            )
            result = await app.resolve_runtime_route(ctx)
            jobs = list(Path(td).glob("asr_*.json"))

        self.assertTrue(result.handled)
        self.assertEqual(result.route_id, "sensor_analysis")
        self.assertIn("Whisper", result.answer)
        self.assertEqual(len(jobs), 1)

    async def test_sensor_result_status_processes_queue_and_returns_latest_summary(self):
        from route_runtime import RouteContext
        import tempfile
        from pathlib import Path
        from unittest.mock import patch

        image_payload = _text_image_payload("后台分析图片", "https://example.com/scene.jpg")
        with tempfile.TemporaryDirectory() as td:
            jobs = Path(td) / "jobs"
            results = Path(td) / "results"
            with patch.dict("os.environ", {"ROKID_SENSOR_JOBS_DIR": str(jobs), "ROKID_SENSOR_RESULTS_DIR": str(results)}, clear=False):
                app.handle_sensor_analysis_request(image_payload, app.extract_user_text(image_payload))
                payload = _text_payload("传感器复核结果")
                ctx = RouteContext(
                    payload=payload,
                    prompt=app.extract_user_prompt(payload),
                    user_text=app.extract_user_text(payload),
                    session_key=app.session_key_for(payload),
                )
                result = await app.resolve_runtime_route(ctx)
                result_files = list(results.glob("vision_result_*.json"))

        self.assertTrue(result.handled)
        self.assertEqual(result.route_id, "sensor_result_status")
        self.assertIn("最近传感器复核", result.answer)
        self.assertEqual(len(result_files), 1)

    async def test_model_process_status_is_l0_not_model_fallback(self):
        from route_runtime import RouteContext

        payload = _text_payload("多模型进程状态是什么")
        ctx = RouteContext(
            payload=payload,
            prompt=app.extract_user_prompt(payload),
            user_text=app.extract_user_text(payload),
            session_key=app.session_key_for(payload),
        )

        result = await app.resolve_runtime_route(ctx)

        self.assertTrue(result.handled)
        self.assertEqual(result.route_id, "model_process_status")
        self.assertIn("眼镜快答模型", result.answer)
        self.assertIn("后台长任务", result.answer)

    async def test_lingzhu_plugin_native_action_is_clamped_before_high_impact_or_model(self):
        from route_runtime import RouteContext

        async def forbidden_model(prompt: str, user_text: str, session_key: str) -> str:
            raise AssertionError("Lingzhu native plugin route must not reach model fallback")

        old_run_answer_with_budget = app.run_answer_with_budget
        app.run_answer_with_budget = forbidden_model
        try:
            payload = _text_payload("导航到钟楼")
            ctx = RouteContext(
                payload=payload,
                prompt=app.extract_user_prompt(payload),
                user_text=app.extract_user_text(payload),
                session_key=app.session_key_for(payload),
            )
            result = await app.resolve_runtime_route(ctx)
        finally:
            app.run_answer_with_budget = old_run_answer_with_budget

        self.assertTrue(result.handled)
        self.assertEqual(result.route_id, "lingzhu_plugin")
        self.assertIn("灵珠平台插件", result.answer)
        self.assertIn("需要先确认", result.answer)
        self.assertIn("不能声称已经执行", result.answer)

    async def test_lingzhu_plugin_uses_platform_receipt_when_present(self):
        from route_runtime import RouteContext

        payload = _text_payload(
            "拍照",
            metadata={"context": {"pluginReceipts": {"photo": {"status": "success", "id": "photo-r1"}}}},
        )
        ctx = RouteContext(
            payload=payload,
            prompt=app.extract_user_prompt(payload),
            user_text=app.extract_user_text(payload),
            session_key=app.session_key_for(payload),
        )

        result = await app.resolve_runtime_route(ctx)

        self.assertTrue(result.handled)
        self.assertEqual(result.route_id, "lingzhu_plugin")
        self.assertIn("收到灵珠平台插件回执", result.answer)
        self.assertIn("photo-r1", result.answer)
        self.assertNotIn("已拍照", result.answer)

    async def test_lingzhu_weather_without_receipt_uses_readonly_payload_context(self):
        from route_runtime import RouteContext

        payload = _text_payload(
            "现在天气怎么样",
            metadata={
                "weather": "当前天气雾，24度",
                "location": "中国浙江省杭州市西湖区",
                "current_time": "2026-05-27 10:30:00",
            },
        )
        ctx = RouteContext(
            payload=payload,
            prompt=app.extract_user_prompt(payload),
            user_text=app.extract_user_text(payload),
            session_key=app.session_key_for(payload),
        )

        result = await app.resolve_runtime_route(ctx)

        self.assertTrue(result.handled)
        self.assertEqual(result.route_id, "lingzhu_plugin")
        self.assertIn("当前天气雾", result.answer)
        self.assertIn("只读天气上下文", result.answer)
        self.assertNotIn("当前没有插件回执", result.answer)

    async def test_lingzhu_calculator_without_receipt_uses_local_safe_calculator(self):
        from route_runtime import RouteContext

        payload = _text_payload("帮我算 23*19+7")
        ctx = RouteContext(
            payload=payload,
            prompt=app.extract_user_prompt(payload),
            user_text=app.extract_user_text(payload),
            session_key=app.session_key_for(payload),
        )

        result = await app.resolve_runtime_route(ctx)

        self.assertTrue(result.handled)
        self.assertEqual(result.route_id, "lingzhu_plugin")
        self.assertIn("计算结果", result.answer)
        self.assertIn("444", result.answer)
        self.assertNotIn("当前没有插件回执", result.answer)

    async def test_lingzhu_high_risk_plugin_without_receipt_still_fails_closed(self):
        from route_runtime import RouteContext

        payload = _text_payload("支付宝付款 12 元")
        ctx = RouteContext(
            payload=payload,
            prompt=app.extract_user_prompt(payload),
            user_text=app.extract_user_text(payload),
            session_key=app.session_key_for(payload),
        )

        result = await app.resolve_runtime_route(ctx)

        self.assertTrue(result.handled)
        self.assertEqual(result.route_id, "lingzhu_plugin")
        self.assertIn("支付是高风险动作", result.answer)
        self.assertIn("不能声称", result.answer)

    async def test_resolve_runtime_route_uses_async_model_fallback_as_terminal_route(self):
        from route_runtime import RouteContext

        old_run_answer_with_budget = app.run_answer_with_budget

        async def fake_model(prompt: str, user_text: str, session_key: str) -> str:
            return f"模型回答:{user_text}:{bool(prompt)}:{bool(session_key)}"

        app.run_answer_with_budget = fake_model
        try:
            payload = _text_payload("普通闲聊问题")
            ctx = RouteContext(
                payload=payload,
                prompt=app.extract_user_prompt(payload),
                user_text=app.extract_user_text(payload),
                session_key=app.session_key_for(payload),
            )

            result = await app.resolve_runtime_route(ctx)
        finally:
            app.run_answer_with_budget = old_run_answer_with_budget

        self.assertTrue(result.handled)
        self.assertEqual(result.route_id, "model_fallback")
        self.assertEqual(result.metrics_bucket, "model_fallbacks")
        self.assertIn("模型回答:普通闲聊问题", result.answer)
    async def test_orphan_action_confirmation_is_rejected_before_model_fallback(self):
        from route_runtime import RouteContext

        async def forbidden_model(prompt: str, user_text: str, session_key: str) -> str:
            raise AssertionError("orphan confirmation must not reach model fallback")

        old_run_answer_with_budget = app.run_answer_with_budget
        app.run_answer_with_budget = forbidden_model
        try:
            payload = _text_payload("确认执行这个动作。")
            ctx = RouteContext(
                payload=payload,
                prompt=app.extract_user_prompt(payload),
                user_text=app.extract_user_text(payload),
                session_key=app.session_key_for(payload),
            )
            result = await app.resolve_runtime_route(ctx)
        finally:
            app.run_answer_with_budget = old_run_answer_with_budget

        self.assertTrue(result.handled)
        self.assertEqual(result.route_id, "orphan_action_confirmation")
        self.assertIn("没有待确认", result.answer)
        self.assertIn("不能直接执行", result.answer)

    def test_voice_safe_answer_rewrites_confirmed_execution_claims(self):
        answer = app.make_voice_safe_answer("好的，已确认执行。")

        self.assertNotIn("已确认执行", answer)
        self.assertIn("需要你确认", answer)
        self.assertIn("明确动作编号", answer)


if __name__ == "__main__":
    unittest.main()
