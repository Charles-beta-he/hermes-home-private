# Claude Code Fable 5 system-level self-check pattern

Use this when the user asks to use Claude Code Fable 5 for a system-level Hermes self-check, architecture/governance review, or recommendations. This is different from asking Fable to review the current conversation or the main assistant's style.

## Trigger language

- “使用 Fable 5 进行系统级别自检”
- “让 Fable 5 给系统建议”
- “用 Claude Code/Fable 做 Hermes 自检/治理审查/全局健康检查”

## Procedure

1. Confirm the real Fable path with a minimal probe before any review:
   - `claude -p '只回复 OK' --model fable --output-format json --max-turns 1 --no-session-persistence`
   - Treat it as usable only if `is_error=false` and `modelUsage` contains `claude-fable-5` or an equivalent resolved Fable model id.
2. Build a compact read-only evidence packet rather than asking Fable to reason from chat alone. Include, as applicable:
   - objective and explicit side-effect boundary;
   - `hermes --version`;
   - current UTC timestamp;
   - Fable probe receipt;
   - `~/.hermes` status summary and Hermes source repo branch/status/log;
   - `post-update-check.py --fix` summary;
   - cron jobs summary including enabled/error/delivery status;
   - taskpool/brain selfcheck and brain validate summaries;
   - provider/consult_models status;
   - dashboard/gateway listener hints and disk summary.
3. Ask Fable for system-level output, not a chat-performance review. Require:
   - overall health as Green/Yellow/Red;
   - P0/P1/P2 recommendations;
   - each recommendation includes evidence, risk, action, verification, and landing boundary;
   - coverage-registry/dynamic-selfcheck candidates vs one-time fixes;
   - memory/skill/proposal/taskpool/do-not-do classification.
4. Preserve authority boundaries:
   - Fable is advisory; do not mutate repos, cron, provider config, taskpool lifecycle, delivery channels, secrets, or destructive state from the review alone.
   - Do not write temporary login state, branch state, job ids, or one-off errors to memory.
   - Concrete engineering follow-ups become taskpool candidates/proposals, not fake memories or skills.
5. Report the Fable receipt and the bounded recommendations to the user. If the user asked only for review, stop before executing fixes.

## Pitfalls

- Do not confuse “system-level self-check” with “review this conversation / review the main assistant's behavior.” If the user clarifies that they mean system-level, collect real Hermes evidence and rerun Fable on that packet.
- Do not use a Claude Code banner, `auth status`, or model dropdown as proof of Fable availability; only a real prompt with successful `modelUsage` counts.
- Do not treat Fable consensus/advice as completion evidence. Fixes require separate implementation, readback, and validation.
- Do not capture environment-dependent login or quota failures as durable negative rules. Capture the probe pattern instead.

## Output skeleton

```text
Fable 5 system self-check receipt:
- command: ...
- result: is_error=false, modelUsage=claude-fable-5
- evidence packet: <path or summary>

Overall: Green/Yellow/Red — <reason>

P0/P1/P2 recommendations:
| priority | issue | evidence | risk | action | verification | landing boundary |
| ... |

Coverage Registry candidates:
- ...

One-time fixes:
- ...

Boundary landing:
- memory: skipped/reason
- skill: ...
- proposal: ...
- taskpool candidate: ...
- do-not-do: ...
```
