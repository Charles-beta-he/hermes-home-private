# Surgical Per-File Revert from a Multi-File Commit

## When to Use

A single commit touched multiple files, but only SOME of them need reverting.
`git revert <sha>` would undo the entire commit including changes you want to keep.

Example: commit b6ef487 changed CardScreen.tsx (bad) and CardWithdrawScreen.tsx (good).
Only CardScreen needed reverting.

## Workflow

### 1. Inspect the commit

```bash
# See which files the commit touched
git show --stat <sha>

# See the diff for a specific file
git diff <sha>^..<sha> -- src/path/to/file.tsx
```

### 2. Revert specific files to pre-commit state

```bash
# Checkout individual files to the parent of the commit
git checkout <sha>^ -- src/screens/card/CardScreen.tsx
git checkout <sha>^ -- src/screens/card/__tests__/CardScreen.test.tsx
```

Key: `<sha>^` = parent commit = the state before this commit.
Only list the files you want to revert; other files from the same commit are untouched.

### 3. Also revert associated test files

If the commit added or modified tests for the reverted feature, revert those too.
Tests that assert on removed behavior will fail if left in place.

### 4. Verify

```bash
npx tsc --noEmit --pretty
pnpm vitest run src/path/to/__tests__/
```

### 5. Commit, push, PR, merge

```bash
git add src/screens/card/CardScreen.tsx src/screens/card/__tests__/CardScreen.noCard.test.tsx
git commit -m "revert(card): remove restored flex tile from CardScreen (<sha short>)

Revert dailyHoldingTotal / isDailyHolding / flex tile restoration.
T7 Jetty #2 intentionally removed the flex tile — hero shows totalAmount.
Single tile only."

git push origin <branch>
gh pr create --repo <owner>/<repo> --base <target> --head <branch> \
  --title "revert(card): remove restored X" --body "..." --draft=false
gh pr merge <PR_NUMBER> --auto --merge --repo <owner>/<repo>
```

## Pitfalls

1. **Don't forget test files.** A reverted source file may import symbols that no longer
   exist, or tests may assert on removed behavior. Always check for associated test files.

2. **`git revert` vs `git checkout <sha>^ -- <file>`**: Use `git revert` when you want to
   undo the ENTIRE commit. Use `git checkout <sha>^ -- <file>` when you want surgical
   per-file control.

3. **Multiline commit messages in `execute_code`**: Build the message as a plain Python
   string variable, then pass to `terminal()`. Do NOT use Python f-strings if the message
   contains curly braces. Do NOT embed newlines directly in the `terminal()` call string —
   Python will choke on unterminated string literals.

   ```python
   msg = "revert(card): remove restored flex tile\n\nDetailed explanation."
   terminal(f"git commit -m '{msg}'", workdir=workdir)
   ```
