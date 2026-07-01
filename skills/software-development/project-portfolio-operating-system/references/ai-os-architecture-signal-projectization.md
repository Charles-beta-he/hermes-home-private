# AI OS Architecture Signal → Hermes Projectization

Use when a user approves turning an external AI OS / assistant architecture signal (conference slide, product demo, device OS diagram, agent framework, or multi-model architecture analysis) into a durable Hermes-managed project.

## Applicability

- User says the architecture direction is accepted and should be advanced as a project.
- The signal is broader than a one-off answer and maps to Hermes self-architecture, workflow governance, control surfaces, edge devices, or CapabilityGraph evolution.
- The desired landing is metadata/SSOT/roadmap first, not immediate runtime mutation.

## Anti-conditions

- Do not claim runtime implementation from a diagram, screenshot, or model analysis.
- Do not create production automation, cron, taskpool execution, external sends, always-on sensing, or Hermes runtime code changes from projectization alone.
- Do not merge project-specific facts or raw user data across profiles; use relations and pattern-only merge policies.
- Do not treat multi-model agreement as evidence of implementation completion.

## Landing procedure

1. **Classify the signal**
   - Separate reusable architecture pattern from project-specific facts, product claims, and speculative model interpretation.
   - Name the durable project at class level, not as a session artifact.

2. **Create profile + SSOT workspace**
   - Project profile under `~/.hermes/project-profiles/<project-id>.json`.
   - SSOT root under `~/.hermes/workflows/projects/<project-id>/`.
   - Minimum docs:
     - `00-model/<project>-ssot.md`
     - `01-architecture/<architecture>.md`
     - `02-roadmap/phase-roadmap.md`
     - `03-governance/default-off-gates.md`
     - `04-evidence/<source-evidence>.json`
     - `05-backlog/task-candidates.json`
     - `progress-ledger.md`

3. **Portfolio registry update**
   - Add the project to the portfolio registry.
   - Add relations to Hermes/control-console/model-router/persona/edge projects using explicit merge policies.
   - Prefer relation-only or shared-module entries over merging facts.

4. **Set conservative maturity**
   - Use states like `profiled+ledgered+contract-ready` for metadata/contract slices.
   - Runtime components should remain `planned`, `not_started`, `shadow-only`, or `explicit-authorization-required` until tests/readback prove otherwise.

5. **Write task candidates, not fake completion**
   - Candidate tasks should include objective, acceptance evidence, anti-drift check, parallel boundary, evidence bundle, and dependency order.
   - P0 candidates should normally be read-only projection/schema/doctor work.

6. **Verify**
   - Run portfolio doctor and strict verify if available.
   - Validate JSON artifacts.
   - Report exact paths and maturity boundary.

## Default gates for Agent OS / AI OS projects

- Default-off: always-on mic/camera/screen, automatic memory writes, external sends, cron creation, runtime routing changes, worker lifecycle mutation, publish/deploy/destructive actions.
- Shadow-first: intent routing, context/environment understanding, memory/skill/task candidates, model routing, proactive suggestion, edge event classification.
- Evidence required before promotion: schema validation, dry-run/readback, tests, kill switch/rollback, cost budget, user-visible receipt, and explicit AuthorityGrant for side effects.

## Example target model

```text
Ingress / Modalities / Devices
  -> Context Graph / Situation Model
  -> CapabilityIntent
  -> CapabilityGraph Router
  -> Policy + Authority Gate
  -> Tool / Skill / Worker Lease
  -> Evidence DAG
  -> ClosureRecord
  -> User-visible Control Surface
```
