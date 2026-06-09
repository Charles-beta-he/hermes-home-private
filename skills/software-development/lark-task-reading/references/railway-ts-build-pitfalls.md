# Railway TypeScript Build Pitfalls

## `tsc -b` vs `tsc --noEmit`: unused re-exports

Railway frontend builds (e.g. uvisa-app) use `tsc -b && vite build` per `package.json` scripts. Local dev checks often use `tsc --noEmit`. These behave differently under `noUnusedLocals: true`.

**Symptom:** Local `tsc --noEmit` passes but Railway `tsc -b` fails with:
```
error TS6133: '<TypeName>' is declared but its value is never read.
```

**Root cause:** `export type { X }` re-exports are treated as "uses" by `tsc --noEmit` but NOT by `tsc -b` (build mode). This is a TypeScript compiler behavioral difference between incremental build mode and type-check-only mode.

**Fix:** Remove the unused type import from the import statement. If the type needs to be re-exported for consumer convenience, import it from the source module directly:
```ts
// Before (fails tsc -b):
import { useStore, type Foo } from "./store";
export type { Foo } from "./store";  // tsc -b sees Foo as unused import

// After (passes tsc -b):
import { useStore } from "./store";
export type { Foo } from "./store";  // no unused import, re-export imports directly
```

**Verification:** Always run `npx tsc -b` locally (not just `tsc --noEmit`) before pushing frontend changes to Railway. The build mode check is stricter and matches Railway's actual build command.

**Date learned:** 2026-05-30 (task t103976 / Railway deploy of uvisa-app)

## General Railway build debugging checklist

1. Check the Railway build log for the exact error (TS error, Vite error, missing dep, etc.)
2. Reproduce locally with the SAME command Railway uses (read `package.json` scripts)
3. `tsc -b` is stricter than `tsc --noEmit` — always use the build-mode command
4. After fixing, `npx tsc -b && npx vitest run` before push
5. Monitor with `railway service status --all --json` after push
6. Smoke check the production URL: `curl -s -o /dev/null -w "%{http_code}" <url>`
