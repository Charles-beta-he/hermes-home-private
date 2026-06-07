# Full-library routing eval coverage

Use this reference when a user explicitly asks to cover every skill with routing evals, not just improve one skill.

## Durable workflow

1. Run or build a contract-layer generator that only creates/updates `evals/prompts.csv`.
   - Required buckets per skill: 3 `positive`, 2 `neighbor`, 2 `forbidden`, 1 `no-load`.
   - Do not change `description` fields in the same bulk pass; descriptions are routing logic.
   - Do not bulk-rewrite SKILL.md bodies from heuristic labels.
2. Emit a manifest under `docs/private/` with counts for changed, preserved, skipped, and generated eval paths.
3. Re-run the non-mutating skill coverage scanner after generation.
4. Verify every discovered `SKILL.md` has a parseable `evals/prompts.csv` satisfying the bucket minimums.
5. Compile/check the scanner and generator scripts when they are Python or otherwise executable.
6. Run a secret scan or equivalent before committing, because generated prompts may accidentally echo sensitive examples from descriptions or references.
7. Stage only the generated eval files, manifest/report files, and the generator/scanner changes. Avoid sweeping unrelated skill-library drift into the commit.

## Submodule / nested repo handling

Skill libraries may contain nested git repositories or submodules. `git add` from the parent can fail with pathspec errors such as a path being inside a submodule.

When that happens:

1. Identify nested repos from `git status --short` and by running `git -C <nested> status --short`.
2. Commit generated eval files inside each nested repo first.
3. Return to the parent repo and stage only the submodule pointer update.
4. In verification, distinguish:
   - dirty generated eval paths inside the nested repo; versus
   - pre-existing unrelated nested-repo modifications.
5. Do not claim the whole submodule is clean if unrelated files were already dirty. Instead report that eval paths are clean and name the unrelated drift as out-of-scope.

## Boundary

Full eval coverage proves test-set presence, not router correctness. The next stage is a real router regression runner that executes positive/neighbor/forbidden/no-load prompts and records actual load behavior.
