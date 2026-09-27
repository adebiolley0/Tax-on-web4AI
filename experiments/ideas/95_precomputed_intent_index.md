# 95 — Pre-computed answer/intent index (question-to-question retrieval)

**Idea**

Treat the corpus's *already-asked questions* — 1,362 parliamentary questions (PQ), the 7 official FAQs (dozens of Q/A pairs each), FAQ-style circulaires, and the "objet"/summary of thousands of ruling requests — as a first-class **question index**. A user question is matched to prior questions (Q→Q, symmetric similarity) rather than only to statutes/chunks (Q→doc). Each matched question carries its authoritative answer and cited provisions. Optionally cluster questions into intents (BERTopic-style) for coverage measurement, dedup of yearly repeats and "intent cards".

**Why it fits this project**

- The main failure mode is the vocabulary gap: a citizen writes "voiture de société", the code says "avantage de toute nature". PQs and FAQs are written *in* the citizen's words, so Q→Q bridges the gap without lexicons or fine-tuning.
- PQ/ruling titles are topic-less (EXPERIMENTS.md §3.8); the question text is the best key.
- CPU/offline: 10–20k short question units embed in minutes; no LLM needed for v1.
- Answers are authoritative and dated (minister, SPF, SDA): the MCP tool can return "asked in 2019; answer X, citing art. 36 CIR 92".

**Evidence**

- PAQ / RePAQ (arXiv 2102.07033): question-similarity retrieval over a pre-built QA bank matches RAG on NQ at ~100× lower cost; with a confidence threshold it answers ~40% of questions alone and backs off otherwise — the selective, answer-aware pattern we want.
- Sakata et al., SIGIR 2019 (arXiv 1905.02851): on localgovFAQ/StackFAQ, query-to-question similarity is the dominant signal; BERT query-to-answer adds on top.
- COUGH (arXiv 2010.12800): FAQ retrieval benchmark; Q→Q and Q→A are complementary.
- SemEval-2017 Task 3 / Quora Question Pairs: Q→Q duplicate detection is mature and works with small encoders.
- BERTopic (arXiv 2203.05794): UMAP+HDBSCAN+c-TF-IDF over sentence embeddings; standard for intent discovery.
- Belgian proxies BSARD (arXiv 2108.11792) and LLeQA (arXiv 2309.17050) show citizen legal questions cluster on recurring topics; tax-specific coverage numbers do not exist — measure locally.

**How we would implement it**

1. *Extract question units*: PQ (question + answer + cited articles), FAQ pairs (split on headings), numbered questions in circulaires, ruling `objet` + decision → `{question, answer, source_doc, provisions, date, assessment_year}` in a LanceDB table.
2. *Q→Q leg*: embed question text only with multilingual-e5-small (`query:` prefix both sides) vs `paraphrase-multilingual-mpnet-base-v2`, plus BM25 over question text. Fuse as a third leg (exp 03 convex fusion) or as a boost on the matched question's parent document.
3. *Selective answer*: if top cosine ≥ τ (tuned on sets A/B/C), return the prior Q/A verbatim with date and provisions; else fall through to the document pipeline (skips the 20–24 s/query reranker).
4. *Intents* (optional): BERTopic over question units → cluster ids, one representative per cluster, coverage stats, dedup.
5. *Freshness*: keep `date`/`assessment_year`; rank newer answers of the same intent higher; flag answers older than the last change to their provisions (ideas 25/41/64); embed only new units at ingestion. With DeepSeek later: 2–3 layman paraphrases per unit (ideas 06/69) and merged intent cards.

**Expected gain and cost**

Retrieval: +0.03–0.08 MRR on citizen-phrased questions whose intent exists in the bank; ~0 on statute lookups. Bigger user-facing gain: an authoritative dated answer in <100 ms for covered questions. Cost: an afternoon of extraction code, minutes of CPU embedding, ~10 MB index. Coverage is *unknown* — rough guess 30–50% (unverified); measure first by labelling the nearest prior question for each test question.

**Risks / open questions**

- PQs are often political/niche (statistics, policy) rather than how-to; coverage may be low and skewed. Rulings are fact-specific — a near-duplicate question may have an inapplicable answer.
- Stale answers shown confidently (amounts, thresholds, abolished regimes); needs date display and change flags.
- Ruling bodies are mostly Dutch; needs a multilingual embedder.
- τ tuned on <100 questions will overfit (idea 79).
- Asymmetric MS MARCO-style encoders may underperform on Q→Q (unverified); test the paraphrase model.

**Verdict**

**try-now** — extraction plus a Q→Q fusion leg is a one-day CPU experiment with the best cost/benefit for the vocabulary-gap problem, and the coverage measurement it forces is valuable on its own.

**Sources**

- https://arxiv.org/abs/2102.07033 (PAQ / RePAQ)
- https://arxiv.org/abs/1905.02851 (Sakata et al.)
- https://arxiv.org/abs/2010.12800 (COUGH)
- https://arxiv.org/abs/2203.05794 (BERTopic)
- https://arxiv.org/abs/2108.11792 (BSARD), https://arxiv.org/abs/2309.17050 (LLeQA)
- https://alt.qcri.org/semeval2017/task3/ (CQA duplicates)
- Mass et al., ACL 2020, "Unsupervised FAQ Retrieval with Question Generation and BERT" (URL unverified)
