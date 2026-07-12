你是 Claude Fable 5。重新复审。上一版输出出现未给证据的“权限拦截/auth.py/providers.py/git diff”说法，本次禁止提及任何未在下方列出的事实。

只基于这些证据：
- hermes portfolio --json: ok true, profile_count 16, doctor errors 0 warnings 0.
- hermes portfolio verify --json: ok true, errors 0 warnings 0.
- portfolio_os_verify.py --json: ok true.
- portfolio_semantic_audit.py --fail-on-warning: ok true, coverage 100.0, dimensions 16, errors 0 warnings 0, findings empty.
- tests/hermes_cli/test_portfolio_os.py: 7 passed.
- JSON readback: pass.
- router smoke: pass, but output_preview contains Hermes verification gate not certified, so it is connectivity/smoke only.
- mission board: two missions paused; main self-architecture mission ticks_used=72 ticks_max=72.
- changes: added portfolio_profile true to project profiles, UVISA portfolio_code_guard, work-project exemption reason+review_after, semantic_audit freshness/exemption fields, required Portfolio OS docs/status/receipt, and readback evidence paths.
- boundaries: no project code changes, no external dispatch, no push/deploy, no destructive/credential/payment action, no validated status restoration.

请中文 600 字以内：系统审核、架构审核、多角度审核、限定域 PASS/FAIL、未恢复 validated 是否正确、剩余边界。