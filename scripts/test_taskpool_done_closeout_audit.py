import json
from pathlib import Path

import taskpool_done_closeout_audit as audit


def task_text(*, title: str, body: str, evidence: str = "") -> str:
    return f"""---
type: task
status: done
priority: P1
lane: work
project: test
capability_delta: {title}
acceptance_evidence: test evidence
architecture_target: taskpool
evidence:
  - {evidence}
---
# {title}
{body}
"""


def test_build_report_classifies_plausible_and_suspicious_done(tmp_path):
    (tmp_path / "ok.md").write_text(
        task_text(title="实现 taskpool runner", evidence="command: pytest PASS", body="- [x] Acceptance\n## Proof Log\ncommand: pytest PASS"),
        encoding="utf-8",
    )
    (tmp_path / "bad.md").write_text(
        task_text(title="实现 taskpool runner", evidence="command: py_compile_taskpool PASS", body="- [ ] Acceptance\n- [ ] Real chain\n## Proof Log\ncommand: py_compile_taskpool PASS"),
        encoding="utf-8",
    )

    report = audit.build_report(tmp_path)

    assert report["done_count"] == 2
    assert report["suspicious_count"] == 1
    assert report["suspicious"][0]["id"] == "bad"


def test_strict_cli_fails_when_suspicious_done_exists(tmp_path, capsys):
    (tmp_path / "bad.md").write_text(
        task_text(title="实现 taskpool runner", evidence="command: py_compile_taskpool PASS", body="- [ ] Acceptance\n- [ ] Real chain"),
        encoding="utf-8",
    )

    rc = audit.main(["--tasks-dir", str(tmp_path), "--strict"])

    assert rc == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "FAIL"
    assert payload["suspicious_count"] == 1
