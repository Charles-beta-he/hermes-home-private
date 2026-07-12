import importlib.util
import json
from pathlib import Path


SCRIPT = Path(__file__).with_name("taskpool_drain_until_empty.py")


def load_module():
    spec = importlib.util.spec_from_file_location("taskpool_drain_until_empty_tested", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_invocation_fails_closed_without_read_or_write(monkeypatch, capsys):
    module = load_module()
    calls = []
    monkeypatch.setattr(module, "append", lambda event: calls.append(("append", event)))
    monkeypatch.setattr(module, "list_state", lambda: calls.append(("list_state", None)))

    rc = module.main([])

    assert rc == 2
    assert calls == []
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "DENIED"
    assert payload["reason"] == "explicit_execute_required"


def test_explicit_execute_empty_pool_stops_without_mutation(monkeypatch, tmp_path, capsys):
    module = load_module()
    events = []
    monkeypatch.setattr(module, "LOG", tmp_path / "drain.jsonl")
    monkeypatch.setattr(module, "append", lambda event: events.append(dict(event)))
    monkeypatch.setattr(module, "list_state", lambda: ([], {}, 0))

    def fake_run(command, timeout=300):
        if "worker-jobs" in command:
            return 0, {"alive_count": 0}
        if "selfcheck" in command:
            return 0, {"status": "PASS", "failures": [], "warnings": []}
        raise AssertionError(f"unexpected command: {command}")

    monkeypatch.setattr(module, "run", fake_run)
    rc = module.main(["--execute", "--max-cycles", "1"])

    assert rc == 0
    assert [event["event"] for event in events] == ["start", "state", "stop"]
    assert not any(event.get("event") == "step" for event in events)
    payload = json.loads(capsys.readouterr().out)
    assert payload["reason"] == "empty"


def test_task_id_is_shell_quoted_for_multimodel_step():
    module = load_module()
    task_id = "task'; touch /tmp/should-not-run; echo '"
    quoted = module.shell_task_argument(task_id)
    assert quoted != task_id
    assert "touch /tmp/should-not-run" in quoted
    assert quoted.startswith("'") and quoted.endswith("'")
