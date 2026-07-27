# Verification Report — Local Synthetic Journey Probe

Scope: `17-synthetic-journey-probes` only.
Truth status: locally verified candidate; not global Agent OS certification.

## Deterministic tests

Command:

```text
python3 -m unittest -v test_synthetic_probe.py
python3 -m py_compile synthetic_probe.py test_synthetic_probe.py
```

Latest result: 13 tests passed; `py_compile` passed.

Covered negative cases:

- absolute target rejected;
- parent traversal rejected;
- target symlink rejected;
- oversized target rejected;
- unknown adapter rejected before execution;
- assertion mismatch fails closed;
- output outside receipt directories rejected;
- output path traversal rejected;
- capability source overwrite rejected;
- AST check finds no network/model/command adapter import or dynamic command execution call.

## Default-off evidence

Command:

```text
python3 synthetic_probe.py --probe probes/agent-os-doctor-readback.json
```

Readback:

```text
ok=true
status=validated
would_execute=false
executed=false
steps=[]
journey_target_read_attempts=0
journey_target_reads_succeeded=0
side_effects_observed=[local_read]  # probe contract and runner evidence only; no journey target read
```

## Live local-read evidence

Command:

```text
python3 synthetic_probe.py \
  --probe probes/agent-os-doctor-readback.json \
  --run \
  --out evidence/agent-os-doctor-readback-live.json
```

Readback:

```text
ok=true
status=pass
executed=true
step=doctor-current:pass
assertion ok=true: pass
assertion findings=[]: pass
external/lifecycle/scheduler/model/learning/command/secret negative assertions: all true
global_certification_claimed=false
```

Evidence artifact:

```text
/Users/charles/.hermes/workflows/projects/hermes-agent-os-control-plane/17-synthetic-journey-probes/evidence/agent-os-doctor-readback-live.json
```

Evidence binding:

```text
runner_sha256=d317c562b82d0b4b99d542f5d1ec65f2d6beafa9d9a4018a118c4105ef8c9cb3
probe_file_sha256=8dab8b5584590d49931f0ff89290c0d7571d28dc3edb895100b6c938c1cd3e34
probe_contract_sha256=50ef63da5f780070cef1f36956b324d58ca1d198bcb1bf06141efde8541be323
target_sha256=b6de5f63025f91970cceaea679404336908fa5791e4013502534165f50344c36
evidence_file_sha256=ac111a34439976d40bcb2c9c8c84c7ebfad74bfe07c98624ad79673c7a921658
```

## Remaining boundaries

- Independent reviewer vote pending at report creation.
- No Agent OS CLI, procedure registry, cron, Taskpool, Gateway, browser, or external-delivery integration was opened.
- Passing this probe proves only the named local doctor projection assertions at the recorded artifact digest and time.
