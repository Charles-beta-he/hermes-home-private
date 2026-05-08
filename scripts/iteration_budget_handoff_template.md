# Iteration Budget Handoff Template

Use this template when a Hermes automation tick approaches or hits the LLM/tool iteration cap. The goal is to stop cleanly before an incomplete response becomes an ambiguous task state.

## Required fields

- task_id:
- claim_id_or_run_id:
- owner:
- generated_at:
- stop_reason: budget_near_limit | budget_exhausted | manual_gate | high_risk_gate | external_blocker | verifier_failed
- execution_mode: script_first_no_agent | tiny_summarizer | bounded_agent_tick | single_shot_capped | manual
- risk: low | medium | high
- budget:
  - agent_cap:
  - max_tool_calls:
  - safety_margin:
  - spent_tool_calls:
  - remaining_before_handoff:
- artifacts:
  - budget_tick_json:
  - logs:
  - proof:

## Gate checklist

- [ ] Task was selected from canonical local-brain task note, not from a derived dashboard.
- [ ] Reconcile ran before execution or the runner proved dispatch state was fresh.
- [ ] Claim command exists before any mutating work.
- [ ] Handoff artifact path is durable and can be searched later.
- [ ] Next bounded command is explicit and safe to resume.
- [ ] Done is blocked until structured evidence exists.

## Resume rules

1. Read the canonical task note and this handoff.
2. Run `brain_task_orchestrator.py reconcile --write --promote-due-retry --json`.
3. Re-run `iteration_budget_doctor.py --json`.
4. Claim the task only if the budget and risk gates pass.
5. Execute one bounded slice.
6. Either write a fresh handoff or mark done/retry with structured evidence.
