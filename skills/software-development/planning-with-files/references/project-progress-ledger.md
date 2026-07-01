# Project Progress Ledger Pattern

Use this reference when a conversation turns into a durable product/implementation track and the user expects the agent to remember real progress across sessions.

## Applicability

Use when:
- the work has a named project/profile/SSOT;
- there are multiple components or implementation slices;
- the user says progress was not preserved, or the work felt like one-off chat;
- the project includes app/UI/API/gateway/agent-control-plane pieces that need evidence.

Anti-conditions:
- do not create a ledger for a one-off answer or research summary;
- do not put raw private data, secrets, or one-trip details in a class-level skill;
- do not store transient WIP in durable memory.

## Minimum ledger shape

```md
# Progress Ledger — <Project>

Updated: <timestamp>
Status model: idea → SSOT → contract → implementation-slice → verified-slice → beta → release

## Current truth
Canonical state lives here. Future sessions must read/update this ledger before claiming project status.

## Components
| Component | Status | Evidence | Next gate |
|---|---|---|---|
| Product SSOT | validated | path(s) | next decision |
| Core package | verified-slice | test command pass | integration gate |
| Gateway/API | verified-slice | contract tests/curl | UI connection |
| App shell | validated-basic-shell | tests/browser proof | persistence/sync |

## Verified commands
- `command`: result

## Browser/API/UI evidence
- exact URL/screenshot/path/readback

## Open gates
1. ...

## Operating rule
Every material future step must update this ledger and any project profile pointer.
```

## Profile/memory split

- Project profile: store the ledger path, SSOT paths, implementation status, and next gate.
- Memory: store only the stable project-profile path or a short profile+ledger pointer.
- Taskpool: store concrete follow-up engineering tasks.
- Skill: store the class-level pattern, not this project's status.
