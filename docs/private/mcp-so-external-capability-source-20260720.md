# MCP.so external capability source review — 2026-07-20

```yaml
schema: hermes_reference_review_v1
id: mcp-so-external-capability-source-20260720
source_url: https://mcp.so/
source_repo: https://github.com/chatmcp/mcpso
source_commit: ddcdb9d54576baec7ab9929af3bf7d5d71497498
observed_at: 2026-07-20T01:23:37+0800
scope: read-only external capability discovery and candidate audit
status: active-discovery-source
trust_level: advisory-only
runtime_mutation: false
auto_install: false
external_write: false
```

## Objective

Add MCP.so as a reusable external capability discovery source for Hermes while preserving a strict separation between discovery, source verification, local evaluation, and runtime adoption.

Success means:

- Hermes can consult MCP.so when looking for MCP servers, clients, CLI tools, Agent Skills, or Loops.
- Every candidate is independently checked against its upstream repository/package/official documentation.
- MCP.so badges, rankings, descriptions, install snippets, and traffic claims never become trust or execution authority.
- No candidate is installed, configured, authenticated, promoted, or scheduled merely because it appears on MCP.so.

## Source facts and evidence

| Claim | Evidence | Confidence |
|---|---|---|
| MCP.so exposes Servers, Remote Servers, Clients, CLI, Loops, Skills, Feed, categories and rankings | Live home/navigation: https://mcp.so/ | high |
| Sitemap currently exposes about 18,278 server pages, 367 client pages, 250 skill pages, 170 CLI pages, and 40 loop pages | Live sitemap sections under https://mcp.so/sitemap.xml | high, time-scoped |
| Paid submission is $39 and promises immediate publication without review, a Verified badge, featured/priority placement, and a dofollow link | https://mcp.so/submit | high |
| Sponsor tiers are $399/$699/$1,299 per month | https://mcp.so/advertise | high |
| Public repository is Apache-2.0, TypeScript, and has an older Supabase/Next.js directory implementation | GitHub API and https://github.com/chatmcp/mcpso | high |
| Public repo does not prove the current commercial site's full implementation | Public repo last observed commit is 2025-03-26 while the live site contains materially newer commercial/features surfaces | medium-high |

## Trust boundary

MCP.so is an index, not a trust root.

Never infer any of the following from a listing, badge, ranking, or snippet:

- official publisher identity;
- repository/package ownership equivalence;
- security review;
- protocol conformance;
- current runtime health;
- least-privilege credential handling;
- production readiness;
- license compatibility;
- permission to install or execute.

The paid path's “publish immediately without review” plus “Verified badge” makes badge semantics commercially ambiguous. Treat `Verified`, `Featured`, `Official`, popularity and star counts as separate untrusted metadata until the upstream source proves each claim.

## Candidate gate

For each candidate, record:

1. `source_identity`: canonical upstream repo/package/docs and an immutable version or commit.
2. `capability_delta`: concrete Hermes gap; reject duplicates and tool-count inflation.
3. `license_and_maintenance`: license, recent activity, owner, update strategy.
4. `execution_surface`: stdio/HTTP/CLI/skill/loop; commands, network, files, credentials and side effects.
5. `schema_and_permissions`: tools/resources/prompts, input schema, read/write/delete scope, sampling behavior.
6. `local_reproduction`: isolated smoke or static workflow comparison; no global config first.
7. `negative_tests`: unknown tool/method, timeout/output bounds, secret redaction, path traversal or destructive-call boundary where applicable.
8. `decision`: `reject | watch | borrow-pattern | ad-hoc-wrapper | native-candidate`.
9. `promotion_gate`: evidence + rollback/fallback + maintenance owner before native/global adoption.

Default decisions:

- Discovery only: `watch`.
- One-off use after validation: `ad-hoc-wrapper` via mcporter or an isolated CLI.
- Reused safely at least three times: may become `native-candidate` after explicit config review.
- Untrusted MCP sampling: disabled during evaluation.

## Initial self-audit

### Worth retaining as candidates

