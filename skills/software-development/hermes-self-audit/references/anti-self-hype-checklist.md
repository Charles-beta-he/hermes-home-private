# Anti-Self-Hype Checklist & Honest Scoring

Reference material for the `hermes-self-audit` skill. Provides detailed methodology for honest self-assessment and avoiding inflated claims.

## Honest Scoring Framework

### Scoring Scale

| Score | Meaning | Evidence Required |
|-------|---------|-------------------|
| 1-3 | Broken/Missing | Component doesn't exist or crashes on basic use |
| 4-5 | Partial/Unstable | Exists but untested, unverified, or disconnected |
| 6-7 | Functional | Tested, integrated, but has known gaps |
| 8-9 | Production-ready | Full test coverage, documented, battle-tested |
| 10 | Exemplary | Industry benchmark quality |

### Scoring Rules

1. **Start at 5** (assume average), then adjust up/down with evidence
2. **Never score above 6** without test coverage > 50%
3. **Never score above 8** without integration tests + documentation
4. **Never score 10** — there's always room for improvement
5. **Each score must cite specific evidence** (test results, metrics, user feedback)

### Score Evidence Template

```markdown
## Component: <name>
- Score: <N>/10
- Evidence:
  - [ ] Test coverage: <X>% (from pytest --cov)
  - [ ] Integration test: <pass/fail>
  - [ ] Documentation: <exists/missing>
  - [ ] Error handling: <comprehensive/basic/none>
  - [ ] Performance: <benchmarked/untested>
- Adjustments:
  - +1 for <specific improvement>
  - -2 for <specific gap>
- Final justification: <why this score>
```

## Self-Hype Detection Patterns

### Pattern 1: Version Inflation

**Symptom**: Bumping major version for minor changes
**Example**: "Version 2.0.0" when only adding a few files
**Fix**: Follow semver strictly. Major = breaking changes, Minor = new features, Patch = fixes.

### Pattern 2: File Count Progress

**Symptom**: "Created 10 files" as achievement
**Example**: "I created 10 new files today" without mentioning if they work
**Fix**: Count working features, not files. A single working feature > 10 empty files.

### Pattern 3: Architecture Worship

**Symptom**: Beautiful diagrams ≠ working system
**Example**: Drawing a perfect architecture diagram but never implementing it
**Fix**: Require end-to-end test that proves the architecture works.

### Pattern 4: Premature Completion

**Symptom**: "All tests pass" when no tests exist
**Example**: Claiming tests pass without actually running tests
**Fix**: Verify test existence before claiming. Run tests and show output.

### Pattern 5: Echo Chamber Validation

**Symptom**: Only checking your own work
**Example**: Running your own code and claiming it works
**Fix**: Use external verification (tests, curl, screenshots, user feedback).

## Dynamic Self-Check Flow

### Phase 1: Existence Check

```bash
# Does the code actually exist?
find . -name "*.py" -newer .git/HEAD -exec python3 -m py_compile {} \;

# Does it have tests?
find . -name "test_*.py" | wc -l

# Is there documentation?
find . -name "*.md" | wc -l
```

### Phase 2: Integration Check

```bash
# Can it run?
python3 -c "import module_name"

# Does it connect to dependencies?
curl -s http://localhost:PORT/health

# Does it handle errors?
python3 -c "
try:
    import module_name
    module_name.function_that_should_fail()
except Exception as e:
    print(f'Error handling works: {e}')
"
```

### Phase 3: Evidence Check

```bash
# Run actual tests (not just syntax check)
python3 -m pytest tests/ -v --tb=short

# Check test coverage
python3 -m pytest --cov=module --cov-report=term-missing

# Verify integration
curl -s -X POST http://localhost:PORT/endpoint \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```

### Phase 4: Honest Assessment

For each component:
1. Score using Honest Scoring Framework
2. List specific evidence for each score
3. Identify what's actually missing
4. Don't list "planned" features as existing

### Phase 5: Report Generation

```markdown
# Honest Assessment Report

## Component Scores

| Component | Score | Evidence | Gaps |
|-----------|-------|----------|------|
| <name> | <N>/10 | <evidence> | <gaps> |

## Gap Analysis

| Claimed | Actually Exists | Verified |
|---------|-----------------|----------|
| <feature> | <yes/no> | <how verified> |

## Readiness Assessment

- **Production Ready**: <yes/no>
- **Test Coverage**: <X>%
- **Documentation**: <complete/partial/missing>
- **Integration**: <verified/unverified>

## Next Actions

1. <specific action with evidence>
2. <specific action with evidence>
```

## Multi-Model Honest Assessment

When using multiple models for assessment, ensure each model:
1. Provides specific evidence (not opinions)
2. Scores using the same framework
3. Identifies gaps (not just strengths)
4. Suggests concrete improvements (not vague goals)

### Model A: Architecture Analysis
- Focus: Component integration, data flow, interface consistency
- Evidence: Integration test results, data consistency checks

### Model B: Code Quality Analysis
- Focus: Test coverage, error handling, documentation
- Evidence: Test results, lint output, documentation completeness

### Model C: Usability Analysis
- Focus: User experience, deployment difficulty, maintenance cost
- Evidence: User feedback, deployment logs, maintenance history

## Synthesis Rules

1. **Consensus > 2 models**: If 2+ models agree on a gap, it's real
2. **Evidence > Opinion**: A model with evidence beats a model with opinion
3. **Specific > Vague**: "Missing unit tests for X" > "needs improvement"
4. **Actionable > Theoretical**: "Add pytest for X" > "improve quality"

## Common Anti-Patterns

### Anti-Pattern 1: Self-Validation
**Problem**: Running your own code and claiming it works
**Fix**: Use external verification (tests, curl, screenshots)

### Anti-Pattern 2: Selective Reporting
**Problem**: Only reporting successes, hiding failures
**Fix**: Report both successes AND failures with equal detail

### Anti-Pattern 3: Future Claims
**Problem**: Claiming features that will be implemented
**Fix**: Only claim what exists NOW, not what's planned

### Anti-Pattern 4: Metric Gaming
**Problem**: Choosing metrics that make you look good
**Fix**: Use standard metrics (test coverage, response time, error rate)

### Anti-Pattern 5: Echo Chamber
**Problem**: Only validating with yourself
**Fix**: Use external validation (tests, user feedback, third-party tools)
