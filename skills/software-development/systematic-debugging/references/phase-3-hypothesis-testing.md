# Systematic Debugging Phase 3 Hypothesis and Testing

Extracted from `/Users/charles/.hermes/skills/software-development/systematic-debugging/SKILL.md` on 2026-07-01T08:52:42.874486+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## Phase 3: Hypothesis and Testing

**Scientific method:**

### 1. Form a Single Hypothesis

- State clearly: "I think X is the root cause because Y"
- Write it down
- Be specific, not vague

### 2. Test Minimally (Isolation First for Destructive Tests)

- Make the SMALLEST possible change to test the hypothesis
- One variable at a time
- Don't fix multiple things at once

**For destructive tests (backup/restore, migrations, format conversions):**
- NEVER test on production data or active skill directories directly
- Copy the target to `/tmp` or a disposable workspace first
- Run the destructive operation against the copy
- Verify the outcome, then apply to the real target only after confirmation
- Clean up the temporary copy when done

### 3. Verify Before Continuing

- Did it work? → Phase 4
- Didn't work? → Form NEW hypothesis
- DON'T add more fixes on top

### 4. When You Don't Know

- Say "I don't understand X"
- Don't pretend to know
- Ask the user for help
- Research more

---
