# 71 — Legal retrieval benchmarks: protocols and metrics to adopt

**Idea**

Align `rag_eval` with the protocols of published legal IR benchmarks — article-level recall@k (BSARD/LLeQA), graded relevance (LeCaRD), span-level attribution (LegalBench-RAG, LLeQA rationales) — and add BSARD/bBSARD as an external corpus so our pipeline gets one number the literature can be compared with.

**Why it fits this project**

- Our headline metric is doc-level MRR. Legal IR almost never leads with MRR: questions map to *several* applicable articles (BSARD questions have multiple relevant articles; COLIEE task 3 scores macro-F2, recall-weighted; CLERC reports R@1000, BSARD R@100/200/500 plus MAP@100/MRR@100). The retriever's job in a retrieve-then-read pipeline is recall; the reader/reranker handles precision.
- BSARD is Belgian, French, layman questions (Droits Quotidiens) → statute articles: the same problem as Corpus B. bBSARD adds Dutch questions (idea 62/10). Nothing else in the literature is this close.
- We already store an evidence quote per B/C question — the span annotation LegalBench-RAG (character ranges) and LLeQA (paragraph rationales) use — so chunk-level attribution metrics are nearly free.
- C already has "several acceptable ids" and 0.5-weighted secondary docs, an informal graded-relevance scheme; formalising it makes nDCG meaningful.

**Evidence**

- BSARD (ACL 2022): 1,108 FR questions, 22,633 Belgian articles, jurist-labelled; metrics R@100/200/500, MAP@100, MRR@100 (verified on abstract: best baseline R@100 74.8 %; fine-tuned dense > BM25 zero-shot). Test split ≈222 q (unverified). https://arxiv.org/abs/2108.11792
- LLeQA (AAAI 2024): 1,868 FR questions, ~27.9k articles, answers with paragraph-level rationales; retrieval reported as recall@k / MAP / MRR (granularity unverified). https://arxiv.org/abs/2309.17050
- bBSARD (2025, Maastricht Law&Tech): FR+NL bilingual BSARD; BM25 remains competitive with multilingual dense zero-shot (arXiv id not verified).
- LegalBench-RAG: 6,858 queries, 79M chars, ground truth = character spans; precision@k/recall@k for k=1…64; small chunks (~500 chars) raise precision (chunk-size finding from memory). https://github.com/zeroentropy-ai/legalbenchrag
- COLIEE: task 1 case retrieval (micro-F1), task 3 statute retrieval over Japanese Civil Code (macro-F2), tasks 2/4 entailment (accuracy) (from memory). https://coliee.org
- CLERC (2024): citation retrieval from legal analysis over US case law; zero-shot IR 48.3 % R@1000; near-duplicate opinions and citation leakage are the stated pitfalls. https://arxiv.org/abs/2406.17186
- LePaRD: passage-level precedent prediction from citation-derived labels. https://arxiv.org/abs/2311.09356
- LeCaRD/LeCaRDv2 (CAIL family): 4-level graded relevance, nDCG@10/20/30. AILA (FIRE 2019): 50 queries, statute + precedent, MAP/BPREF. ECtHR/LexGLUE and EUR-Lex are classification (F1), not retrieval. (unverified)
- BEIR has no legal subset (nDCG@10 primary, R@100 secondary); MTEB carries AILA, LegalBench-QA, GerDaLIR, LeCaRDv2 at nDCG@10 (unverified). https://arxiv.org/abs/2104.08663

**How we would implement it**

1. `rag_eval.metrics`: add R@5/10/20/100, MAP@100, nDCG@10 with integer grades; keep MRR. Leaderboard rows gain these columns; readmes report R@k first.
2. Question schema: `relevant: [{id, grade: 0–3, span: [start,end]}]`; migrate `secondary` → grade 1, primary → grade 3; derive spans from the existing evidence quotes with a fuzzy-match script. Add `equivalent_ids` groups for yearly/regional editions and FR/NL twins (one hit in a group counts once; a second copy is not a false positive).
3. Chunk-level metric (LegalBench-RAG style): a chunk is relevant if it overlaps a gold span; report span-P@k / span-R@k for k=5, 20.
4. Corpus D = BSARD test split (HF `maastrichtlawtech/bsard`): run BM25-fr, e5-small, hybrid + bge-reranker top-30; publish R@100 / MRR@100 next to the paper's baselines. Later bBSARD-NL for the Dutch leg.

**Expected gain and cost**

No retrieval gain; comparability and diagnostics: R@k separates retriever misses from reranker misorders (on C, R@10 0.891 vs H@1 0.609 says most loss is ordering). BSARD gives a third-party-labelled sanity check of our French normalisation and hybrid stack. Cost: ~1 day of harness work, ~1 h to embed 22.6k articles (e5-small), ~1.5 h of reranking.

**Risks / open questions**

- BSARD covers civil/family/housing law, not tax; only the *ordering* of methods transfers, not absolute numbers.
- Migrating grades changes existing leaderboard numbers; keep the MRR column untouched and version the metric set.
- Span offsets break on re-parsing (idea 61); store quote text, re-derive offsets at load time.
- BSARD is CC-BY-NC-SA: evaluation only.

**Verdict**

**try-now** — cheap harness changes plus one public Belgian-French benchmark make every other idea in this folder measurable and citable.

**Sources**

- https://arxiv.org/abs/2108.11792 · https://github.com/maastrichtlawtech/bsard · https://huggingface.co/datasets/maastrichtlawtech/bsard
- https://arxiv.org/abs/2309.17050 · https://github.com/maastrichtlawtech/lleqa
- https://arxiv.org/abs/2408.10343 · https://github.com/zeroentropy-ai/legalbenchrag
- https://arxiv.org/abs/2406.17186 (CLERC) · https://arxiv.org/abs/2311.09356 (LePaRD)
- https://coliee.org (fetch failed) · https://arxiv.org/abs/2110.00976 (LexGLUE) · https://arxiv.org/abs/2104.08663 (BEIR)
- LeCaRD, AILA, bBSARD, ECtHR-PCR, MTEB legal tasks: from memory, not fetched.
