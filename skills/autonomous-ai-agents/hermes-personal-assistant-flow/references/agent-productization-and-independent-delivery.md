# Agent Productization and Independent Delivery

Scope: use when a user asks Hermes to design an agent/personal assistant for a business scenario and asks whether it should run inside Hermes or become an independently deliverable product. Applicability is class-level: examples below are generic archetypes, not project facts or delivery commitments. Anti-condition: do not encode customer-specific IDs, paths, channels, credentials, or one-off project acceptance rules here; put those in project profiles or scoped references.

## Core decision

Separate three roles:

- Hermes as incubator/factory: research, design, generate, test, iterate, ratchet.
- Hermes as runtime: fastest internal assistant delivery via skills/profile/taskpool/cron/gateway.
- Independent runtime: customer-facing product or deployable bot/service after the workflow stabilizes.

Do not treat an agent as a prompt. A deliverable agent is:

```text
business objective + input sources + tools + state machine + evidence chain + human approvals + output interface + operations loop
```

## Three delivery shapes

### A. Hermes-native assistant

Best for internal use, dogfooding, and fast MVPs.

Typical package:

- skill(s);
- project/profile;
- taskpool workflow pack;
- cron/webhook triggers;
- delivery adapter such as chat or work-management platforms;
- dashboard projection;
- evidence and closeout policy.

### B. Hermes-incubated, independently delivered agent

Best after the Hermes-native workflow has proven value.

Mapping:

- Hermes cron -> scheduler such as system cron, Celery, Temporal, BullMQ, GitHub Actions.
- Hermes taskpool -> Postgres/SQLite/Redis queue and task state.
- Hermes skills -> playbooks, prompt templates, policy files.
- Hermes memory -> user/org profile DB and configuration.
- Hermes gateway -> bot/webhook adapters.
- Hermes tools -> typed tool adapters or MCP tools.
- Hermes evidence artifacts -> evidence store / object storage / audit log.

### C. Agent runtime / product base

Best only after multiple vertical agents are validated.

Minimum modules:

- Agent Profile;
- Workflow Kernel;
- Tool Registry;
- Task Queue;
- Memory/Profile Store;
- Evidence Ledger;
- Human Approval Gate;
- Delivery Adapters;
- Dashboard;
- Evaluation Harness.

## Standard path from scenario to product

1. Business scenario model
   - user/persona;
   - daily/weekly job-to-be-done;
   - input sources;
   - output artifacts;
   - success criteria;
   - red lines and side-effect boundaries;
   - cadence and cost limits.
2. Agent Spec
   - role, domain, objective, users, sources, tools, outputs, risks.
3. Workflow Pack
   - Signal -> Intake -> Classify -> Plan -> Execute/Recommend -> Prove -> Verify -> Report/AskHuman.
4. Hermes dogfood run
   - cron/webhook/taskpool/profile/skills/dashboard.
5. Evaluation and evidence
   - source accuracy, action usefulness, no authority overreach, proof quality, cost, latency.
6. Export/extraction
   - turn Hermes-specific assets into independent runtime modules.
7. Delivery package
   - Docker/CLI/Web app/Bot/SaaS/private deployment, depending on target.

## Product boundary rule

The product should be named by the closed-loop business outcome, not by a generic AI persona.

Prefer archetype names like:

- domain-specific evidence daily monitor;
- blocker detection and acceptance-evidence assistant;
- case triage and evidence-completion assistant;
- public-signal business opportunity radar.

Avoid generic positioning such as:

- AI project manager;
- AI research assistant;
- AI customer service.

## Human-gate defaults

Keep these proposal-only unless explicitly authorized:

- publishing or external messaging to customer channels;
- remote push/merge;
- production deploy;
- payment/purchase;
- secret or credential writes;
- destructive deletes;
- major value/strategy decisions.

For those cases, generate an approval packet with proposed action, evidence, risks, rollback, and read-back plan.

## Verification checklist

- The agent has a business-specific success criterion.
- Input sources and output surfaces are explicit.
- The state machine and evidence policy are defined before execution automation.
- Hermes-native MVP has been tested before independent extraction.
- Independent delivery replaces Hermes internals with explicit runtime modules.
- Human approval boundaries are visible in both the spec and runtime.
