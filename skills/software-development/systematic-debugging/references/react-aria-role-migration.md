# React ARIA Role Migration — Test Selector Cascade Pitfall

## Trigger
Tests fail after replacing one interactive component with another (e.g. `<Link>` → `<button>`/`<CtaBtn>`, `<a>` → `<button>`, `<div onClick>` → `<button>`).

## Root Cause
Testing Library's `getByRole()` resolves based on the **rendered HTML element**, not the React component name. When you swap:

| Before | After | Test role breaks |
|--------|-------|-----------------|
| `<Link to="...">` (renders `<a>`) | `<button onClick={...}>` | `getByRole('link')` → `getByRole('button')` |
| `<a href="...">` | `<CtaBtn>` (renders `<button>`) | `getByRole('link')` → `getByRole('button')` |
| `<div onClick>` | `<button>` | no role → `getByRole('button')` |
| `<button>` | `<a href>` | `getByRole('button')` → `getByRole('link')` |

## Diagnosis
1. Read the failing test assertion — note which `getByRole` / `queryByRole` it uses
2. Read the component change — what HTML element does the new component render?
3. Update the role in the test to match the new rendered element

## UVISA Example (2026-05-30, Lark cf5c1057)
NotificationDetailScreen migrated CTA from `<Link>` to `<CtaBtn>` (button).

**Before:**
```tsx
fireEvent.click(screen.getByRole('link', { name: '查看相关业务' }));
expect(screen.queryByRole('link', { name: '查看相关业务' })).not.toBeInTheDocument();
```

**After:**
```tsx
fireEvent.click(screen.getByRole('button', { name: '查看相关业务' }));
expect(screen.queryByRole('button', { name: '查看相关业务' })).not.toBeInTheDocument();
// Also: no-target fallback now shows a button, not absent
expect(screen.getByRole('button', { name: '返回消息中心' })).toBeInTheDocument();
```

## Prevention
When doing component migration PRs, grep all test files for `getByRole` / `queryByRole` referencing the old component's role before committing. One `search_files` call catches all cascading failures.
