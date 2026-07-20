---
name: ai-agent-b2b-service
description: "Use when packaging AI Agent customization or AI-assisted software-delivery governance as a B2B service: qualification, diagnosis, truth-source mapping, authority contracts, pilot validation, evidence-gated delivery, handover, and ongoing ops."
version: 1.5.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    scope: cross-project
    applicability: "B2B AI Agent customization and AI-assisted software-delivery governance: diagnosis, truth-source mapping, authority contracts, pilot, evidence-gated delivery, handover, and ops"
    anti_conditions: "Internal Hermes operations, personal assistant tasks, or one-off technical Q&A"
    tags: [b2b, ai-agent, consulting, service-delivery, startup]
    related_skills: [hermes-personal-assistant-flow, harness-intake-contract, goal-calibration]
---

# AI Agent B2B Service Delivery

## Scope

Use this skill when the user wants to package AI Agent customization expertise or an AI-assisted software-delivery governance workflow as a B2B service offering. It covers qualification, diagnosis, commercial/spec/authority contracts, pilot validation, evidence-gated production delivery, client handover, and ongoing operations.

Anti-conditions:
- Not for internal Hermes operations or personal assistant workflows.
- Not for one-off technical Q&A unrelated to service delivery.
- Not for C2C or consumer product strategies.

## When to Use

- User asks how to monetize AI Agent or AI-assisted engineering expertise.
- User wants to create a service offering around Agent deployment/customization.
- User wants to turn a real software project workflow into a repeatable client delivery system.
- User needs templates for client diagnosis, authority, evidence, proposals, acceptance, or handover.
- User is planning a solo/small-team consulting business around Agents or governed software delivery.

## Core Framework

### Service Types (pick 1-3 to start, not all)

```
Type A: AI Agent Deployment
  - Help client set up and configure an Agent instance
  - Customize skills, tools, integrations
  - Pricing: 5K-30K per deployment

Type B: AI Workflow Consulting
  - Diagnose which business processes can be automated
  - Design Agent workflows, not just install tools
  - Pricing: 2K-10K per diagnosis, 5K-20K for full design

Type C: Frontend + AI Composite Service
  - Build AI-powered web/apps for clients
  - Leverages both frontend skills and Agent expertise
  - Pricing: 20K-100K per project

Type D: Training & Enablement
  - Teach client teams to use/customize Agents
  - Pricing: 500-2000/person, group discounts

Type E: AI-Assisted Software Delivery Governance
  - Map truth sources, capability backlog, safe slices, authority, evidence, acceptance, and handover
  - Best for migrations, cross-platform parity, legacy rewrites, and teams already using AI coding tools
  - Price diagnosis/pilot/production separately; do not quote whole-project delivery before the baseline and authority contract
```

### Standard Delivery Pipeline

```
Phase 1: Client Acquisition (ongoing)
  - Target: SMEs wanting AI but lacking expertise
  - Channels: tech community articles, referrals, freelance platforms
  - Case study packaging: real Hermes experience → publishable case
  - Key action: write 1-2 articles showing real Agent customization results

Phase 2: Needs Diagnosis (1-2 days)
  - Client interview (20 questions, see template below)
  - Identify automation opportunities
  - Output: Needs Diagnosis Report
  - Key rule: listen more than pitch

Phase 3: Solution Design (2-3 days)
  - Agent capability specification
  - Skill list with inputs/outputs/triggers
  - Data integration plan
  - Milestone plan with pricing
  - Output: Solution Design Document + Formal Quote

Phase 4: Rapid Validation (3-5 days)
  - Build MVP with 1-2 core skills
  - Client demo and feedback
  - Confirm direction before full build
  - Output: Demonstrable MVP

Phase 5: Full Delivery (1-2 weeks)
  - Develop remaining skills per priority
  - System integration and testing
  - Deployment and monitoring setup
  - Output: Production-ready Agent + Documentation

Phase 6: Training & Ops (ongoing)
  - User training with key users
  - Operations manual
  - Monitoring and optimization
  - Output: Self-sufficient client + SLA
```

