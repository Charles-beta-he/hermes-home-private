---
name: pytorch-fsdp
description: Use when you need guidance on expert guidance for Fully Sharded Data Parallel training with PyTorch FSDP - parameter sharding, mixed precision, CPU offloading, FSDP2.
version: 1.0.0
author: Orchestra Research
license: MIT
dependencies:
- torch>=2.0
- transformers
metadata:
  hermes:
    tags:
    - Distributed Training
    - PyTorch
    - FSDP
    - Data Parallel
    - Sharding
    - Mixed Precision
    - CPU Offloading
    - FSDP2
    - Large-Scale Training
    related_skills:
    - brand
    - github
    - guidance
    - loop
    - maps
    - outlines
    - plan
---

# Pytorch-Fsdp Skill

## Overview


Comprehensive assistance with pytorch-fsdp development, generated from official documentation.

## When to Use
This skill should be triggered when:
- Working with pytorch-fsdp
- Asking about pytorch-fsdp features or APIs
- Implementing pytorch-fsdp solutions
- Debugging pytorch-fsdp code
- Learning pytorch-fsdp best practices


- Don't use for: tasks outside this skill's trigger class, requests with a more specific neighboring skill, or situations where required evidence/tooling is unavailable.
## Quick Reference

The generated quick-reference patterns from official PyTorch distributed/FSDP documentation were moved to `references/quick-reference-patterns.md` to keep the root skill loadable. Load that file when the user specifically needs API examples, distributed initialization details, join context manager notes, process-group examples, NCCL ordering caveats, or DDP static-graph details.

Default first response for FSDP work should still start with current project constraints: model size, GPU count/type, interconnect, PyTorch version, launcher, precision target, checkpointing plan, and failure symptoms.

## Reference Files

This skill includes comprehensive documentation in `references/`:

- **other.md** - Other documentation

Use `view` to read specific reference files when detailed information is needed.

## Working with This Skill

### For Beginners
Start with the getting_started or tutorials reference files for foundational concepts.

### For Specific Features
Use the appropriate category reference file (api, guides, etc.) for detailed information.

### For Code Examples
The quick reference section above contains common patterns extracted from the official docs.

## Resources

### references/
Organized documentation extracted from official sources. These files contain:
- Detailed explanations
- Code examples with language annotations
- Links to original documentation
- Table of contents for quick navigation

### scripts/
Add helper scripts here for common automation tasks.

### assets/
Add templates, boilerplate, or example projects here.

## Notes

- This skill was automatically generated from official documentation
- Reference files preserve the structure and examples from source docs
- Code examples include language detection for better syntax highlighting
- Quick reference patterns are extracted from common usage examples in the docs

## Updating

To refresh this skill with updated documentation:
1. Re-run the scraper with the same configuration
2. The skill will be rebuilt with the latest information

## Common Pitfalls

1. Loading this skill outside its trigger class and skipping a simpler, more direct path.
2. Ignoring prerequisites such as platform, credentials, installed commands, or linked reference files.
3. Treating the skill as a static memo instead of verifying the exact commands, artifacts, or outputs in the current environment.

## Verification Checklist

- [ ] The task actually matches this skill's trigger class and the current route is still appropriate.
- [ ] All prerequisites, linked references, templates, scripts, and required tools have been checked before execution.
- [ ] Claimed outputs, commands, files, or external side-effects were read back or otherwise verified before completion.
