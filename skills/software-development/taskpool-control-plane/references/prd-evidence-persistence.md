# PRD Evidence Persistence for Lark Tasks

## Problem

Lark PRD documents (e.g., `https://uaecprod.sg.larksuite.com/docx/...`) require authenticated access and are extracted via Chrome logged-in fallback. The extracted content is typically saved to `/tmp/` paths (e.g., `/tmp/uvisa-lark-product-doc-redacted.txt`) which are ephemeral — cleaned up on reboot or manual `/tmp/` sweeps.

When a Lark task is later audited for product-document evidence, the PRD extract is gone, making it impossible to verify whether a behavior change (e.g., routing, display logic) is specified in the product doc or only exists as a Lark comment/request.

## Evidence Authority Order (reference)

From the taskpool-control-plane skill's core principle:

1. **Newest product doc / PRD / canonical project profile** — business semantics and acceptance
2. **Prototype / PM screenshot / comment image** — UI layout, interaction, visual parity
3. **Live task source** (Lark title/body/comments) — symptom/scope/reproduction
4. **Current implementation/runtime** — landing and regression proof

PRD is rank-1 evidence. If it's missing, the task's acceptance criteria cannot be fully verified against product intent.

## Mitigation: Persist PRD Extracts Under Evidence Directory

When extracting a Lark PRD for a specific task or batch:

1. **Save to the project evidence directory**, not `/tmp/`:
   ```
   ~/.hermes/evidence/<project>/prd-extracts/<lark-doc-id>.md
   ```
   Example: `~/.hermes/evidence/uvisa-app-2.0/prd-extracts/GaGLdayTSosobYx6kWylgS7PgMg.md`

2. **Reference the persisted path** in the task's `evidence_refs` frontmatter:
   ```
   evidence_refs: ["proof:prd:GaGLdayTSosobYx6kWylgS7PgMg; artifact:~/.hermes/evidence/uvisa-app-2.0/prd-extracts/GaGLdayTSosobYx6kWylgS7PgMg.md"]
   ```

3. **For batch intake**, extract the PRD once and reference the same artifact across all tasks in the batch. Do not re-extract per task.

4. **For prototype screenshots**, same pattern:
   ```
   ~/.hermes/evidence/<project>/prototype-screenshots/<feature>-<date>.png
   ```

## Detection: PRD Missing During Audit

When auditing a Lark task's evidence chain and the PRD reference points to a `/tmp/` path:

1. Check if the file still exists: `ls /tmp/uvisa-lark-product-doc*`
2. If gone, check if a copy exists under the evidence directory
3. If neither exists, flag the task as `prd_evidence_missing` — the task's business-rule claims cannot be verified against product doc
4. Do NOT close the Lark task as "product-verified" without PRD evidence; mark as "implementation-verified only"

## Example: 0220b40e Wealth-Buy Routing

- **Lark task**: 理财申购的记录点击后跳转到对应的申购理财产品的详情页
- **PRD source**: `https://uaecprod.sg.larksuite.com/docx/GaGLdayTSosobYx6kWylgS7PgMg`
- **PRD extract**: `/tmp/uvisa-lark-product-doc-redacted.txt` — **GONE** (cleaned up)
- **Prototype**: `https://napp.denatrust.com` — static, no click behavior demonstrated
- **Conclusion**: Routing change had only Lark task description as evidence, no PRD verification possible
- **Lesson**: PRD extracts must be persisted under `~/.hermes/evidence/` at extraction time

## Anti-Pattern

- Saving PRD to `/tmp/` and referencing it in task frontmatter without a persistence step
- Closing a Lark task as "product-verified" when only the Lark title/comment exists (rank-3 evidence) and PRD (rank-1) was never checked or is missing
- Assuming `/tmp/` files survive across sessions
