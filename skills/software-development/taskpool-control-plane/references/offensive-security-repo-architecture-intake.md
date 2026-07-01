# Offensive/security repo architecture-only taskpool intake

Use when the user asks to analyze, absorb, or add to taskpool an external repo whose advertised function includes pentesting, vulnerability scanning, exploitation, C2, credential attacks, or other offensive/security tooling.

## Applicability

- The source is useful as an architecture/control-plane reference, not as a tool to run.
- The requested outcome is Hermes/taskpool learning: side-effect gates, evidence schemas, workflow registries, dry-run/no-network harnesses, reporting structure, or safety validators.
- The user did not explicitly authorize live security testing, installation of offensive toolchains, credential use, or external side effects.

## Anti-conditions

- Do not run scanners, exploit tools, password/credential tooling, Docker compose stacks, or repo install scripts during intake.
- Do not probe live targets or use examples like `example.com` as real scan targets.
- Do not promote offensive execution to a default Hermes capability.
- Do not mark the repo production-ready based on README/demo claims alone.

## Intake procedure

1. Inspect source statically first: README/docs plus the concrete control-plane files that implement execution, validation, workflow discovery, result models, and reporting.
2. Write a durable evidence note under `~/.hermes/evidence/external-repos/` with:
   - source URL and inspected commit/path;
   - files/line ranges inspected;
   - absorbable patterns;
   - red lines and non-goals;
   - proposed taskpool classification.
3. Create the task with `brain_task_orchestrator.py add-repo-capability-absorption`, not generic `add`, and keep it `integration-level=evaluate` unless a separate human gate authorizes implementation.
4. Encode red lines explicitly: no live pentest, no network probing, no runtime install, no credential handling, no production adapter write-through.
5. Add acceptance criteria for architecture learning, not execution:
   - cite inspected source lines;
   - produce Hermes gap map;
   - define side-effect-gate / evidence-schema / workflow-registry contract;
   - define a no-network/dry-run test matrix.
6. After creation, read the task note back. The CLI may compress repeated `--accept` fields; patch both frontmatter `acceptance_criteria` and the body checklist if any criteria were lost.
7. Run taskpool health checks after creation: at minimum `selfcheck --json`, `proof-check --json`, and `next --reconcile --json`. Report whether an event hook routed the task to multimodel/running separately from any runtime execution; advisory multimodel routing is not permission to run the offensive repo.

## Suggested test matrix for later Hermes-native implementation

- command validator unit tests;
- workflow registry discovery/import-error tests;
- target/scope parser tests;
- blocked-command bypass tests;
- dashboard evidence schema tests;
- dry-run / no-network mode tests;
- read-back tests proving no external side effects occurred.

## Reporting language

Prefer: “P2 architecture absorption / static intake; absorb governance, evidence, registry, and test patterns.”

Avoid: “installed”, “ready to run”, “pentest capability added”, or any wording that implies offensive execution was enabled.
