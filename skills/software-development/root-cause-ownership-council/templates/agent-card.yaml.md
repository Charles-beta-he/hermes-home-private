# Agent Card Template

Use this template when adding a new council role or project-specific domain specialist.

```yaml
name: ""
version: "1.0.0"
role_type: framing|domain|skeptic|ownership|product-standard|evidence|implementation|regression|certification
trigger:
  positive:
    - ""
  negative:
    - ""
scope:
  owns:
    - ""
  does_not_own:
    - ""
inputs:
  required:
    - problem_brief
    - relevant_files_or_sources
  optional:
    - git_history
    - failing_tests
    - screenshots
    - api_readbacks
outputs:
  fields:
    - ""
evidence_required:
  minimum_quality: A|B|C|D
  accepted_sources:
    - tests
    - code
    - runtime_readback
    - screenshots
    - api_response
falsifiers:
  - ""
forbidden_actions:
  - "Do not execute side effects without explicit authorization."
  - "Do not treat model agreement as evidence."
handoff:
  receives_from:
    - ""
  sends_to:
    - ""
verification:
  - ""
```
