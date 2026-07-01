# Social/video link intake scope guard

Applicability: user provides a social/video/course/article link and asks to analyze/add to taskpool.

User preference learned: do not narrow the task to "Hermes/taskpool/workflow absorption" unless the user explicitly asks for only that. The default scope is content-first synthesis.

Task/intake shape:
1. Analyze the content itself first: what it says, visible/OCR/transcript evidence, source facts, core claims, factual vs opinion/marketing language, and confidence.
2. Include product, business, technical, user/persona, opportunity, and risk analysis where relevant.
3. Put Hermes/taskpool/agent/workflow absorption in a separate derived subsection, not as the primary objective.
4. If the platform content is inaccessible without login or private access, record an evidence gap and ask for screenshot/transcript/OCR rather than inventing content.
5. When adding to taskpool, acceptance criteria must explicitly require content synthesis and evidence gaps before any Hermes absorption section.
6. For WeChat Channels/视频号 or other opaque landing pages where only a canonical preview page/title is available, do not infer topic from Hermes interests. Store canonical URL/source facts, but keep the task objective broad enough for content analysis once screenshot/OCR/transcript evidence is available.
7. Title guard: avoid task titles like “evaluate its Hermes/taskpool/workflow absorption value” unless the user explicitly requested that narrow objective. Prefer “content synthesis, opportunity/risk analysis, and derived Hermes takeaways.”

Anti-conditions:
- Do not turn single-source social-media heat into engineering proof.
- Do not log in, bypass platform controls, repost, download private content, or fabricate video details.
- Do not let the generated task title/objective imply the only value is Hermes workflow absorption.
