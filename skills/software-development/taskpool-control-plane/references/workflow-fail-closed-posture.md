# Workflow fail-closed posture activation

Applicability: Hermes-owned Workflow Kernel / Control Tower work after runtime readiness, broader-adapter contracts, remaining terminal gates, Phase-G candidate backlog, and publication terminal summary already exist. Use when the user asks to “开启 fail-closed”, “稳定架构”, or “补充 fail-closed 完善项” without granting external side-effect authority.

Anti-conditions: do not use this pattern to enable real sends, publication apply, generic adapter write-through, taskpool enqueue, lifecycle mutation, credential/model generation changes, or executor activation. Those still require exact target/payload/idempotency/rollback/human authorization gates.

## Target posture

“Fail-closed enabled” means the safe-default posture is explicitly observable, not that any dangerous executor is opened.

Expected aggregate readback:

```text
status=FAIL_CLOSED_POSTURE_ENABLED
fail_closed_enabled=true
forbidden_enabled_observations=[]
external_side_effects_enabled=false
unattended_dispatch_enabled=false
publication_apply_enabled=false
generic_adapter_write_through_enabled=false
taskpool_enqueue_enabled=false
executor_enabled=false
```

## Recommended landing sequence

1. Compile a local/read-only posture artifact that aggregates existing evidence sources:
   - runtime readiness or auto-enabled runtime summary;
   - broader adapter operation contract;
   - remaining gates terminal index;
   - Phase-G optimization backlog projection;
   - publication governance terminal summary.
2. Treat missing sources or any forbidden true flag as degraded, not enabled.
3. Persist JSON + Markdown under a private evidence directory such as:

```text
docs/private/workflow-kernel-fail-closed-posture/
```

4. Expose it through Control Tower as `workflow_kernel_control_tower.fail_closed_posture`.
5. Add tests for both paths:
   - current artifacts -> `FAIL_CLOSED_POSTURE_ENABLED`;
   - missing source or forbidden true flag -> degraded/fail-closed disabled.
6. Verify with focused tests plus live/Python Control Tower readback.
7. Commit the child repo slice first, then the parent gitlink pointer; leave unrelated runtime/worktree dirtiness unstaged.
8. Record a mission stage report if the work belongs to a governed mission.

## Verification checklist

```bash
python3 -m py_compile hermes_cli/control_tower.py scripts/workflow_fail_closed_posture.py
./scripts/run_tests.sh \
  tests/scripts/test_workflow_fail_closed_posture.py \
  tests/hermes_cli/test_control_tower_snapshot.py \
  tests/plugins/test_control_tower_dashboard_plugin.py
```

Read back:

```python
from hermes_cli.control_tower import build_snapshot
build_snapshot()["workflow_kernel_control_tower"]["fail_closed_posture"]
```

If the dashboard is running from an older backend process, restart only the dashboard process and re-read `/api/plugins/control-tower/snapshot`; do not restart gateway/message delivery casually.

## Pitfalls

- Do not equate `fail_closed_enabled=true` with permission to execute. It is a posture/guardrail projection.
- Do not let a runtime auto-enabled status override external-dispatch gates. Runtime readiness and external side-effect authority are separate layers.
- Do not stage unrelated dirty runtime artifacts or broad skill/doc changes just because the parent repo shows the submodule as modified.
- Do not store this as memory; it is a reusable procedure and belongs in the control-plane skill/reference.