## Delivery-Grade Software Workflow Branch

When the deliverable is an operable software-delivery workflow—not merely consulting, Agent installation, or a Pi package—load `references/delivery-grade-software-workflow.md` and use its eight-stage lifecycle:

```text
Qualification → Discovery/Baseline → Commercial/Spec/Authority
→ Solution Workspace → Pilot Slice → Production Delivery
→ Acceptance/Handover → Operations/Ratchet
```

Required rules:
- map canonical requirements, reference implementations, target code and runtime proof as separate truth sources;
- bind every completion claim to scope, freshness, evidence and limitations;
- fail closed on unresolved evidence contradictions;
- keep local-safe work separate from push, deploy, external send, credentials, payment and production mutation;
- separate pilot, production and client-acceptance boundaries;
- keep public cases `not_ready` until publication rights and anonymization pass.

Create the machine-readable control surface from `templates/delivery-engagement-manifest.json`, then validate it with:

```bash
python3 ~/.hermes/skills/business/ai-agent-b2b-service/scripts/verify_delivery_workflow.py <manifest.json>
```

A validator PASS proves only that the declared snapshot satisfies the local manifest gates up to the declared `completion_boundary`. It does not independently prove business-code correctness, remote evidence, production readiness, live authority, or client acceptance. The starter template must remain RED until placeholders are replaced; `in_progress` does not require the target boundary to be accepted.

## Client Interview Template (20 Questions)

### Business Context
1. What does your company do? Main products/services?
2. What's your team size and structure?
3. What tools/software do you currently use daily?

### Pain Points
4. What are the most time-consuming repetitive tasks?
5. Which processes have the most errors or rework?
6. Where do employees complain most about inefficiency?
7. What tasks require waiting for someone else's input?

### AI Readiness
8. Has your team used any AI tools? Which ones?
9. What's your experience with AI so far?
10. Are there any data security/compliance requirements?

### Expectations
11. What specific outcomes do you expect from AI automation?
12. How would you measure success? (time saved, errors reduced, etc.)
13. What's your budget range for this initiative?
14. What's your timeline expectation?

### Technical Environment
15. What systems need to integrate with the Agent?
16. Do you have APIs or data export capabilities?
17. Who will be the internal champion/operator?

### Decision Process
18. Who makes the final decision on this project?
19. What would make this a "must-do" vs "nice-to-have"?
20. What's your biggest concern about adopting AI?

## Pricing Reference (3 Tiers)

```
Tier 1: Starter (5K-15K)
  - 1-2 automation scenarios
  - Basic Agent setup + 3-5 skills
  - 1 round of training
  - 30-day support
  - Best for: small teams testing AI

Tier 2: Professional (15K-50K)
  - 3-5 automation scenarios
  - Full Agent with 10-20 skills
  - System integration (1-2 systems)
  - Training + documentation
  - 90-day support + monthly check-in
  - Best for: mid-size companies serious about AI

Tier 3: Enterprise (50K-200K)
  - Comprehensive automation suite
  - Custom Agent with 20+ skills
  - Full system integration
  - Training program + operations manual
  - 6-month support + quarterly optimization
  - Best for: companies wanting AI-first operations
```

## Delivery Artifacts Checklist

```
□ Needs Diagnosis Report
  - Business context summary
  - Pain point analysis
  - Automation opportunity list (prioritized)
  - Expected ROI estimate
  - Preliminary pricing

□ Solution Design Document
  - Agent architecture diagram
  - Skill specification (input/output/trigger for each)
  - Data integration plan
  - Milestone plan
  - Formal quote with payment terms

□ MVP Demo
  - Working prototype of core skill(s)
  - Client feedback recorded
  - Direction confirmed

□ Production Delivery
  - All skills implemented and tested
  - System integration complete
  - Deployment verified
  - User documentation

□ Training Package
  - Training slides/recording
  - Operations manual
  - FAQ document

□ Operations Agreement
  - SLA terms
  - Escalation process
  - Update/iteration schedule
  - Support boundaries
```

