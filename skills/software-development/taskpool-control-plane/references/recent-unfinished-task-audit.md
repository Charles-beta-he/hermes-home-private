# Recent unfinished task audit fallback

Scope/applicability: Hermes local taskpool/control-plane inventories only. This reference applies to read-only inspection of the local brain task-note store and kanban projection. It is not a general project-management rule and must not be applied to unrelated repositories or non-Hermes task systems.

Anti-conditions:
- Do not use this as a lifecycle mutation recipe.
- Do not use this to bypass proof gates or blocked-task governance.
- Do not treat the local paths below as portable outside the active Hermes profile/host.

## Trigger

Use this when the user asks to inspect recent unfinished tasks and the normal taskpool commands are slow, empty, or inconsistent:

- the canonical dashboard/list/next commands time out under a short bounded timeout;
- the dynamic runner exits successfully but prints no payload;
- the user asked for a quick inventory rather than task advancement.

## Safe read-only fallback

1. Try canonical commands first with bounded timeouts and record their health.
2. If they fail or stall, directly scan the local brain task markdown directory read-only:
   - default active-profile path: `~/Documents/brain/05-实践与项目/tasks`;
   - parse only YAML frontmatter fields when present;
   - exclude terminal statuses such as `done`, `archived`, `cancelled`;
   - keep nonstandard statuses (`active`, `ready`, `review`, `unknown`, `current`) visible instead of normalizing them away;
   - sort by file mtime for “recent”.
3. Query the active profile kanban projection read-only:
   - default active-profile DB: `~/.hermes/kanban.db`;
   - summarize `tasks.status`;
   - list recent unfinished rows with projection fields such as worker pid, claim expiry, heartbeat, and spawn error when present.
4. Report the two stores separately:
   - brain markdown is the lifecycle/task-note source;
   - kanban DB is a projection/worker surface and can legitimately disagree.
5. If large frontmatter or YAML escaping is visible, flag it as a likely observability/performance issue, not as task completion evidence.

## Pitfalls

- Do not declare “no unfinished tasks” from kanban DB alone; brain markdown may still contain pending work.
- Do not mutate task files during an inventory.
- Do not full-load every task note through generic YAML when a quick frontmatter field scan is enough; large escaped evidence fields can make orchestrator-style parsing slow or timeout.
- Do not collapse `unknown`/`active`/`current` into `pending`; surface them as metadata hygiene items.

## Output shape

Prefer a compact terminal-friendly report:

- canonical command health: timed out / empty / OK;
- current session todo count if available;
- brain markdown unfinished count and status summary;
- top recent unfinished brain tasks with status, priority, lane, project, title, and blocker;
- kanban projection unfinished count and status summary;
- explicit note if brain and kanban disagree.
