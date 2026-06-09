# SSOT Violation: Competing Task Pools

## Anti-pattern

Creating a new task pool (e.g., `task_pool.py` in Edge Worker) when one already exists (`brain_task_orchestrator.py` + `kanban.db`) violates Single Source of Truth.

## Symptoms

- Two independent task pools with different storage
- State divergence: pool A shows `pending=7`, pool B shows `pending=0`
- No synchronization mechanism
- User asks "为什么还有X个pending任务" pointing at the original pool while the new pool claims zero

## Root cause

Building a distributed worker (Edge Worker, remote executor, agent node) with its own task creation/management instead of treating it as a pure execution layer.

## Correct architecture

```
Local Brain (Decision Layer) — SSOT
├── brain_task_orchestrator.py
├── kanban.db
├── Task creation, assignment, state transitions
└── Proof/evidence governance

Edge Workers (Execution Layer) — stateless executors
├── Receive task from brain
├── Execute task
├── Return result to brain
└── No independent task storage
```

## Rules

1. **Only one task pool exists**: `brain_task_orchestrator.py` + `kanban.db`
2. **Edge Workers are execution-only**: they fetch tasks, execute, report results
3. **No local task creation on workers**: workers do not add/assign/transition tasks
4. **State sync is one-directional**: brain → worker (task), worker → brain (result)
5. **Before building any new task management**: check if `brain_task_orchestrator.py` already covers it

## Detection checklist

Before creating a new task pool class/module:
- [ ] Does `brain_task_orchestrator.py` already manage tasks?
- [ ] Does `kanban.db` already store task state?
- [ ] Would this create two sources of truth for task status?
- [ ] Can the new component be a pure executor instead?

If any answer is yes → do not create a new task pool. Build an adapter/executor instead.

## Example: Edge Worker integration (correct pattern)

```python
# CORRECT: Edge Worker as executor
class EdgeWorker:
    def __init__(self, brain_url):
        self.brain_url = brain_url
    
    def execute_next_task(self):
        # Fetch from brain (SSOT)
        task = requests.get(f"{self.brain_url}/api/tasks/next").json()
        # Execute
        result = self._run(task)
        # Report back to brain
        requests.post(f"{self.brain_url}/api/tasks/{task['id']}/result", json=result)
```

```python
# WRONG: Edge Worker with own task pool
class EdgeWorker:
    def __init__(self):
        self.task_pool = TaskPool()  # ← competing SSOT!
    
    def add_task(self, ...):  # ← should not exist on worker
        self.task_pool.add_task(...)
```

## Recovery

If a competing task pool was already created:
1. Identify which pool is the canonical SSOT (usually the original one)
2. Migrate any unique tasks from the competing pool to SSOT
3. Delete the competing task pool module
4. Replace with an executor/adapter that calls the SSOT's API
5. Verify: only one source of truth for task state

## Concrete implementation: Unified Task Pool Adapter

When the SSOT violation is detected and needs recovery, the correct implementation has three layers:

### Layer 1: Unified Task Pool Adapter (`unified_task_pool.py`)
```python
class UnifiedTaskPool:
    """Delegates to brain as SSOT, never stores tasks locally"""
    def __init__(self, brain_orchestrator):
        self.brain = brain_orchestrator  # SSOT reference
    
    def add_task(self, task_type, params, priority):
        # Always delegate to brain
        return self.brain.create_task({...})
    
    def get_task(self, task_id):
        # Always read from brain
        return self.brain.get_task(task_id)
    
    def update_task_status(self, task_id, status, result=None):
        # Always write to brain
        self.brain.update_task_status(task_id, status, result)
```

### Layer 2: Edge Worker Executor (`edge_worker_executor.py`)
```python
class EdgeWorkerExecutor:
    """Pure executor - no local task storage"""
    def __init__(self, brain_url, worker_id):
        self.brain_url = brain_url
        self.worker_id = worker_id
    
    def execute_task(self, task_id):
        # Fetch from brain (SSOT)
        task = requests.get(f"{self.brain_url}/tasks/{task_id}").json()
        # Execute
        result = self._execute(task)
        # Report back to brain
        requests.post(f"{self.brain_url}/tasks/{task_id}/result", json={
            "result": result, "status": "completed", "worker_id": self.worker_id
        })
        return result
```

### Layer 3: Unified API (`unified_api.py`)
```python
# Single REST API that delegates to UnifiedTaskPool
# GET  /tasks           → list tasks
# GET  /tasks/<id>      → get task
# POST /tasks           → create task
# POST /tasks/<id>/result → update result
# GET  /metrics         → pool metrics
```

### File locations
- Implementation: `~/hermes-edge-worker/unified_task_pool.py`
- Implementation: `~/hermes-edge-worker/edge_worker_executor.py`
- Implementation: `~/hermes-edge-worker/unified_api.py`
- Architecture doc: `~/hermes-edge-worker/UNIFIED-TASK-POOL-ARCHITECTURE.md`

## Multi-model architecture discussion pattern

When facing a non-trivial architecture decision (SSOT violations, distributed system design, data consistency), use a multi-model discussion approach:

1. **Define model roles**: e.g., Claude Code (architecture/safety), DeepSeek (engineering/performance), MiMo (algorithms/academic)
2. **Each model argues from its perspective**: theoretical framework, engineering implementation, academic support
3. **Each model cites core works**: authoritative books/papers that support the argument
4. **Synthesize into final agreement**: consensus points, implementation plan, performance targets

Core works for SSOT/data architecture:
- 《Designing Data-Intensive Applications》(Kleppmann) — data consistency, replication, partitioning
- 《Patterns of Enterprise Application Architecture》(Fowler) — layering, repository, unit of work
- 《Clean Architecture》(Robert C. Martin) — dependency rule, boundary management
- 《Domain-Driven Design》(Eric Evans) — bounded contexts, aggregates, domain events
- 《Microservices Patterns》(Chris Richardson) — saga, CQRS, event sourcing
