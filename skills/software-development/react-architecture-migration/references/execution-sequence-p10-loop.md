# React Migration Execution Sequence with P10 Loop

Extracted from `/Users/charles/.hermes/skills/software-development/react-architecture-migration/SKILL.md` on 2026-07-01T08:52:42.874486+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## Execution Sequence (Loop with P10 Self-Check Each Round)

### Round 1: Foundation
1. `npm i zustand axios`
2. Create `src/lib/api.ts` — Axios with auth interceptor
3. Create all `src/services/*.service.ts` — one per domain
4. Create all `src/stores/*.store.ts` — Zustand stores with loading/error
5. Create `mock-server/` — Express with all endpoints
6. Update `vite.config.ts` — API proxy to mock server
7. `node node_modules/typescript/bin/tsc --noEmit` verify

### Round 2: Screen Migration
1. Remove `import { ... } from '../data/mock'` from all screens
2. Add store/service imports
3. Replace hardcoded constants with store hooks
4. Use `useEffect` for data fetching
5. `tsc --noEmit` verify

### Round 3: Multi-Model Review (SMALL SCOPE)
Delegate 3 parallel subagents — **5-8 files each max**:
- Agent 1: API/Service layer review
- Agent 2: Screen layer review (sample screens)
- Agent 3: Security/Performance review
Fix all CRITICAL/HIGH issues found.

### Round 4: Dark Mode + Skeleton + Error Boundary
1. `src/stores/theme.store.ts` — persist to localStorage, set data-theme
2. Add `dark:` Tailwind variants to ALL components
3. Create `SkeletonScreen.tsx` with page-specific patterns
4. Create `ErrorBoundary.tsx` — 3 level (app/screen/component)
5. Wire into `App.tsx` — lazy + Suspense + ErrorBoundary

### Round 5: i18n + PWA + Monitoring
1. `npm i react-i18next i18next i18next-browser-languagedetector`
2. Create `src/i18n/` with zh/en JSON
3. Migrate screens to `useTranslation()` — use batch script (see below)
4. `npm i -D vite-plugin-pwa` + configure
5. `npm i @sentry/react web-vitals`
6. Create `sentry.ts`, `vitals.ts`, `analytics.ts`

### Round 6: Testing + Final Audit
1. `npm i -D vitest @testing-library/react @testing-library/jest-dom jsdom`
2. Create test files for stores and utilities
3. Programmatic completeness audit

### i18n Overflow Audit (After Migration)

After i18n migration, run 3 parallel subagents (5-8 files each):
- Agent 1: Screen audit — check fixed-width containers, missing truncation, flex without min-w-0
- Agent 2: Length audit — compare zh vs en string lengths, flag >4x ratios
- Agent 3: CSS audit — check Tailwind for missing truncate, overflow-hidden on grids

Critical overflow patterns:
- 4-column action grids (grid-cols-4): add `truncate` + `overflow-hidden` to labels
- Tab bars: "Quantitative" (12 chars) crowds narrow cells — add `max-w` or `truncate`
- Section titles: "Cross-border Remittance (SWIFT / E-wallet / Crypto)" = 51 chars
- Always add `min-w-0 truncate` to flex children containing text
- Currency names: use bilingual `{ zh, en }` pattern or i18n keys

### Programmatic i18n Fix (When Subagent Times Out)

When subagent times out on i18n text replacement, use `execute_code`:

```python
import os, re
for root, dirs, files in os.walk('src/screens'):
    for f in files:
        if not f.endswith('.tsx'): continue
        fp = os.path.join(root, f)
        content = open(fp).read()
        if 'useTranslation' in content: continue
        # Add import + hook call programmatically
        lines = content.split('\n')
        last_import = max(i for i, l in enumerate(lines) if l.startswith('import '))
        lines.insert(last_import + 1, 'import { useTranslation } from "react-i18next";')
        content = '\n'.join(lines)
        match = re.search(r'(export default function \w+\([^)]*\)\s*\{)', content)
        if match:
            content = content[:match.end()] + '\n  const { t } = useTranslation();' + content[match.end():]
        open(fp, 'w').write(content)
```

Then do common string replacement in a second pass, and add new i18n keys to zh.json/en.json.

### i18n Batch Migration (When Subagents Timeout)

**Subagents timeout on 55-file migrations.** Use `execute_code`:

```python
import os, re
base = "/path/to/src/screens"
for root, dirs, files in os.walk(base):
    for f in files:
        if not f.endswith('.tsx'): continue
        fp = os.path.join(root, f)
        content = open(fp).read()
        if 'useTranslation' in content: continue
        lines = content.split('\n')
        last_import = max(i for i, l in enumerate(lines) if l.startswith('import '))
        lines.insert(last_import + 1, 'import { useTranslation } from "react-i18next";')
        content = '\n'.join(lines)
        match = re.search(r'(export default function \w+\([^)]*\)\s*\{)', content)
        if match:
            content = content[:match.end()] + '\n  const { t } = useTranslation();' + content[match.end():]
        open(fp, 'w').write(content)
```

Then do text replacement for common Chinese strings in a second pass.
