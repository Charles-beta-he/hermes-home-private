---
name: external-framework-evaluation
description: "Use when evaluating an external framework, tool, or platform for integration with or migration to Hermes Agent. Covers architecture extraction, Hermes primitive mapping, gap analysis, and migration value assessment. Triggers: evaluate framework, assess tool, map to Hermes, migration value, integration feasibility, 外部框架评估, 工具评估."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [evaluation, framework, integration, migration, architecture]
    related_skills: [workflow-ecosystem-audit, agent-boundary-audit, architecture-theory-audit, goal-calibration]
---

# External Framework Evaluation

## Overview

When Hermes encounters an external framework, tool, or platform, use this skill to systematically evaluate its architecture, map it to Hermes primitives, identify gaps, and assess migration value. This prevents ad-hoc evaluation and ensures consistent, evidence-based decisions.

## When to Use

- User asks to evaluate an external framework or tool for Hermes integration
- User asks to assess migration feasibility from another system
- User asks to map external concepts to Hermes primitives
- User says: evaluate framework, assess tool, map to Hermes, migration value, integration feasibility, 外部框架评估, 工具评估

Don't use for:
- Simple feature comparisons without architectural analysis
- One-off tool usage without integration intent
- Internal Hermes component evaluation (use `hermes-self-audit` instead)

## Core Evaluation Steps

### Step 1: Architecture Extraction

Extract the external framework's core architecture:

1. **Identify core components**: What are the main modules/services?
2. **Map data flow**: How does data move through the system?
3. **Identify interfaces**: What APIs/protocols does it expose?
4. **Document constraints**: What are the limitations and requirements?

**Output**: Architecture diagram or structured description

### Step 2: Hermes Primitive Mapping

Map external concepts to Hermes primitives:

| External Concept | Hermes Primitive | Gap/Difference |
|------------------|------------------|----------------|
| [External feature] | [Hermes equivalent] | [What's missing or different] |

**Common Hermes primitives to map to**:
- `goal-calibration` — Task intake and goal alignment
- `taskpool` — Task lifecycle and state management
- `skill` — Reusable procedures and workflows
- `memory` — Persistent knowledge storage
- `experience-ratchet` — Cross-session learning
- `agent-boundary-audit` — Self-optimization and landing
- `workflow-ecosystem-audit` — Workflow coverage and gaps

**Output**: Mapping table with gap analysis

### Step 3: Gap Analysis

Identify what Hermes lacks compared to the external framework:

1. **Feature gaps**: What capabilities does Hermes lack?
2. **Architecture gaps**: What structural differences exist?
3. **Integration gaps**: What would need to change in Hermes?
4. **Risk gaps**: What risks does the external framework mitigate that Hermes doesn't?

**Output**: Prioritized gap list with impact assessment

### Step 4: Migration Value Assessment

Assess the value of migrating or integrating:

| Feature | Migration Value | Migration Difficulty | Priority |
|---------|-----------------|---------------------|----------|
| [Feature] | ⭐⭐⭐⭐⭐ | [Low/Medium/High] | [P1/P2/P3] |

**Value criteria**:
- ⭐⭐⭐⭐⭐: Critical capability, high impact
- ⭐⭐⭐⭐: Important capability, significant impact
- ⭐⭐⭐: Useful capability, moderate impact
- ⭐⭐: Nice-to-have, low impact
- ⭐: Marginal value

**Difficulty criteria**:
- Low: Direct mapping, minimal changes
- Medium: Some adaptation required
- High: Significant architecture changes needed

**Output**: Migration value matrix

### Step 5: Implementation Plan

If migration is recommended, create a phased plan:

1. **Phase 1**: [Highest value, lowest difficulty]
2. **Phase 2**: [High value, medium difficulty]
3. **Phase 3**: [Medium value, higher difficulty]

**Output**: Phased implementation plan

## Output Template

```markdown
# [Framework Name] Evaluation Report

## 📋 Evaluation Objective
[Evaluate [framework] for [purpose]]

## 🎯 Architecture Analysis
### Core Components
- [Component 1]: [Description]
- [Component 2]: [Description]

### Data Flow
[Description or diagram]

### Interfaces
- [API 1]: [Description]
- [API 2]: [Description]

## 🎯 Hermes Primitive Mapping

| External Concept | Hermes Primitive | Gap/Difference |
|------------------|------------------|----------------|
| [Concept] | [Primitive] | [Gap] |

## 🎯 Gap Analysis

### Feature Gaps
- [Gap 1]: [Impact]
- [Gap 2]: [Impact]

### Architecture Gaps
- [Gap 1]: [Impact]
- [Gap 2]: [Impact]

## 🎯 Migration Value Assessment

| Feature | Migration Value | Difficulty | Priority |
|---------|-----------------|------------|----------|
| [Feature] | ⭐⭐⭐⭐⭐ | [Difficulty] | [Priority] |

## 🎯 Implementation Plan

### Phase 1: [Name] (1 week)
1. [Step 1]
2. [Step 2]

### Phase 2: [Name] (1 week)
1. [Step 1]
2. [Step 2]

## 🎯 Recommendation
[Final recommendation with rationale]

---
**Status**: ✅ Evaluation complete
**Conclusion**: [High/Medium/Low] value migration
**Priority**: [P1/P2/P3]
```

## Common Pitfalls

1. **Superficial analysis**: Don't just compare features — analyze architecture and data flow
2. **Missing gaps**: Always identify what Hermes lacks, not just what it has
3. **Overvaluing novelty**: Newer isn't always better — assess actual value, not novelty
4. **Ignoring integration cost**: Migration difficulty is as important as value
5. **No phased plan**: Big-bang migrations are risky — always propose phased approach

## Verification Checklist

- [ ] Architecture extraction covers core components, data flow, and interfaces
- [ ] Hermes primitive mapping identifies equivalent concepts and gaps
- [ ] Gap analysis prioritizes by impact and feasibility
- [ ] Migration value assessment uses consistent criteria
- [ ] Implementation plan is phased and realistic
- [ ] Recommendation is evidence-based and actionable

## References

See `references/guardrails-evaluation-example.md` for a complete evaluation example.
