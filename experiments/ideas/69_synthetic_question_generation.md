# 69 — Synthetic question generation: templates, diversity, filters (evaluation *and* training)

**Idea**

One generator pipeline feeding idea 58 (bigger eval set) and idea 12 (fine-tuning data): per-document-type templates, explicit diversity slots, a cascade of cheap filters, and a strict rule that the 133 human questions stay the *only* model-selection oracle. Generated questions are a **dev set** (fusion weights, chunk sizes, prompts, ablations) and a **training set** — never the reported MRR.

**Why it fits this project**

- ±0.05 MRR noise on 130 questions hides every +0.02–0.04 idea in this folder; a 1,000-question dev set makes ±0.03 visible for *relative* decisions.
- Templates follow the corpus: articles (B) need layman paraphrases (the dominant failure), circulaires "what do I declare" questions, rulings/PQs (topic-less titles) fact-pattern questions from the body, tables rate questions with year/region slots (C's twins).
- Human questions were written from titled documents (EXPERIMENTS.md §5); slot-controlled generation rebalances toward vocabulary-gap and region/year questions.

**Evidence**

- Promptagator: ≤8 exemplars; round-trip filter (source passage must rank top-1) +2.5 nDCG on 8/11 sets but hurts small ones. https://arxiv.org/abs/2209.11755
- InPars-v2: generate 100k, keep top-10k by monoT5 score; the reranker filter is what makes open generators work. https://arxiv.org/abs/2301.01820
- Doc2Query--: relevance-filtering generated queries removes hallucinations, +16 % effectiveness. https://arxiv.org/abs/2301.03266
- DUQGen: cluster-sampled 1k examples beat 5k random on 13/18 sets — coverage beats volume. https://arxiv.org/abs/2404.02489
- Synthetic test collections (Rahmani et al., SIGIR 2024): LLM queries + judgments reproduce human system rankings (Kendall τ ≈ 0.8–0.9, unverified) with a bias toward LLM-based rankers. https://arxiv.org/abs/2405.07767
- Alaofi et al. 2023: LLM query variants are less varied and lexically closer to documents than human ones (unverified detail). https://dl.acm.org/doi/10.1145/3539618.3591960
- RAGAS testset generation: persona × query style × "evolutions" as diversity knobs. https://docs.ragas.io/en/stable/concepts/test_data_generation/rag/
- ≈3B open generators match large ones once filtered. https://arxiv.org/abs/2510.02241
- French seq2seq now: `doc2query/msmarco-french-mt5-base-v1` (mT5-base, mMARCO-fr). https://huggingface.co/doc2query/msmarco-french-mt5-base-v1 — BSARD's 118k mT5 questions are grammatical but shallow (idea 12).

**How we would implement it**

1. *Sampling*: stratify by document type, region, year; cluster e5-small embeddings (DUQGen), one chunk per cluster; skip TOC/index pages (AGENTS.md policy).
2. *Templates* (JSON out, 3 questions/chunk):
   - article → "layman": no statute term in the question, one concrete situation;
   - circulaire → "practical": *que dois-je déclarer / quel code / quel délai*;
   - ruling / PQ → "fact-pattern": 2–3 sentence situation, no entity names;
   - table → "rate": *quel taux / plafond pour <year> en <region>*, values copied from the table.
3. *Diversity slots*: persona (particulier, indépendant, comptable, dirigeant PME), register (SMS-like / formal), region, year, with/without amount; 10 % Dutch-body chunks with French questions; 8 real questions as style exemplars, rotated.
4. *Filters* (cheap → dear): schema/length; MinHash + e5 cosine ≥ 0.92 dedup against other generated *and* human questions (leakage guard); term-overlap cap (Jaccard vs chunk ≤ 0.6, kills copy-paste); round-trip: BM25+e5 hybrid ranks the source *document* top-3; bge-reranker score ≥ median; hallucination: every number/year/region in the question must appear in the chunk; optional self-judge "answerable from the passage" 1–4.
5. *Pilot now, CPU-only*: mT5-fr doc2query and Qwen3-0.6B (llama.cpp, ~5–10 s per 3 questions [unverified]) on 500 corpus-B articles, same filters; measure acceptance rate and lexical overlap with human questions.
6. *Oracle rule*: report human MRR only; synthetic dev set decides between configurations only when the human ordering agrees in sign; log both in `leaderboard.jsonl` with a `synthetic` flag; never fine-tune on questions from documents that are human-question targets.

**Expected gain and cost**

Not an MRR gain by itself: it turns invisible +0.02 decisions into measurable ones (n≈1,000 dev) and supplies idea 12's data. Cost per 1k *kept* questions (≈2.5k generated, 3 per chunk, 1.5k cached-prompt tokens + 0.3k output): DeepSeek V4.1-Flash ≈ $0.30–0.50, V4-Pro ≈ $2; judge pass ≈ +$0.50; reranker filtering ≈ 0.7 s/pair on CPU → ~30 min per 2.5k. mT5/Qwen pilot: free, one CPU night, expect 30–50 % acceptance and weaker layman phrasing.

**Risks / open questions**

- Distribution shift: generated questions are longer, lexically closer to the source and more uniform than real users'; measure with the 133 human set (length, type-token, overlap) and re-weight.
- Round-trip filtering biases the set toward what current retrievers already find (Promptagator caveat); keep a 20 % unfiltered slice for evaluation.
- LLM-judge/LLM-rewriter configurations may be favoured by LLM-generated questions (SIGIR 2024 bias).
- Dedup against human questions must be tight or the "oracle" leaks.

**Verdict**

**try-when-LLM** — the framework is cheap (< $5 per 1k questions with DeepSeek) and prerequisite for ideas 12 and 58, but the small-model pilot can start now to build templates and filters; the human set stays the only reported score.

**Sources**

URLs above; DeepSeek pricing https://api-docs.deepseek.com/quick_start/pricing; Qwen3-0.6B https://huggingface.co/Qwen/Qwen3-0.6B; in-repo idea files 06, 12, 58; `experiments/EXPERIMENTS.md` §3.0, §5.
