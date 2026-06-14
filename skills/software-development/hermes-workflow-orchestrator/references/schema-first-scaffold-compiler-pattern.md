# Schema-first scaffold compiler pattern

Applicability: use this reference for Hermes Workflow Pack / Agent Card / app-scaffold design when a user asks to turn a natural-language request into a reproducible workflow or project scaffold. It is a class-level pattern; external scaffold tools are evidence examples only.

Anti-conditions: do not use this reference as authority to install a specific third-party CLI, register an MCP server, create a real project, or replace Hermes taskpool/evidence-ledger authority. Re-read the target tool's live schema/docs before execution.

## Principle

Natural language is intake, not configuration. Before creating files, registering tools, installing dependencies, or deploying anything, compile the request into explicit schema-validated config and show a dry-run/proposal.

## Compiler chain

```text
intent intake
→ schema introspection
→ explicit config generation
→ compatibility validation
→ dry-run / plan artifact
→ human or policy gate
→ write / install / deploy
→ read-back verification
→ reproducible lock/config
```

## Design requirements

- Runtime schema introspection: the builder/tool should expose its current input shapes so agents do not hardcode stale option lists.
- Full explicit config: avoid hidden defaults for major decisions. Empty arrays/`none` should be explicit.
- Compatibility matrix: reject invalid combinations before dispatch or writes.
- Plan-before-create: non-mutating preview is mandatory for file writes, tool registration, dependency installs, MCP setup, or deploy.
- Reproducible lock/config: record schema version, selected modules, generated command/config, package manager, install/deploy choices, and later add-on mutations.
- Add-on mutation path: adding modules later should validate against the existing lock/config, not infer project state from marketing docs or partial prompts.

## Hermes mapping

For Workflow Pack / Agent Card generation, make these explicit:

```yaml
workflow_scaffold:
  objective: null
  inputs: []
  outputs: []
  modules: []
  tools: []
  write_surfaces: []
  external_side_effects: []
  model_routing: {}
  evidence_gates: []
  human_gates: []
  retry_policy: {}
  closeout_policy: {}
  observability: {}
  schedule: null
  install_required: false
  deploy_required: false
  package_or_runtime: null
  lockfile_path: null
```

## Red lines

- Do not treat a scaffold generator as the long-running workflow runtime.
- Do not install MCP servers, dependencies, editor plugins, or generated apps during research/intake.
- Do not let generated app config replace taskpool/evidence ledger authority.
- Do not proceed from dry-run to write/install/deploy without an explicit gate.
- Do not freeze one session's option list as a permanent rule; re-read schema/docs when executing.
