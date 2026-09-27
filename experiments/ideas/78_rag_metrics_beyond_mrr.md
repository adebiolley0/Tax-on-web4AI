# 78 — RAG metrics beyond MRR: context sufficiency, nuggets, citation correctness, abstention

**Idea**

Extend the harness from "is the right document in the top k" to four layers: (1) **retrieval quality at span level** (context precision/recall, *sufficiency* of the packed context), (2) **answer support** (nugget recall à la TREC RAG AutoNuggetizer), (3) **citation correctness** (ALCE-style citation precision/recall, RAGAS/TruLens/ARES faithfulness) and (4) **calibrated abstention** (coverage/risk curve: does the system say "je ne sais pas" when the context is insufficient?). Layers 1 and part of 3 can be computed **now without an LLM** from annotated spans; the rest is switched on when DeepSeek arrives, using the same annotations.

**Why it fits this project**

A tax answer is only useful if it cites the exact article / circulaire paragraph; fluency is irrelevant. Document-level MRR cannot tell us whether the chunk handed to the LLM actually contains the provision, whether the packed context is *sufficient*, or whether the LLM invents "art. 132bis" unsupported by context. The `notes` field in `questions_b.json`/`questions_c.json` already names the answer-bearing passages ("Art. 130: 25 % jusqu'à 16.720 €…"), so nuggets and gold spans are half-written.

**Evidence**

- RAGAS context precision/recall: LLM and **non-LLM variants** (ID-based, string-similarity on reference contexts). https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_precision/
- TREC 2024 RAG track AutoNuggetizer: LLM creates vital/okay nuggets, assigns them to answers; strong correlation with manual nugget scoring over 21 topics / 45 runs. https://arxiv.org/abs/2411.09607
- ALCE citation recall/precision via NLI; best models lack full citation support ~50 % of the time on ELI5. https://arxiv.org/abs/2305.14627
- ARES: fine-tuned lightweight judges for context relevance / faithfulness / answer relevance, calibrated with a few hundred human labels (PPI). https://arxiv.org/abs/2311.09476
- TruLens RAG triad (context relevance, groundedness, answer relevance). https://www.trulens.org/getting_started/core_concepts/rag_triad/
- "Sufficient context" (Joren et al.): classify whether context suffices; strong LLMs answer wrongly rather than abstain on insufficient context; sufficiency-guided selective generation +2–10 % correct answers. https://arxiv.org/abs/2411.06037
- LegalBench-RAG: legal retrieval benchmark scored on **character-span** precision/recall, not documents (from memory, not re-fetched). https://arxiv.org/abs/2408.10343

**How we would implement it**

1. *Annotations* (one pass, ~2 days): add to each question `gold_spans: [{doc, char_start, char_end}]` and `nuggets: [{text, vital}]`, derived from the existing `notes`; add 10–15 **unanswerable / out-of-corpus** questions per corpus for abstention.
2. *LLM-free metrics now* (`rag_eval/metrics.py`): span-level **context recall@k** (fraction of gold span characters covered by returned chunks), **context precision@k** (RAGAS non-LLM/ID variant at chunk level), **sufficiency@k** = all vital spans covered within a token budget (e.g. 4k), **lexical nugget recall** (normalised substring / fuzzy match of nugget key terms and amounts in the context — amounts and article numbers are exact tokens, so this proxy is strong here). Log all to `leaderboard.jsonl`.
3. *Citation proxies now*: for any answer text (later DeepSeek, today a template that quotes the top chunk), parse references (`art. 130 CIR 92`, `Circ. 2025/C/9`) with the numeric-reference extractor of idea 14 and check (a) the cited id exists in the corpus, (b) it is among the gold docs, (c) the cited chunk was in the context — **citation precision/recall without NLI**.
4. *With DeepSeek later*: AutoNuggetizer-style nugget assignment, ALCE-style claim support, RAGAS faithfulness; abstention scored as a **coverage–risk curve** (answer rate vs error rate) on answerable + unanswerable questions, split by our sufficiency label to separate retrieval from generation failures. Calibrate the judge with ~150 hand labels (ARES PPI).

**Expected gain and cost**

No MRR change — this changes *what we optimise*: it reveals chunking/packing regressions invisible at document level (correct doc at rank 1 but the article truncated), gives an acceptance test for the MCP `search` output before any LLM, and a ready judge pipeline when DeepSeek lands. Cost: ~3 days annotation + metrics; later ≈ 2–3 LLM calls per question (cheap on 130 questions).

**Risks / open questions**

- Span annotation is the bottleneck; lexical nugget proxies over-reward keyword overlap (weight amounts/article numbers).
- Citation parsing must handle Belgian formats (`art. 90, 1°`, `CIR 92`, `AR/CIR`) — reuse idea 14.
- LLM-judge bias on French legal text is unvalidated; needs ARES-style human calibration.
- Context budget for sufficiency depends on DeepSeek context and MCP payload limits.

**Verdict**

**try-now** (span/nugget proxies, citation-id checks); LLM layers **try-when-LLM** — annotations are half written and document-level MRR 0.70 hides the chunk- and citation-level failures that matter most for a legal assistant.

**Sources**

https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_precision/ · https://arxiv.org/abs/2411.09607 · https://arxiv.org/abs/2305.14627 · https://arxiv.org/abs/2311.09476 · https://www.trulens.org/getting_started/core_concepts/rag_triad/ · https://arxiv.org/abs/2411.06037 · https://arxiv.org/abs/2408.10343 (unverified)
