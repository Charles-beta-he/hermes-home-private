# Step 2.5: Design Human Evaluation (If Applicable)

Extracted from `/Users/charles/.hermes/skills/.archive/curator-umbrella-2026-06-17/research/references/absorbed/research-paper-writing/SKILL.md` on 2026-07-01T08:56:29.614759+00:00 during full core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

### Step 2.5: Design Human Evaluation (If Applicable)

Many NLP, HCI, and alignment papers require human evaluation as primary or complementary evidence. Design this before running automated experiments — human eval often has longer lead times (IRB approval, annotator recruitment).

**When human evaluation is needed:**
- Automated metrics don't capture what you care about (fluency, helpfulness, safety)
- Your contribution is about human-facing qualities (readability, preference, trust)
- Reviewers at NLP venues (ACL, EMNLP) expect it for generation tasks

**Key design decisions:**

| Decision | Options | Guidance |
|----------|---------|----------|
| **Annotator type** | Expert, crowdworker, end-user | Match to what your claims require |
| **Scale** | Likert (1-5), pairwise comparison, ranking | Pairwise is more reliable than Likert for LLM outputs |
| **Sample size** | Per annotator and total items | Power analysis or minimum 100 items, 3+ annotators |
| **Agreement metric** | Cohen's kappa, Krippendorff's alpha, ICC | Krippendorff's alpha for >2 annotators; report raw agreement too |
| **Platform** | Prolific, MTurk, internal team | Prolific for quality; MTurk for scale; internal for domain expertise |

**Annotation guideline checklist:**
```
- [ ] Clear task description with examples (good AND bad)
- [ ] Decision criteria for ambiguous cases
- [ ] At least 2 worked examples per category
- [ ] Attention checks / gold standard items (10-15% of total)
- [ ] Qualification task or screening round
- [ ] Estimated time per item and fair compensation (>= local minimum wage)
- [ ] IRB/ethics review if required by your institution
```

**Reporting requirements** (reviewers check all of these):
- Number of annotators and their qualifications
- Inter-annotator agreement with specific metric and value
- Compensation details (amount, estimated hourly rate)
- Annotation interface description or screenshot (appendix)
- Total annotation time

See [references/human-evaluation.md](references/human-evaluation.md) for complete guide including statistical tests for human eval data, crowdsourcing quality control patterns, and IRB guidance.

---
