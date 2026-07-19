# Theory-to-Engineering Map

Load this reference only when theoretical provenance, method selection, or core works are directly relevant. Routine inquiry should use the root protocol without loading this file.

## Methods and operational projections

| Tradition | Durable insight | Engineering projection | Boundary / misuse |
|---|---|---|---|
| C. S. Peirce: abduction, deduction, induction | Generate an explanation, derive consequences, test them | hypothesis -> discriminating prediction -> observation -> update | Abduction generates or ranks explanations; it does not establish truth by itself |
| Karl Popper: conjectures and refutations | Informative claims must risk failure | explicit falsifier, adversarial test, counterexample search | Failure to falsify is not verification; probabilistic and auxiliary assumptions complicate simple refutation |
| Chamberlin: multiple working hypotheses | Avoid affection for the first explanation | maintain H1/H2/H0 and compare predictions | Do not add decorative alternatives with no mechanism or distinct prediction |
| John Platt: strong inference | Prefer experiments that exclude alternatives | sequence decisive/discriminating probes | Many complex systems cannot provide one decisive experiment; use cumulative evidence honestly |
| Bayesian confirmation | Evidence changes relative confidence | likelihood-aware update, base rates, calibrated states | Avoid unsupported numeric probabilities and independence assumptions |
| John Dewey: theory of inquiry | Convert an indeterminate situation into an operationally resolved one | problemize before solving; revise the representation when evidence resists it | Not every normative disagreement has an empirical resolution |
| R. A. Fisher / design of experiments | Valid inference depends on controls, randomization, replication, and design | control variables, identify confounders, preserve exact inputs | A well-designed synthetic test still cannot certify a different real boundary |
| Thomas Kuhn: anomalies and paradigms | Persistent anomalies may challenge the frame | escalate from local bug to representation/architecture review | Do not call every refactor a paradigm shift |
| Imre Lakatos: research programmes | Judge whether adjustments increase explanatory/predictive power or merely protect a failing core | track whether fixes predict new outcomes or accumulate exceptions | One failed test need not invalidate an architecture; repeated ad hoc patches are warning evidence |
| George Box: models as useful approximations | A model is judged against purpose and boundary | state scope, cost function, known limits, demotion conditions | "All models are wrong" is not permission for unvalidated guesses |
| Qian Xuesen: meta-synthesis | Combine qualitative expert judgment with quantitative and machine checks while preserving roles | source ledger + dissent ledger + engineering ledger + handback | Multi-model agreement is not quantitative proof or execution authority |

## Core works, prioritized

### Inquiry and explanation

- Charles S. Peirce, "The Fixation of Belief" and "How to Make Our Ideas Clear"; collected writings on abduction.
- John Dewey, *Logic: The Theory of Inquiry* and *How We Think*.
- Karl Popper, *The Logic of Scientific Discovery* and *Conjectures and Refutations*.
- T. C. Chamberlin, "The Method of Multiple Working Hypotheses".
- John R. Platt, "Strong Inference", *Science* 146 (1964).

### Evidence, experiments, and causality

- R. A. Fisher, *The Design of Experiments*.
- George E. P. Box, J. Stuart Hunter, William G. Hunter, *Statistics for Experimenters*.
- E. T. Jaynes, *Probability Theory: The Logic of Science*.
- Judea Pearl, *Causality*; Judea Pearl and Dana Mackenzie, *The Book of Why*.

### Scientific change and architecture escalation

- Thomas S. Kuhn, *The Structure of Scientific Revolutions*.
- Imre Lakatos, *The Methodology of Scientific Research Programmes*.
- Herbert A. Simon, *The Sciences of the Artificial*.
- Donald Schön, *The Reflective Practitioner*.

### Complex systems and meta-synthesis

- 钱学森等，《论系统工程》。
- 钱学森等关于开放复杂巨系统与“从定性到定量综合集成方法”的论文。
- 综合集成研讨厅（Hall for Workshop of Meta-Synthetic Engineering）相关研究。

## Selection guide

- Unknown technical cause: Peirce + Chamberlin/Platt + experimental design.
- High confirmation-bias risk: Popper + multiple working hypotheses.
- Noisy cumulative evidence: Bayesian update + causal reasoning.
- Wrong problem frame: Dewey + Kuhn.
- Repeated ad hoc repairs: Lakatos + architecture governance.
- Multi-expert/multi-model complex system: Qian meta-synthesis.

## Non-transfer rules

1. Scientific method does not determine values, legal permission, product taste, or authority.
2. Controlled experiments are not always ethical, possible, or representative.
3. Social and open complex systems may require triangulation, natural experiments, simulation, qualitative evidence, and explicit uncertainty rather than laboratory-style certainty.
4. Falsifiability is one quality criterion, not a complete universal demarcation algorithm.
5. Reproducibility is claim- and boundary-relative; replication of a local artifact does not imply universal generalization.