## Pitfalls

1. **Selling technology instead of outcomes.** Clients buy solutions to problems, not AI features. Always frame in business terms: "saves 20 hours/month" not "has 20 skills."
2. **Over-promising on MVP.** An MVP should demonstrate ONE core value well, not five features poorly.
3. **Under-pricing.** Your experience (143 skills, multi-model orchestration, taskpool governance) is rare. Price on value, not time.
4. **Skipping the diagnosis.** Jumping to implementation without understanding the client's real problem leads to wrong solutions.
5. **No success metrics defined.** If you can't measure whether the Agent helped, the client can't justify paying.
6. **Ignoring the human factor.** The biggest blocker is usually people resisting change, not technical limitations. Plan for change management.
7. **One-person bottleneck.** As a solo operator, document everything so you can eventually delegate or scale.

## Linked Files

- `references/solo-company-startup-context.md` — startup models, registration considerations, pricing reference for solo consultants.
- `references/delivery-grade-software-workflow.md` — eight-stage, evidence-gated workflow for AI-assisted software delivery, migration, parity, authority, handover, and operations.
- `templates/needs-diagnosis-report.md` — ready-to-use client diagnosis report template.
- `templates/delivery-engagement-manifest.json` — intentionally-RED starter for machine-readable truth sources, artifacts, claims, authority, stages, metrics, risks, public-case and acceptance state.
- `scripts/verify_delivery_workflow.py` — fail-closed manifest validator with reference integrity, local SHA-256 evidence pinning, ordered stages, stage-specific semantic artifacts, maximum completion-boundary enforcement, closure contracts and authority/publication gates.
- `scripts/test_verify_delivery_workflow.py` — regression tests for contradiction, evidence integrity, malformed input, semantic artifacts, stage/boundary/closure state, authority, client acceptance and anonymization gates.
- `references/delivery-manifest-adversarial-verification.md` — reusable RED/GREEN/template, mutation, authority, semantic-artifact and independent-fixture verification procedure for fail-closed Manifest validators.

## Verification Checklist

- [ ] Client's actual problem is identified (not assumed).
- [ ] Success criteria are measurable and agreed upon.
- [ ] Pricing reflects value delivered, not hours spent.
- [ ] MVP demonstrates core value before full build.
- [ ] Client can operate the Agent independently after training.
- [ ] Support boundaries and SLA are explicit.
- [ ] A public case is produced only when publication rights and anonymization are verified; otherwise an internal case packet is retained.
- [ ] Delivery manifest declares an exact completion boundary and closure state.
- [ ] Every verified claim has scope, evidence, a non-empty limitations list, exact S0–S7 `stage_refs`, and a `max_stage` that is bounded both by those refs and by at least one cited truth source's `max_stage`; every accepted stage has a linked verified claim.
- [ ] Unresolved contradictions block acceptance rather than being averaged or deleted.
- [ ] Reviewable stages contain their required artifact types and evidence; superseded closure resolves to a registered successor engagement backed by `successor_engagement`-typed evidence.
- [ ] External action names are allowlisted; enabled actions include exact target/scope, a typed evidence-backed authority grant bound to the same action/target/scope, rollback and readback; credential/payment actions remain human-only.
- [ ] Pilot evidence is not promoted to production or client acceptance.
- [ ] Accepted closures contain at least one verified outcome and no unverified/disputed claims; accepted risks name an approver, date, controls and evidence.
- [ ] Public-ready and accepted-client states cite typed publication/anonymization/acceptance evidence, not only booleans or unrelated known IDs; final client acceptance requires S6 accepted.
