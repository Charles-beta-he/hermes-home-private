import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import app
from rokid_bridge.sensor_context import build_sensor_context, create_image_analysis_job, create_whisper_review_job
from rokid_bridge.sensor_worker import process_sensor_queue, summarize_latest_sensor_result


class SensorWorkerTests(unittest.TestCase):
    def test_processes_vision_job_into_fail_soft_result_and_marks_job_done(self):
        payload = app.RokidRequest(
            message_id="vision-worker-msg",
            agent_id="hermes-rokid",
            user_id="sensor-user",
            message=[
                app.Message(role="user", type="text", text="后台分析图片"),
                app.Message(role="user", type="image", image_url="https://example.com/photo.jpg"),
            ],
            metadata={"context": {"location": "西安"}},
        )
        with tempfile.TemporaryDirectory() as td:
            jobs = Path(td) / "jobs"
            results = Path(td) / "results"
            with patch.dict("os.environ", {"ROKID_SENSOR_JOBS_DIR": str(jobs), "ROKID_SENSOR_RESULTS_DIR": str(results)}, clear=False):
                job_path = create_image_analysis_job(build_sensor_context(payload), question="后台分析图片")
                processed = process_sensor_queue(limit=5)
                job = json.loads(job_path.read_text(encoding="utf-8"))
                result_paths = list(results.glob("vision_result_*.json"))
                self.assertEqual(len(result_paths), 1)
                result = json.loads(result_paths[0].read_text(encoding="utf-8"))

        self.assertEqual(len(processed), 1)
        self.assertEqual(job["status"], "processed")
        self.assertEqual(result["schema"], "vision_analysis_result_v1")
        self.assertEqual(result["source_job"], job_path.name)
        self.assertEqual(result["status"], "adapter_unavailable")
        self.assertEqual(result["adapter_status"]["vlm"], "unavailable")
        self.assertTrue(result["adapter_status"]["no_stub_fallback"])
        self.assertNotIn("https://example.com/photo.jpg", json.dumps(result, ensure_ascii=False))
        self.assertEqual(result["image_refs"][0]["uri_hash"], result["image_access_proofs"][0]["uri_hash"])
        self.assertTrue(result["fail_soft"])

    def test_processes_asr_job_and_generates_text_correction_candidates_without_whisper(self):
        payload = app.RokidRequest(
            message_id="asr-worker-msg",
            agent_id="hermes-rokid",
            user_id="sensor-user",
            message=[app.Message(role="user", type="text", text="复核语音识别")],
            metadata={"context": {"audio_url": "file:///tmp/voice.wav", "asr_text": "进毒"}},
        )
        with tempfile.TemporaryDirectory() as td:
            jobs = Path(td) / "jobs"
            results = Path(td) / "results"
            with patch.dict("os.environ", {"ROKID_SENSOR_JOBS_DIR": str(jobs), "ROKID_SENSOR_RESULTS_DIR": str(results)}, clear=False):
                job_path = create_whisper_review_job(build_sensor_context(payload))
                processed = process_sensor_queue(limit=5)
                job = json.loads(job_path.read_text(encoding="utf-8"))
                result_paths = list(results.glob("asr_result_*.json"))
                self.assertEqual(len(result_paths), 1)
                result = json.loads(result_paths[0].read_text(encoding="utf-8"))

        self.assertEqual(len(processed), 1)
        self.assertEqual(job["status"], "processed")
        self.assertEqual(result["schema"], "asr_review_result_v1")
        self.assertEqual(result["recognized_text"], "进毒")
        self.assertIn("进度", result["correction_candidates"])
        self.assertTrue(result["fail_soft"])

    def test_queue_processing_is_idempotent_and_latest_summary_is_voice_safe(self):
        payload = app.RokidRequest(
            message_id="summary-worker-msg",
            agent_id="hermes-rokid",
            user_id="sensor-user",
            message=[app.Message(role="user", type="text", text="复核语音识别")],
            metadata={"context": {"audio_url": "file:///tmp/voice.wav", "asr_text": "装太"}},
        )
        with tempfile.TemporaryDirectory() as td:
            jobs = Path(td) / "jobs"
            results = Path(td) / "results"
            with patch.dict("os.environ", {"ROKID_SENSOR_JOBS_DIR": str(jobs), "ROKID_SENSOR_RESULTS_DIR": str(results)}, clear=False):
                create_whisper_review_job(build_sensor_context(payload))
                first = process_sensor_queue(limit=5)
                second = process_sensor_queue(limit=5)
                summary = summarize_latest_sensor_result()

        self.assertEqual(len(first), 1)
        self.assertEqual(second, [])
        self.assertIn("最近传感器复核", summary)
        self.assertIn("状态", summary)
        self.assertNotIn("已执行", summary)


if __name__ == "__main__":
    unittest.main()
