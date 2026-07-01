# Multi-model GitLab merge gate pattern

Use when a GitLab MR/PR was developed by one model and the user requests independent multi-model review plus auto-merge.

## Applicability

- Development model/provider is known or inferable from the active session.
- User authorizes merge after review.
- The target repository can be merged by CLI/API.

## Anti-conditions

- Do not treat a same-provider reviewer as the independence gate; it is advisory only.
- Do not auto-merge if review fixes were pushed after the last independent review.
- Do not delete source branches unless explicitly authorized or required by project policy.

## Procedure

1. Capture the diff and reviewed source SHA.
2. Run at least one independent reviewer from a different model/provider family than the development model.
3. Optionally run same-family/static reviewers as advisory; still act on deterministic findings.
4. For any concrete finding:
   - add a failing regression test proving it;
   - implement the smallest fix;
   - run targeted tests/lint/build;
   - commit and push;
   - update the reviewed SHA.
5. Re-run the independent reviewer on the final diff after all fixes.
6. Post a non-resolvable review receipt with reviewer identities, blockers, fixes, and verification commands.
7. Merge with an expected SHA gate, e.g. `glab mr merge <iid> --sha <reviewed_sha> --auto-merge=false --yes`.
8. Read back MR state, merge commit SHA, target branch head, and whether the target contains the reviewed source commit.

## Common pitfall

A reviewer may find a real issue even if it is not the official independence gate. Example class: token handoff to allowlisted hosts must also require HTTPS; host allowlists alone do not prevent plaintext credential exposure.
