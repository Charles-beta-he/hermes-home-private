# Public medical incident research (Chinese web)

Use when a user asks to “查询/查一下 <medical procedure/drug> 事件” and the phrase may refer to a loose cluster of public discussions rather than one official incident.

## Procedure

1. **Disambiguate the incident shape before summarizing.** Treat the query as unclassified until evidence shows one canonical event. Common buckets:
   - clinical adverse event / death / malpractice dispute;
   - criminal or misconduct allegation under anesthesia;
   - pricing, informed-consent, or low-price package dispute;
   - general medical-safety Q&A misread as an “event”.
2. **Search with medical synonyms and risk terms.** For Chinese GI endoscopy examples, try combinations of:
   - `无痛胃肠镜`, `无痛胃镜`, `无痛肠镜`, `胃肠镜`, `肠胃镜`;
   - `全麻`, `麻醉`, `镇静`, `丙泊酚`;
   - `死亡`, `医疗事故`, `医疗纠纷`, `心脏骤停`, `过敏`, `猥亵`, `侵犯`, `低价套餐`, `切息肉`.
3. **Separate verified sources from search snippets.** Search-result snippets can reveal candidate buckets, but final claims should be backed by accessible articles, court/authority documents, hospital/association guidance, or clearly labeled as “search result/舆论线索未核实”.
4. **Avoid collapsing unrelated incidents.** If evidence shows multiple unrelated cases, say so explicitly: “not a single official-named event; it appears to be several discussion threads.”
5. **Report practical takeaways without medical overclaiming.** For safety questions, emphasize risk stratification, pre-anesthesia evaluation, monitoring, emergency readiness, informed consent, and choosing qualified institutions. Do not present individualized medical advice.

## Output shape

- Bottom line: single event vs cluster.
- Evidence buckets: 2–4 bullets with source URLs and what each supports.
- What is verified vs uncertain.
- Practical checklist/questions to ask the hospital, if relevant.

## Pitfalls

- Do not infer guilt from sensational reposts about anesthesia-related misconduct; distinguish allegation, verdict, and unrelated procedure context.
- Do not let Q&A pages become incident evidence; they are background/risk explanation only.
- Do not over-index on one search engine’s related searches; use them only to generate follow-up queries.
