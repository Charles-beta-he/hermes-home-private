# Decision-Discovery Interview Before Spec and Implementation

## Applicability

Use this procedure when a material product, domain, architecture, authority, state-machine, or cross-document decision is still ambiguous and implementation would otherwise depend on silent assumptions.

Use it especially when:

- several specs or ADRs appear to claim current authority;
- domain terms are overloaded or imply competing lifecycles;
- a recommendation/projection is being confused with a commitment, command, execution, acceptance, or financial fact;
- the user asks to pressure-test or “grill” a design before implementation;
- the conversation contains exact negative requirements or numeric boundaries that could be lost during later Spec synthesis.

## Anti-conditions

Do not use it for:

- trivial, reversible edits with already-frozen acceptance criteria;
- fact lookup that the Agent can resolve directly;
- urgent bounded incident repair;
- implementation or deployment authorization;
- reopening unrelated economic, production, security, or governance policy merely because it exists nearby.

## Why this is more than a grilling conversation

A decision-tree interview is useful, but chat-only decisions are fragile. A glossary records only terminology, while ADRs should remain rare. Therefore every material answer must also land in a decision ledger and then converge into a canonical Spec. Do not let the majority of the user's decisions exist only in the context window.

## Procedure

### 1. Freeze the interview contract

Record:

- goal and non-goals;
- exact scope and authority boundary;
- source references and precedence;
- evidence required for closure;
- explicit statement that shared understanding does not authorize implementation.

When documents conflict, distinguish:

1. fresh runtime/code/test/API/readback evidence for current facts;
2. explicitly approved current Spec for intended behavior;
3. active long-term architecture for durable boundaries;
4. ADRs only for the decisions they actually govern;
5. historical/superseded artifacts as provenance;
6. OCR-derived or inferred statements as unresolved leads.

Newer dates never silently erase long-term boundaries, retractions, or runtime evidence.

### 2. Separate facts from decisions

The Agent owns fact discovery. Inspect available files, code, tests, APIs, logs, and readbacks instead of asking the user to retrieve discoverable facts.

The user owns product intent and real trade-offs. The Agent may recommend an answer and explain consequences, but must not relabel its own default as the user's decision.

### 3. Build a dependency tree

Model unresolved decisions and their prerequisites. The current **frontier** contains only decisions whose prerequisites are settled.

Ask one frontier round at a time:

- number every question;
- include a recommended answer;
- include material consequences and alternatives when useful;
- never put two questions in the same round if one answer could change the other;
- recompute the frontier after every response.

One-question-at-a-time is valid when focus or language needs warrant it; frontier batching is valid only for independent decisions.

### 4. Persist every material answer immediately

Maintain a decision ledger with:

- stable decision ID;
- question and dependency;
- state: `open | provisional | settled | deferred | rejected | blocked`;
- exact user answer or clearly labelled Agent recommendation;
- negative requirements and numeric constraints without softening;
- alternatives and consequences;
- writeback target.

A timeout, silence, unavailable user, or automation instruction to “use best judgment” does **not** become an explicit user decision. If safe local work can continue, mark the recommendation `provisional` and require final confirmation. Otherwise leave it `open` or `blocked`.

### 5. Maintain domain language without polluting it

Write a canonical term to `CONTEXT.md` only after it is settled.

`CONTEXT.md` is a glossary only:

- definitions and distinctions are allowed;
- implementation detail, current task state, plans, acceptance criteria, and scratch notes are not;
- aliases or schema/view concepts must map explicitly to canonical objects and must not create parallel lifecycles;
- use `CONTEXT-MAP.md` only for genuinely different bounded-context meanings or ownership, not merely because the repository is a monorepo.

### 6. Create ADRs sparingly

Create or propose an ADR only when all three conditions hold:

1. hard to reverse;
2. surprising without context;
3. the result of a real trade-off.

A documentation-only distinction that has not yet bound a stable API, event contract, persisted state, or independent deployment is often not hard to reverse and should remain in the Spec/decision ledger.

Historical ADRs with stale assumptions should gain explicit current-authority notes; preserve provenance instead of silently rewriting history.

### 7. Converge into the canonical Spec

When the frontier is empty, map every material decision to:

- domain objects and role/authority boundaries;
- business rules;
- exact negative cases;
- acceptance criteria;
- evidence requirements;
- source/supersession markers;
- deferred decisions and their separate future trees.

Produce a decision-to-evidence matrix. Negative requirements require negative evidence. A polished Spec is not sufficient if an exact answer vanished or became weaker prose.

### 8. Close at the correct gate

Ask the user for final shared-understanding confirmation. If no explicit response arrives, keep the packet in `awaiting_shared_understanding_confirmation`; do not claim `spec_ready`.

Even after confirmation:

- `shared_understanding` is not `implementation_authorized`;
- `spec_ready` is not runtime activation, release, deployment, or publication authority;
- commits, pushes, external writes, production changes, payments, credentials, and destructive operations retain their own exact gates.

## Verification checklist

- [ ] Goal, non-goals, authority boundary, sources, and evidence requirements are frozen.
- [ ] Facts were inspected instead of delegated back to the user.
- [ ] Questions in each frontier round are dependency-independent.
- [ ] Each question includes a recommendation but preserves user decision ownership.
- [ ] Silence/timeouts are labelled provisional/open, never user-confirmed.
- [ ] Every material answer exists in a decision ledger outside chat.
- [ ] Negative and numeric requirements survive unchanged into the Spec.
- [ ] `CONTEXT.md` remains pure domain vocabulary.
- [ ] ADRs pass all three gates and stale ADRs retain provenance.
- [ ] Current Spec, long-term architecture, historical artifacts, and runtime facts have explicit precedence.
- [ ] Every acceptance claim maps to fresh positive or negative evidence.
- [ ] Final shared-understanding and implementation authorization are separate gates.

## Promotion and reuse

First land this as a project-scoped candidate. Promote it into a broader workflow only after at least one completed pilot demonstrates that it exposes real ambiguity, preserves decisions better than chat alone, and does not impose disproportionate ceremony on small work. Add positive, neighbor, negative, and forbidden routing examples before canonical promotion.
