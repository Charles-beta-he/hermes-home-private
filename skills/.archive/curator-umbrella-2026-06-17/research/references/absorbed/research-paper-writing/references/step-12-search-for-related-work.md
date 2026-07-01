# Step 1.2: Search for Related Work

Extracted from `/Users/charles/.hermes/skills/.archive/curator-umbrella-2026-06-17/research/references/absorbed/research-paper-writing/SKILL.md` on 2026-07-01T08:56:29.614759+00:00 during full core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

### Step 1.2: Search for Related Work

**Load the `arxiv` skill** for structured paper discovery: `skill_view("arxiv")`. It provides arXiv REST API search, Semantic Scholar citation graphs, author profiles, and BibTeX generation.

Use `web_search` for broad discovery, `web_extract` for fetching specific papers:

```
# Via web_search:
web_search("[main technique] + [application domain] site:arxiv.org")
web_search("[baseline method] comparison ICML NeurIPS 2024")

# Via web_extract (for specific papers):
web_extract("https://arxiv.org/abs/2303.17651")
```

Additional search queries to try:

```
Search queries:
- "[main technique] + [application domain]"
- "[baseline method] comparison"
- "[problem name] state-of-the-art"
- Author names from existing citations
```

**Recommended**: Install **Exa MCP** for real-time academic search:
```bash
claude mcp add exa -- npx -y mcp-remote "https://mcp.exa.ai/mcp"
```
