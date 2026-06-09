# External skill package → Hermes brain overlay

Use this pattern when the user asks Hermes to gain a capability from an external Agent Skills package or repo, especially when it should become a governed local brain rather than a one-off note.

## Workflow

1. Load `hermes-agent` and any relevant taskpool/control-plane skill before touching the brain registry.
2. Inspect the external repo's runtime contract first:
   - canonical `SKILL.md`
   - configuration docs
   - engine/scripts and diagnostics
   - host assumptions such as slash-command UX vs direct CLI fallback
3. Inspect existing local brain structure before creating anything:
   - `~/.hermes/brains/registry.yaml`
   - similar `~/.hermes/brains/<brain>/brain.yaml`
   - current `brainctl.py` routing behavior if the registry route is keyword-backed
4. Add the capability as a class-level brain overlay, not as an isolated copied repo:
   - create `~/.hermes/brains/<capability>/brain.yaml`
   - register it in `registry.yaml`
   - update `main`/parent brain route hints where appropriate
   - install/copy/symlink the skill package into the Hermes skill library if Hermes should be able to load it by skill name
5. Record the source boundary explicitly:
   - baseline sources that work without credentials
   - optional sources gated by env vars, OAuth, browser cookies, or paid APIs
   - do not claim optional sources are available unless diagnose/config evidence confirms them
6. Create or update a taskpool entry only if it adds durable follow-through. Include dependency order and acceptance evidence. Do not leave a verbal "later" promise.

## Verification checklist

- `brainctl brains validate` passes and shows the new subbrain.
- `brainctl brains route "<representative query>"` resolves to the new brain.
- `skills_list(category=...)` or equivalent discovery finds the installed skill if skill loading is part of the integration.
- The external engine's own `--diagnose` or smoke check runs with the intended interpreter.
- Taskpool `selfcheck`, `proof-check`, and dispatch summary remain green.
- Existing cron/follow-through jobs are enabled, or a new scheduled trigger is created when the user asked for ongoing follow-through.

## Closeout pitfall

For evolution-lane brain integrations, do not force `review -> done` just because deterministic checks passed. The taskpool may require multi-model certification before `done` even when the task was not originally expensive. Correct closeout is:

- write proof-shaped evidence (`proof:`, `artifact:`, `file:`, `brainctl:` prefixes or absolute evidence paths);
- move to `review` after implementation and deterministic verification;
- only move to `done` when the task's completion gate and multi-model status allow it.

If `multimodel_certification_required_before_done` appears, treat it as normal fail-closed governance, not a failure of the integration.

## Example evidence shape

```yaml
evidence:
  - proof:installed <brain> overlay at ~/.hermes/brains/<brain>/brain.yaml and registered registry version <n>
  - artifact:~/.hermes/skills/<category>/<skill>/SKILL.md
  - brainctl:brains validate PASS; route(<query>)=<brain>
  - proof:<engine> --diagnose PASS with baseline sources ... and optional sources gated by credentials
  - proof:taskpool selfcheck PASS; proof-check PASS; dispatch tick summary OK; follow-through triggers present
```
