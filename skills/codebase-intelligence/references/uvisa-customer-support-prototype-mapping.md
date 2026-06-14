# Scoped reference: UVISA customer-support prototype mapping

Scope: UVISA project only. Applicability: use only when the task explicitly concerns the UVISA customer-service/support page, AI 智能助手, knowledge base, FAQ, or the UVISA prototype repository. Anti-condition: do not generalize these paths, routes, content rules, or product mappings to other projects or to global customer-support UI work.

## Source-of-truth relationship

- Prototype repo: `L1f4Is6o0d2Yuu/uvdemo2.0`.
- PRD files:
  - `prd/uvisa-knowledge-base.md` = customer-facing knowledge-base content truth source.
  - `prd/uvisa-faq.md` = FAQ page curated high-frequency subset.
- Product mapping:
  - “知识库” in the customer-support UI means the AI 智能助手 entry/screen, not the FAQ screen.
  - “faq / 常见问题” means the FAQ accordion/self-service question list.
- Existing/prototype AI implementation pattern: local deterministic keyword search over mirrored KB data, no LLM/API key dependency for the public support path.

## Retrieval notes

If raw GitHub URLs 404 for the prototype PRD, do not assume the files are absent. For private/authenticated repos, use `gh api`:

```bash
gh api repos/L1f4Is6o0d2Yuu/uvdemo2.0/contents/prd --jq '.[].name'
gh api repos/L1f4Is6o0d2Yuu/uvdemo2.0/contents/prd/uvisa-knowledge-base.md --jq .content | base64 -d
gh api repos/L1f4Is6o0d2Yuu/uvdemo2.0/contents/prd/uvisa-faq.md --jq .content | base64 -d
```

If `git clone` falls back to SSH and fails with host-key/auth issues, use the GitHub zipball API or direct `gh api` file reads. Treat clone failures as retrieval setup friction, not evidence that the prototype does not exist.

## Frontend implementation pattern

1. Confirm target repo/path first; for current UVISA React frontend it is usually `/Users/charles/Desktop/folder/work/uvisa-app-2.0-migration`.
2. Inspect the prototype files before editing current code. Relevant prototype paths inside the zipball include:
   - `uvisa-app/src/screens/me/CustomerServiceScreen.tsx`
   - `uvisa-app/src/screens/me/AIAssistantScreen.tsx`
   - `uvisa-app/src/screens/me/FaqScreen.tsx`
   - `uvisa-app/src/data/csKnowledge.ts`
3. Preserve current-project real API boundaries:
   - Customer contact/advisor fields should continue to come from `platformConfigService.getCustomerService()` when the current app already uses it.
   - Do not reintroduce hardcoded fallback contact values that flash before config loads if existing tests guard against that behavior.
4. Map prototype into current routes without breaking public-support auth assumptions:
   - `/me/customer` = support hub with advisor hero, chat CTA, AI tile, FAQ tile, contact rows, urgent card.
   - `/me/customer/ai` = AI 智能助手 / knowledge-base search.
   - `/me/customer/faq` = FAQ curated list.
5. Keep KB content customer-facing: avoid internal supplier/funds-flow/channel explanations in rendered answers. Run the PRD redline grep against the mirrored data file when updating content.
6. Verify with focused tests, `tsc -b`, production build, and browser navigation for all three routes. For AI, submit a real query and read back the answer; for FAQ, verify the expected curated entries render.

## Pitfalls

- Do not collapse AI assistant and FAQ into one page: both share the same KB data, but the product surface and UX are distinct.
- Do not treat a marker-only data change as UI parity; inspect the real rendered hub and the AI/FAQ subroutes.
- Do not commit on an unrelated branch or with unrelated pre-existing dirty files; stop at verified worktree changes unless the branch/commit scope is clean.
