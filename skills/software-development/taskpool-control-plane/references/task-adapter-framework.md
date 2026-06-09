# Task Adapter Framework Pattern

When the taskpool needs to ingest tasks from multiple distinct sources (Lark collections, brain notes, direct user input, GitHub issues, etc.), use the pluggable TaskAdapter framework instead of hard-coding source logic into the orchestrator.

## Architecture

```
task_adapter.py          # Core interface + data models (TaskSource, TaskSpec, CompletionGate, StepTemplate, PreflightResult)
task_registry.py         # Adapter registry (register/get by source name)
task_pipeline.py         # Unified pipeline: execute → observe → check gates → complete
adapters/
  __init__.py            # Auto-registers all adapters
  lark_adapter.py        # Lark task collection adapter
  brain_adapter.py       # Brain markdown note adapter
  direct_adapter.py      # Direct user-input adapter
```

## Key Interfaces

### TaskAdapter (protocol)
Every adapter must implement:
- `source: TaskSource` — enum identifying the source type
- `fetch(project, filters) -> list[TaskSpec]` — pull tasks from source
- `enrich(spec) -> TaskSpec` — add source-specific metadata
- `classify(spec) -> str` — determine task category/lane
- `preflight(spec) -> PreflightResult` — confidence + risk assessment
- `get_step_template(spec) -> StepTemplate` — default execution steps
- `get_completion_gates(spec) -> list[CompletionGate]` — blocking/non-blocking gates
- `on_complete(spec, evidence) -> bool` — post-completion hook

### TaskSpec
Source-agnostic task representation with:
- Core fields: `task_id`, `title`, `description`, `source`, `project`, `priority`, `lane`
- Source-specific fields: `lark_guid`, `lark_comments`, `lark_scope` (for Lark)
- `to_dict()` / `from_dict()` — full serialization (includes source-specific fields)
- `to_observer_dict()` — source-agnostic dict for observer (excludes source-specific fields)

### CompletionGate
```python
CompletionGate(name="build_pass", blocking=True, passed=False, description="Build passes")
```
- `blocking=True` gates must pass before `pipeline.complete()` succeeds
- `passed` is set by the pipeline based on evidence, not by the adapter

## Integration Points

1. **Registry**: `registry = TaskRegistry(); registry.register('lark', LarkAdapter())`
2. **Pipeline**: `pipeline = TaskPipeline()` — auto-discovers adapters
3. **Execute**: `pipeline.execute(spec)` — starts observer
4. **Observe**: `pipeline.observer.observe(task_id, event_type, detail)` — logs steps
5. **Complete**: `pipeline.complete(spec, evidence)` — checks gates, notifies adapter, finishes observer

## Pitfalls

- **Observer.observe() signature**: `(task_id, event_type, detail)` — no `step` parameter. The observer infers steps from the step template, not from observe calls.
- **Pipeline.preflight.check()**: Takes `(task_id, title, description)` individually, not a TaskSpec. This is the old API; the new adapter-based preflight uses `adapter.preflight(spec)`.
- **Gate checking**: `pipeline.complete()` checks gates but does NOT automatically set `gate.passed` from evidence. The adapter's `get_completion_gates()` returns gates with `passed=False`; the pipeline needs a mechanism to evaluate evidence against gates before calling complete.
- **Source-agnostic observer dict**: Use `spec.to_observer_dict()` when writing to observer/progress files. This strips source-specific fields (e.g., `lark_guid`, `lark_comments`) so the observer stays source-agnostic.
- **Adapter auto-registration**: `adapters/__init__.py` should import and register all adapters. New adapters need to be added to this init file.

## Adding a New Source

1. Create `adapters/new_adapter.py` implementing the TaskAdapter protocol
2. Add import to `adapters/__init__.py` and register with `registry.register('new', NewAdapter())`
3. Add `TaskSource.NEW` to the TaskSource enum in `task_adapter.py`
4. Observer, Preflight, Query, Dashboard all work without modification

## Testing Pattern

```python
# Verify adapter interface
adapter = NewAdapter()
assert hasattr(adapter, 'source')
assert hasattr(adapter, 'fetch')
# ... etc

# Verify serialization roundtrip
spec = TaskSpec(source=TaskSource.NEW, ...)
d = spec.to_dict()
spec2 = TaskSpec.from_dict(d)
assert spec2.source == TaskSource.NEW

# Verify observer dict excludes source-specific fields
obs_d = spec.to_observer_dict()
assert 'new_specific_field' not in obs_d
```

## Composite Tasks & Parallel Execution (Dynamic Workflow Migration)

TaskSpec now supports composite tasks with subtasks:

```python
parent = TaskSpec(
    task_id="fix-asset-page", title="Fix Asset Page",
    source=TaskSource.LARK, project="uvisa-app-2.0", priority="P1", lane="work",
    subtasks=[analyze_spec, implement_spec],
    parallelism=2,  # max parallel workers
    convergence_condition="all_agree",  # 'all_agree' | 'majority' | 'threshold:N'
    max_iterations=1,  # convergence loop limit
)
```

Pipeline supports parallel/composite/convergence execution:

```python
pipeline = TaskPipeline()

# Parallel execution
results = list(pipeline.execute_parallel([spec1, spec2, spec3], max_workers=4))

# Composite task (subtasks run per parallelism setting)
result = pipeline.execute_composite(parent_spec)

# Convergence loop (iterate until condition met)
result = pipeline.run_convergence(spec)  # {'status': 'converged', 'iteration': 2, ...}

# Adversarial verification (verifier tries to refute output)
verification = pipeline.adversarial_verify(spec, output)  # {'approved': True/False}
```

Checkpoint/resume for long-running tasks:

```python
from checkpoint_manager import CheckpointManager

cm = CheckpointManager("long-running-task")
cm.save({"step": 3, "progress": "60%", "data": results})
state = cm.resume_from_latest()  # resume after crash
```

## Current File Locations

- `~/.hermes/scripts/task_adapter.py` — core interface (composite task fields: subtasks, parallelism, convergence_condition, max_iterations)
- `~/.hermes/scripts/task_registry.py` — registry
- `~/.hermes/scripts/task_pipeline.py` — pipeline (execute_parallel, execute_composite, run_convergence, adversarial_verify, check_convergence)
- `~/.hermes/scripts/checkpoint_manager.py` — checkpoint save/load/resume for long-running tasks
- `~/.hermes/scripts/adapters/` — adapter implementations
- `~/.hermes/scripts/task_observer.py` — source-observer (refactored)
- `~/.hermes/scripts/task_preflight.py` — adapter-aware preflight (refactored)
- `~/.hermes/scripts/task_progress.py` — step-level progress
- `~/.hermes/scripts/task_query.py` — unified query
- `~/.hermes/scripts/test_adapter_integration.py` — integration tests
- `~/.hermes/scripts/test_dynamic_workflow.py` — dynamic workflow tests (26 tests)