| Candidate | Source evidence | Decision | Reason / next gate |
|---|---|---|---|
| `larksuite/cli` skill family, especially `lark-shared` and `lark-openapi-explorer` | Official repo https://github.com/larksuite/cli, MIT, active; inspected skill blobs `5b1c94e...` and `508193a...` | `watch` → possible `ad-hoc-wrapper` | Strong fit for the existing Lark workflow: identity-aware auth, least-scope guidance, exit-10 high-risk confirmation, documentation-first raw OpenAPI fallback. Do not install/auth until an unmet Lark operation requires it; reconcile first with current `lark-mcp` and local OAuth flow. |
| `receiving-code-review` | https://github.com/obra/superpowers/blob/main/skills/receiving-code-review/SKILL.md, MIT, inspected blob `4c77a10...` | `borrow-pattern` | Useful missing complement to pre-commit review: verify external feedback against code, preserve compatibility/YAGNI, implement one item at a time. Land only through the code-review skill's own routing/eval gate, not by blind package install. |
| `vercel-react-best-practices` | https://github.com/vercel-labs/agent-skills/blob/main/skills/react-best-practices/SKILL.md, skill declares MIT, inspected blob `237988d...` | `watch` | High-quality React/Next performance rule taxonomy. Current Hermes already has broad UI/React guidance; evaluate against a real Next.js performance task before adding 70 rules globally. |
| `minimal-run-and-audit` | MCP.so page points to `lllllllama/ai-paper-reproduction-skill` | `watch` | Evidence-normalized ML reproduction outputs could strengthen MLOps work, but no current reproduction task justifies installation. Requires upstream license/commit and a real smoke target. |

### Useful ideas already covered locally

| MCP.so item | Existing Hermes coverage | Decision |
|---|---|---|
| `independent-verifier-pass` Loop | `requesting-code-review`, `development-closure-consensus`, completion-claim gate | reject duplicate |
| `visual-regression-until-match` Loop | visual regression/uIMax/browser screenshot-diff workflows | reject duplicate |
| `agent-browser`, `webapp-testing` | browser tools, macOS computer use, browser-harness integration | reject by default; reconsider only for a missing cloud-browser/sandbox case |
| `systematic-debugging`, `test-driven-development`, `writing-plans`, `requesting-code-review`, `subagent-driven-development` | already installed local skills | reject duplicate |
| Time, filesystem, memory, Figma/Stitch MCP entries | already enabled through Hermes native MCP | reject duplicate |

### MCP server adoption result

No new MCP server should be added now.

Current native MCP inventory already provides filesystem, git, memory, time, Figma Context and Stitch. Adding an unproven server would increase global tool count, startup coupling, prompt surface, package execution and credential risk without an evidenced capability gap.

## Decisions

```yaml
decisions:
  immediate_landing:
    - add MCP.so to the MCP skill family as a conditionally loaded read-only discovery source
    - enforce upstream verification and no-auto-install boundaries
    - retain four candidates as watch/borrow-pattern items
  blocked_until:
    - native MCP addition requires a concrete capability gap, isolated smoke, permission review, rollback and maintenance plan
    - Lark CLI adoption requires overlap analysis with current lark-mcp/OAuth behavior and exact auth/write authority
    - code-review pattern absorption requires a scoped skill routing/eval change
  do_not_do:
    - do not treat MCP.so Verified/Featured/Official labels as certification
    - do not execute npx/uvx/install snippets directly from a listing
    - do not auto-add servers to config.yaml
    - do not enable sampling for untrusted candidates
    - do not schedule polling or external delivery from this approval
```

## Verification

- Live site, submit, advertise, sample server/skill/loop pages inspected.
- Sitemap counts read from live XML.
- Candidate upstream repositories and selected skill blobs read through GitHub API.
- Current native MCP inventory read with `hermes mcp list`.
- Local skill inventory compared with MCP.so's 250 skill slugs; exact overlap found for six core software-development skills.
- Agent OS route preflight classified this as medium-risk S2 local/docs work and prohibited S4–S7 side effects.

## Refresh policy

This review controls trust and procedure, not live listing state. Re-fetch MCP.so and the canonical upstream source whenever evaluating a candidate. Refresh this document only when the source's role, badge semantics, categories, or adoption boundary materially changes; do not append ordinary per-candidate task progress here.
