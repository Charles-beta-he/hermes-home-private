# Development Brain Profile v0.2.0

Default software-development rules:
- Start from project profile or repository context.
- For bugfixes, reproduce or inspect evidence first.
- Prefer small verified slices unless user asks for architecture-level landing.
- Do not push project code unless explicitly requested; Hermes/self backup can be pushed when safe.
- Treat project/code/product/document queries as entry-point investigations by default: expand to associated producers, transformers, consumers, routes, permissions, KPIs/badges, tests, and runtime evidence unless the user explicitly asks for a narrow lookup.
- If full associated-surface coverage is not completed, name the unchecked surfaces instead of implying closure.

Agent-facing tooling rules:
- When a CLI/script exposes structured output, prefer the machine-readable contract over prose. Record the command, schemaVersion/contract version, required fields, and failure shape before agents depend on it.
- When a tool ships version-specific guidance from its own binary, load workflow/help/schema/diagnostics from the exact binary/environment that will execute the project. Static docs are secondary unless the tool has no discoverable contract.
- Treat unfamiliar compilers, eval harnesses, generated artifacts, and untrusted examples as sandbox/disposable-workspace work by default.
- Repair automation is plan-first: require diagnostic/issue id, safety label, affected surface, and retest evidence before applying or claiming behavior preservation.
- Optimization claims require a budget/readiness artifact or before/after metric, not just subjective code cleanliness.
