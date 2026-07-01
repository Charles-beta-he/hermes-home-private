# Step 1.3: Verify Every Citation

Extracted from `/Users/charles/.hermes/skills/.archive/curator-umbrella-2026-06-17/research/references/absorbed/research-paper-writing/SKILL.md` on 2026-07-01T08:56:29.614759+00:00 during full core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

### Step 1.3: Verify Every Citation

**NEVER generate BibTeX from memory. ALWAYS fetch programmatically.**

For each citation, follow the mandatory 5-step process:

```
Citation Verification (MANDATORY per citation):
1. SEARCH → Query Semantic Scholar or Exa MCP with specific keywords
2. VERIFY → Confirm paper exists in 2+ sources (Semantic Scholar + arXiv/CrossRef)
3. RETRIEVE → Get BibTeX via DOI content negotiation (programmatically, not from memory)
4. VALIDATE → Confirm the claim you're citing actually appears in the paper
5. ADD → Add verified BibTeX to bibliography
If ANY step fails → mark as [CITATION NEEDED], inform scientist
```

```python
# Fetch BibTeX via DOI
import requests

def doi_to_bibtex(doi: str) -> str:
    response = requests.get(
        f"https://doi.org/{doi}",
        headers={"Accept": "application/x-bibtex"}
    )
    response.raise_for_status()
    return response.text
```

If you cannot verify a citation:

```latex
\cite{PLACEHOLDER_author2024_verify_this}  % TODO: Verify this citation exists
```

**Always tell the scientist**: "I've marked [X] citations as placeholders that need verification."

See [references/citation-workflow.md](references/citation-workflow.md) for complete API documentation and the full `CitationManager` class.
