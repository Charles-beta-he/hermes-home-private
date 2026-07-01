# Cross-Cutting Concern Recognition

Extracted from `/Users/charles/.hermes/skills/software-development/multi-model-thinking/SKILL.md` on 2026-07-01T08:22:36.087987+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## Cross-Cutting Concern Recognition (交叉关注点识别)

When a user or Lark task describes a **point fix** (e.g., "this input field accepts emoji"), the agent MUST classify the problem before executing:

1. **Point fix**: isolated to one screen/component, no similar patterns elsewhere → fix locally.
2. **Cross-cutting concern**: validation, security, error handling, data transforms, i18n, logging → must be implemented as **shared infrastructure**, not point fixes.

Classification signals:
- Same pattern duplicated in 2+ files (e.g., `cleanText()` in multiple screens)
- Existing shared infrastructure for the same concern (e.g., `validators.ts` already has `isValidEthAddress`)
- The fix prevents a class of problems, not a single instance
- Defense-in-depth requires the same rule at multiple layers (frontend + backend)

When a cross-cutting concern is identified, the correct action is:
1. Extract to shared infrastructure (e.g., `validators.ts`, `utils.ts`)
2. Update all existing consumers to use the shared version
3. Add tests at the infrastructure level
4. If backend exists, add matching validation as defense-in-depth

This pattern was established after the agent followed a Lark task literally ("fix bank name emoji validation at one location") without recognizing that validation is infrastructure. The user corrected: "有些对于项目属于基础设施或者常规限制，不能因为任务只说了一个地方就只改这一个地方."

**Theoretical grounding**: Kahneman's System 1 (literal task following) vs System 2 (architectural pattern recognition). Donella Meadows' leverage points: operate at "system structure" level, not "parameter tweaking." Pragmatic Programmer DRY principle.

For UVISA specifically: `src/lib/validators.ts` is the shared validation infrastructure location, `src/lib/utils.ts` is for general text utilities.
