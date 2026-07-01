# Step 0.7: Multi-Author Coordination

Extracted from `/Users/charles/.hermes/skills/.archive/curator-umbrella-2026-06-10/research/research-paper-writing/SKILL.md` on 2026-07-01T08:56:29.614759+00:00 during full core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

### Step 0.7: Multi-Author Coordination

Most papers have 3-10 authors. Establish workflows early:

| Workflow | Tool | When to Use |
|----------|------|-------------|
| **Overleaf** | Browser-based | Multiple authors editing simultaneously, no git experience |
| **Git + LaTeX** | `git` with `.gitignore` for aux files | Technical teams, need branch-based review |
| **Overleaf + Git sync** | Overleaf premium | Best of both — live collab with version history |

**Section ownership**: Assign each section to one primary author. Others comment but don't edit directly. Prevents merge conflicts and style inconsistency.

```
Author Coordination Checklist:
- [ ] Agree on section ownership (who writes what)
- [ ] Set up shared workspace (Overleaf or git repo)
- [ ] Establish notation conventions (before anyone writes)
- [ ] Schedule internal review rounds (not just at the end)
- [ ] Designate one person for final formatting pass
- [ ] Agree on figure style (colors, fonts, sizes) before creating figures
```

**LaTeX conventions to agree on early**:
- `\method{}` macro for consistent method naming
- Citation style: `\citet{}` vs `\citep{}` usage
- Math notation: lowercase bold for vectors, uppercase bold for matrices, etc.
- British vs American spelling

---
