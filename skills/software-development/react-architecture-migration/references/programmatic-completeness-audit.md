# React Migration Programmatic Completeness Audit

Extracted from `/Users/charles/.hermes/skills/software-development/react-architecture-migration/SKILL.md` on 2026-07-01T08:53:45.426287+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## Programmatic Completeness Audit

After all rounds, run this to verify:

```python
import os, json

# 1. Infrastructure files
infra = ['api.ts', 'sentry.ts', 'vitals.ts', 'analytics.ts', 'haptics.ts',
         'validators.ts', 'pinGuard.ts', 'pinVerify.ts', 'exportUtils.ts',
         'featureFlags.ts', 'retry.ts', 'version.ts']
for f in infra:
    exists = os.path.exists(f'src/lib/{f}')
    print(f"  {'✓' if exists else '✗'} {f}")

# 2. Store middleware
for f in os.listdir('src/stores'):
    if f.endswith('.store.ts'):
        content = open(f'src/stores/{f}').read()
        has_persist = 'persist' in content
        has_devtools = 'devtools' in content
        print(f"  {f}: persist={has_persist} devtools={has_devtools}")

# 3. Screen adoption
for root, dirs, files in os.walk('src/screens'):
    for f in files:
        if not f.endswith('.tsx'): continue
        c = open(os.path.join(root, f)).read()
        has_i18n = 'useTranslation' in c
        # Check for remaining Chinese (acceptable: brand/bank/language names)
        import re
        chinese = re.findall(r'[\u4e00-\u9fff]+', c)
        # ... categorize and report
```
