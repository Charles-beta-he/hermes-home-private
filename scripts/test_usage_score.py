#!/usr/bin/env python3
"""Regression tests for usage-score semantics."""
from __future__ import annotations

import importlib.util
import json
import os
import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


SCRIPT = Path.home() / ".hermes" / "scripts" / "usage-score.py"


class UsageScoreTests(unittest.TestCase):
    def load_module(self, db_path: str):
        old = os.environ.get("HERMES_ROUTE_DB_PATH")
        os.environ["HERMES_ROUTE_DB_PATH"] = db_path
        try:
            spec = importlib.util.spec_from_file_location("usage_score_under_test", SCRIPT)
            assert spec and spec.loader
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            mod.read_jsonl = lambda path: []
            mod.cron_stats = lambda: {
                "score_raw": 1.0,
                "ok": 1,
                "total": 1,
                "recent_24h": 1,
                "pending_first_run": 0,
                "bad": 0,
                "source": "test",
            }
            return mod
        finally:
            if old is None:
                os.environ.pop("HERMES_ROUTE_DB_PATH", None)
            else:
                os.environ["HERMES_ROUTE_DB_PATH"] = old

    def make_db(self, path: str):
        conn = sqlite3.connect(path)
        conn.execute(
            """
            CREATE TABLE route_outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                skill TEXT NOT NULL,
                task_class TEXT NOT NULL DEFAULT '',
                route TEXT NOT NULL DEFAULT '',
                verdict TEXT NOT NULL DEFAULT 'unknown',
                duration_s REAL DEFAULT 0,
                tokens_in INTEGER DEFAULT 0,
                tokens_out INTEGER DEFAULT 0,
                task_id TEXT DEFAULT '',
                model_chain TEXT DEFAULT '',
                cost_usd REAL DEFAULT 0,
                error TEXT DEFAULT '',
                is_synthetic INTEGER DEFAULT 0,
                chain_id TEXT
            )
            """
        )
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        for model in ["gpt-5.5", "claude-fable-5", "deepseek-v4-pro", "mimo-v2.5-pro"]:
            conn.execute(
                "INSERT INTO route_outcomes (ts, skill, route, verdict, duration_s, tokens_in, tokens_out, model_chain, cost_usd, is_synthetic) VALUES (?,?,?,?,?,?,?,?,?,0)",
                (ts, "probe", "probe:smoke", "pass", 1.0, 10, 10, model, 0.001),
            )
        for route in ["hook:terminal", "hook:read_file", "hook:patch"]:
            conn.execute(
                "INSERT INTO route_outcomes (ts, skill, route, verdict, duration_s, tokens_in, tokens_out, model_chain, cost_usd, is_synthetic) VALUES (?,?,?,?,?,?,?,?,?,0)",
                (ts, "hook", route, "pass", 0.0, 0, 0, "gpt-5.5", 0.0),
            )
        conn.commit()
        conn.close()

    def test_route_diversity_excludes_hook_bookkeeping_rows(self):
        with tempfile.TemporaryDirectory() as td:
            db = str(Path(td) / "route_outcomes.db")
            self.make_db(db)
            mod = self.load_module(db)
            data = mod.compute()
            rd = data["components"]["route_diversity"]
            self.assertEqual(rd["score"], 15)
            self.assertEqual(rd["evaluated_rows"], 4)
            self.assertEqual(rd["excluded_hook_rows"], 3)
            self.assertEqual(list(rd["routes"].keys()), ["probe:smoke"])

    def test_compute_splits_operational_health_from_evidence_readiness(self):
        with tempfile.TemporaryDirectory() as td:
            db = str(Path(td) / "route_outcomes.db")
            self.make_db(db)
            mod = self.load_module(db)
            data = mod.compute()
            self.assertIn("semantic_grades", data)
            self.assertEqual(data["semantic_grades"]["operational_health"]["grade"], "A")
            self.assertEqual(data["semantic_grades"]["operational_health"]["cron_bad_count"], 0)
            self.assertIn("evidence_readiness", data["semantic_grades"])
            self.assertIn("interpretation", data)
            self.assertIn("runtime", data["interpretation"])

    def test_certified_discussion_results_count_as_ratification_corpus(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            db = str(root / "route_outcomes.db")
            self.make_db(db)
            tick = root / "tick-20260506-170132"
            tick.mkdir()
            (tick / "discussion_result.json").write_text(
                '{"status":"certified","models_consulted":["gpt-5.5","mimo-v2.5-pro","deepseek-v4-pro"],"truth_assessment":{"truth_status":"grounded","can_certify_truth":true}}'
            )
            mod = self.load_module(db)
            mod.H = root
            data = mod.compute()
            self.assertEqual(data["components"]["ratification_corpus"]["count_7d"], 1)
            self.assertIn("discussion_result", data["components"]["ratification_corpus"]["sources"])
            self.assertNotIn("ratification_corpus", data["semantic_grades"]["evidence_readiness"]["missing"])

    def test_executed_ensemble_votes_count_as_evidence_readiness(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            db = str(root / "route_outcomes.db")
            self.make_db(db)
            logs = root / "logs"
            logs.mkdir()
            mod = self.load_module(db)
            ts = mod.NOW.strftime("%Y-%m-%dT%H:%M:%SZ")
            (logs / "ensemble-votes.jsonl").write_text(
                f'{{"ts":"{ts}","execute":true,"total_voters":3,'
                '"models":["gpt-5.5","claude-fable-5","mimo-v2.5-pro"]}\n'
            )
            mod.H = root
            mod.ENSEMBLE = logs / "ensemble-votes.jsonl"
            mod.read_jsonl = lambda path: [json.loads((logs / "ensemble-votes.jsonl").read_text())] if Path(path) == mod.ENSEMBLE else []
            data = mod.compute()
            self.assertEqual(data["components"]["ensemble_executed"]["count_7d"], 1)
            self.assertGreater(data["components"]["ensemble_executed"]["score"], 0)
            self.assertNotIn("ensemble_executed", data["semantic_grades"]["evidence_readiness"]["missing"])

    def test_usage_score_daily_wrapper_records_timeout_and_degraded_receipts(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            wrapper_path = Path.home() / ".hermes" / "scripts" / "usage-score-daily-wrapper.py"
            spec = importlib.util.spec_from_file_location("usage_score_daily_wrapper_under_test", wrapper_path)
            assert spec and spec.loader
            wrapper = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(wrapper)

            wrapper.H = root
            wrapper.SCRIPT = root / "scripts" / "usage-score.py"
            wrapper.STATE = root / "state" / "usage-score.json"
            wrapper.DEPRECATED_STATE = root / "scripts" / "usage-score.json"
            wrapper.LOG = root / "logs" / "usage-score-daily-wrapper.jsonl"
            wrapper.STATE.parent.mkdir(parents=True)
            wrapper.STATE.write_text(json.dumps({"score": 72.26, "grade": "B", "ts": "2026-07-18T17:01:33Z"}))

            class TimeoutRun:
                stdout = "partial stdout"
                stderr = "partial stderr"

            def timeout_run(*args, **kwargs):
                raise wrapper.subprocess.TimeoutExpired(cmd=["usage-score.py"], timeout=wrapper.TIMEOUT, output="partial stdout", stderr="partial stderr")

            old_run = wrapper.subprocess.run
            wrapper.subprocess.run = timeout_run
            try:
                self.assertEqual(wrapper.main(), 0)
            finally:
                wrapper.subprocess.run = old_run

            timeout_rec = json.loads(wrapper.LOG.read_text().splitlines()[-1])
            self.assertEqual(timeout_rec["status"], "timeout_recorded")
            self.assertTrue(timeout_rec["run"]["timeout"])
            self.assertEqual(timeout_rec["run"]["returncode"], 124)
            self.assertTrue(timeout_rec["usage"]["parse_ok"])

            class FailedProcess:
                returncode = 7
                stdout = "bad stdout"
                stderr = "bad stderr"

            wrapper.subprocess.run = lambda *args, **kwargs: FailedProcess()
            try:
                self.assertEqual(wrapper.main(), 0)
            finally:
                wrapper.subprocess.run = old_run

            degraded_rec = json.loads(wrapper.LOG.read_text().splitlines()[-1])
            self.assertEqual(degraded_rec["status"], "degraded_recorded")
            self.assertFalse(degraded_rec["run"]["timeout"])
            self.assertEqual(degraded_rec["run"]["returncode"], 7)
            self.assertTrue(degraded_rec["usage"]["parse_ok"])

    def test_usage_score_daily_wrapper_proposes_advisory_when_self_evolution_closure_zero(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            wrapper_path = Path.home() / ".hermes" / "scripts" / "usage-score-daily-wrapper.py"
            spec = importlib.util.spec_from_file_location("usage_score_daily_wrapper_under_test", wrapper_path)
            assert spec and spec.loader
            wrapper = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(wrapper)

            wrapper.H = root
            wrapper.SCRIPT = root / "scripts" / "usage-score.py"
            wrapper.STATE = root / "state" / "usage-score.json"
            wrapper.DEPRECATED_STATE = root / "scripts" / "usage-score.json"
            wrapper.LOG = root / "logs" / "usage-score-daily-wrapper.jsonl"
            wrapper.STATE.parent.mkdir(parents=True)
            wrapper.STATE.write_text(json.dumps({
                "score": 78.22,
                "grade": "B",
                "ts": "2026-07-21T17:01:23Z",
                "components": {
                    "self_evolution_closure": {
                        "score": 0.0,
                        "max": 10,
                        "closure_events_14d": 0,
                    }
                },
            }))

            class SuccessfulProcess:
                returncode = 0
                stdout = "usage score ok"
                stderr = ""

            old_run = wrapper.subprocess.run
            wrapper.subprocess.run = lambda *args, **kwargs: SuccessfulProcess()
            try:
                self.assertEqual(wrapper.main(), 0)
            finally:
                wrapper.subprocess.run = old_run

            rec = json.loads(wrapper.LOG.read_text().splitlines()[-1])
            self.assertEqual(rec["status"], "ok")
            self.assertTrue(rec["usage"]["parse_ok"])
            self.assertEqual(rec["discussion_result"]["status"], "advisory_action_proposed")
            self.assertEqual(rec["discussion_result"]["trigger"], "self_evolution_closure_zero")
            self.assertEqual(rec["discussion_result"]["root_cause_class"], "verifier_gap")
            self.assertLessEqual(
                {"swap_model", "raise_tier", "lower_tier", "duplicate_cron"},
                set(rec["discussion_result"]["forbidden_actions"]),
            )

    def test_usage_score_daily_cron_contract_is_local_no_agent_wrapper(self):
        job = {
            "name": "usage-score-daily",
            "script": "usage-score-daily-wrapper.py",
            "no_agent": True,
            "enabled": True,
            "deliver": "local",
            "enabled_toolsets": ["terminal", "file"],
            "schedule": {"kind": "cron", "expr": "0 1 * * *"},
        }
        self.assertEqual(job["name"], "usage-score-daily")
        self.assertEqual(job["script"], "usage-score-daily-wrapper.py")
        self.assertTrue(job["no_agent"])
        self.assertTrue(job["enabled"])
        self.assertEqual(job["deliver"], "local")
        self.assertLessEqual(set(job["enabled_toolsets"]), {"terminal", "file"})
        self.assertEqual(job["schedule"]["kind"], "cron")


if __name__ == "__main__":
    unittest.main(verbosity=2)
