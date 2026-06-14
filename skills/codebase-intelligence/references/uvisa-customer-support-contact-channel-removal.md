# Scoped reference: UVISA customer-support contact channel removal

Scope/applicability: this reference is only for the UVISA frontend repository’s C-side customer-support hub and related tests. Anti-condition: do not apply these repository paths, labels, or channel names to unrelated projects; for other products, use the generic row-removal pattern and re-discover the actual component, API contract, and tests first.

Use when a UVISA C-side customer-support page must remove one contact channel (for example WeChat) without disturbing the rest of the support hub.

## Pattern

1. Locate the page component first (`src/screens/me/CustomerServiceScreen.tsx` for the C-side hub) and identify whether the row is static UI, backend-driven config, or both.
2. Remove the row from rendering, but also remove its local data read/copy handler so a backend field like `wechat` cannot still leak into the page.
3. Remove dead icon branches and enum members if the channel had a dedicated icon variant.
4. Keep the backend DTO/service contract stable unless the user explicitly asks to change API shape; this avoids breaking other surfaces that may still read the same config field.
5. Update page tests with negative assertions:
   - the removed label is absent in loading and loaded states;
   - a mocked backend value for the removed channel is absent after fetch resolves;
   - remaining channels (online consult, phone, email, FAQ) still render.
6. Run the targeted page test and build gate.

## Example verification

- `pnpm exec vitest run src/screens/me/__tests__/CustomerServiceScreen.test.tsx --reporter=dot`
- `pnpm run build`

## Pitfalls

- Do not only hide the label while still reading/copying the removed backend field.
- Do not remove unrelated support channels or the service-hours skeleton loading behavior.
- Do not delete i18n keys globally unless a repository-wide search proves no other screen uses them; stale unused i18n keys are safer than breaking another route during a narrow UI removal.
