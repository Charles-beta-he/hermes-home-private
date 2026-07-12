# Community Practice-Bank Intake Pattern

Scope: class-level procedure for public/social-media leads that point to community agent-architecture practice banks. This reference intentionally uses one verified intake as an example, but the durable rule is the reusable intake boundary.

Applicability: use when a public preview, repository, or user-provided file claims to provide Claude/agent-architecture/MCP/coding-agent practice questions and the user asks to use it for Hermes skill testing or capability improvement.

Anti-conditions: do not use this reference to copy question text, install third-party skills, treat unofficial answers as certification evidence, enable MCP/tool authority, or write session scores to memory.

## Example source evidence class

A verified public preview/repository lead had these properties:
- public media preview was QR/App-gated, so only metadata and cover-frame evidence were available;
- repository README described an unofficial Claude Certified Architect practice exam;
- repository API reported no declared license;
- raw files included a README, a large markdown exam file, and a coding-agent skill file;
- parsed structure showed 77 questions and 77 answer keys across five domains;
- answer-key distribution was strongly skewed, so it is weak as a pure benchmark but useful for domain/process coverage.

## Durable absorption rule

Use community practice banks in three bounded ways:

1. Session-local drill source
   - User authorizes the specific source.
   - Parse only the subset needed for the session.
   - Do not persist question text or answer explanations.

2. Skill/process coverage test
   - Extract domain labels, scenario classes, and capability gaps without copying questions.
   - Compare gaps against loaded Hermes skills and workflow gates.
   - Patch only abstract durable rules, such as source-intake gates, readback requirements, and weak-domain mapping.

3. Eval prompt seed
   - Write original prompts that represent the capability boundary.
   - Keep prompts short and non-infringing.
   - Include positive, neighbor, forbidden, and no-load cases.

## Required source readback

Before using the bank, capture:
- URL/path and authority class: official, community, derived/unknown;
- license/readme status;
- freshness evidence: live retrieval time, upstream updated/pushed time or immutable file hash;
- whether the source is latest reachable upstream, pinned, or stale; stale/local-only sources can support process rehearsal but not current-skill certification;
- file list and content hashes or byte sizes;
- question count and domain headings if parseable;
- any bias or quality warning visible from structure, such as answer-key skew;
- exact boundary: local/session use only vs durable abstract pattern.

## Skill-test interpretation

Do not ask “did Hermes get the practice exam score right?” as the only metric. Ask:

- Does the relevant skill load for this request?
- Does the skill require source/license/readback before use?
- Does it map misses to a domain instead of a vague self-critique?
- Does it improve the right landing zone: skill, eval, task proposal, or no-action boundary?
- Does it avoid memory pollution and unlicensed durable copying?

## Falsifier

Narrow this pattern if a future source has an explicit permissive license, official vendor authority, or a deterministic machine-readable eval contract. In that case, it may support stronger reusable fixtures or benchmark automation, but still requires source/readback and anti-copy checks.
