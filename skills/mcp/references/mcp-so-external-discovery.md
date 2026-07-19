# MCP.so external discovery source

Scope: domain — read-only discovery and audit of external MCP/agent capabilities.
Applicability: use only when a task requires finding or comparing unknown MCP servers, remote servers, clients, CLI tools, Agent Skills, or reusable Loops.
Anti-conditions: do not use for ordinary configuration of a known server, protocol implementation, or as authority to install, authenticate, execute, schedule, or promote a candidate.
Falsifier/refresh trigger: narrow or retire this source if its listings become inaccessible, cannot be resolved to canonical upstream evidence, or a better source provides stronger identity, health, permission, and provenance guarantees.

## Source role

Use `https://mcp.so/` as an advisory discovery index. Route known persistent integrations to `native-mcp`, one-off calls to `mcporter`, and server construction to `mcp-server-from-scratch`.

The dated source review and current candidate decisions are stored outside the global skill in:

- `docs/private/mcp-so-external-capability-source-20260720.md`

## Trust boundary

MCP.so is an index, not a trust root. Its listing, `Verified`, `Featured`, `Official`, rank, star count, install command, generated FAQ, or “production-ready” wording is not proof of publisher identity, security, protocol compliance, runtime health, least privilege, license compatibility, or production readiness.

The observed paid-submission page advertised immediate publication without review together with a Verified badge. Keep badge and placement metadata advisory until verified at the canonical upstream source.

Never:

- run `npx -y`, `uvx`, curl/install commands, or remote MCP URLs directly from a listing;
- copy credentials into a candidate config;
- add a candidate to persistent Hermes configuration merely because it is popular or featured;
- enable MCP sampling during untrusted evaluation;
- treat paid placement as quality or security certification.

## Discovery-to-adoption ladder

1. Discover on MCP.so by category, tag, search, or ranking.
2. Resolve the canonical upstream repository, package registry entry, official documentation, and publisher identity.
3. Pin a version or commit and verify license and recent maintenance.
4. State the concrete capability gap. Reject duplicates, wrappers over existing tools, and global tool-count inflation without value.
5. Inspect command/package or HTTP endpoint; tools/resources/prompts and input schemas; network, filesystem, credential, write/delete, and sampling behavior; timeout, output, and error boundaries.
6. Use the smallest evaluation surface: static comparison for prose skills/loops; `mcporter` or a disposable environment for one-off MCP smoke; never native/global config first.
7. Run positive and relevant negative checks: initialize/list/call, unknown method/tool, timeout/output bounds, secret redaction, path traversal, and destructive-call boundaries.
8. Classify as `reject`, `watch`, `borrow-pattern`, `ad-hoc-wrapper`, or `native-candidate`.
9. Promote only with evidence, rollback/fallback, and maintenance ownership. Default heuristic: three safe, useful ad-hoc uses before native consideration.

## Candidate record

```yaml
source_url: https://mcp.so/...
canonical_upstream: https://github.com/... | package registry | official docs
version_or_commit: ...
license: ...
capability_gap: ...
overlap: ...
execution_surface:
  transport: stdio|http|cli|skill|loop
  network: ...
  filesystem: ...
  credentials: ...
  side_effects: ...
  sampling: disabled|not_applicable
verification:
  positive: ...
  negative: ...
decision: reject|watch|borrow-pattern|ad-hoc-wrapper|native-candidate
rollback_or_fallback: ...
maintenance_owner_or_refresh: ...
```

## Initial reusable audit result

No new MCP server is justified by the first audit. Existing native capabilities already cover filesystem, git, memory, time, Figma Context, and Stitch; an unproven addition would increase startup coupling, tool/prompt surface, package execution, and credential risk without an evidenced gap.

Candidates worth retaining:

- Official `larksuite/cli` skills: potential identity-aware auth and documentation-first OpenAPI fallback; reconcile with the existing Lark integration before adoption.
- `receiving-code-review`: useful pattern for verifying feedback before implementation; absorb only through the governing review workflow and its evals.
- `vercel-react-best-practices`: useful Next.js performance taxonomy; evaluate against a real Next.js task before broad adoption.
- `minimal-run-and-audit`: possible evidence-normalized ML reproduction pattern; keep on watch until a real reproduction task exists.

Reject as current duplicates: independent-verifier and visual-regression loops, generic browser-testing skills in ordinary local work, already installed development skills, and already configured MCP capabilities.

## Verification checklist

- [ ] Live listing and canonical upstream source were both inspected.
- [ ] Badge/ranking/install text remained untrusted metadata.
- [ ] A concrete capability gap was written down.
- [ ] Overlap with current tools, skills, and MCP servers was checked.
- [ ] Version/commit, license, permissions, and maintenance were checked.
- [ ] Evaluation was isolated and sampling remained disabled for untrusted MCP.
- [ ] Positive and relevant negative tests have real output.
- [ ] Decision and promotion boundary are explicit.
