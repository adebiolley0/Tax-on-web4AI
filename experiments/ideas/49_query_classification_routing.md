# 49 — Query classification and routing with small models

**Idea**

Train tiny classifiers that map a French question to four facets — *tax type* (IPP/ISOC/TVA/succession/enregistrement/taxes assimilées/divers), *region* (fédéral/BXL/WAL/VL), *target document type* (statute/circulaire/ruling/QP/jurisprudence/FAQ/any) and *intent* (rate, procedure, eligibility, definition) — and feed the probabilities to (a) soft boosts in the fused ranking, (b) `search` tool selection/filters in the MCP layer, (c) a prior on which sub-index to ask. Idea 27 covers rules and boost mechanics; this note covers the *learned* layer: labels, models, evaluation.

**Why it fits this project**

- Distant supervision is already on disk: every one of the 21,259 `myfin_docs` files carries a `path` front-matter whose level 1 is the tax domain (e.g. `["FISCALITÉ", "Droits de succession", "Questions parlementaires"]`). The 1,362 QPs are question-shaped text, the closest proxy to user queries; the 1,120 circulars and 8k code articles give titles per domain.
- Corpus C has 24 document types and yearly/regional near-duplicates; a type/region prior cleans the reranker's top-30 (§3.8).
- CPU-only: logistic regression on cached e5-small embeddings or fastText runs in < 10 ms/query, no GPU or LLM. Later, the same facets become enum arguments of `search` for DeepSeek.

**Evidence**

- Adaptive-RAG (NAACL 2024): a query classifier with only 30–66 % per-class accuracy still lifts F1 44.3 → 46.9 at 3.6 vs 8.8 s/query; oracle routing reaches 56.3, and 60M/223M classifiers do as well as T5-large. Headroom is accuracy, not size. https://arxiv.org/abs/2403.14403
- RAGRouter-Bench (Apr 2026): TF-IDF + SVM 93.2 % accuracy / 0.928 macro-F1, 3.1 F1 above MiniLM embeddings; *legal queries were the most tractable domain*. https://arxiv.org/abs/2604.03455
- RouterBench (2024): predictive KNN/MLP routers beat the "zero router" only on some tasks; cascades degrade fast once judge error > 0.2. Routers must abstain when unsure. https://arxiv.org/abs/2403.12031
- SetFit: prompt-free few-shot fine-tuning of sentence-transformers, order-of-magnitude faster than PEFT/PET, multilingual by swapping the encoder. https://arxiv.org/abs/2209.11055
- Political DEBATE (2024): NLI models fine-tuned on 10–25 examples beat supervised classifiers trained on thousands. https://arxiv.org/abs/2409.02078
- Zero-shot NLI for French: `MoritzLaurer/mDeBERTa-v3-base-mnli-xnli`, 0.3B, XNLI-fr 83.4 %, MIT. Small French encoder: `cmarkea/distilcamembert-base`, 68M, MIT. https://huggingface.co/MoritzLaurer/mDeBERTa-v3-base-mnli-xnli · https://huggingface.co/cmarkea/distilcamembert-base
- fastText supervised: trains in seconds on 12k examples, char/word n-grams. https://fasttext.cc/docs/en/supervised-tutorial.html
- Utterance-based routing with local encoders: https://github.com/aurelio-labs/semantic-router

**How we would implement it**

1. *Oracle test first (½ day)*: hand-label the ~130 questions (B + C + repo) with the four facets; inject the *gold* facets as boosts in `14_ltr_fusion`. If gold-facet MRR − baseline < 0.03, stop here.
2. *Distant training set*: tax type from `path[1]` (7 classes), document type from `document_type`; examples = QP question paragraphs + circular/article titles (+ synthetic questions from idea 12). Region only from `Législation régionale` paths and city/keyword rules — text rarely states it.
3. *Models, in order of cost*: LR on cached e5-small embeddings → TF-IDF char-n-gram SVM / fastText → SetFit on multilingual-e5-small → zero-shot mDeBERTa (for intent, which has no distant labels) → distilcamembert fine-tune only if the others plateau.
4. *Use*: probabilities → `λ_t·p(type)` boost (idea 27), abstain below 0.5; expose top facet as default `filters` in the MCP `search` tool and as `suggested_document_type` in the response.
5. *Evaluation*: 5-fold on the 130 questions per facet (macro-F1 with bootstrap CI), then end-to-end MRR/recall@30 under none / predicted / gold facets.

**Expected gain and cost**

+0.01–0.04 MRR on B/C (mostly twin-article/twin-year cases), bounded by the gold-facet oracle; larger value for tool selection and at 100k documents. Cost: 1–2 days; < 10 ms/query for LR/fastText, ~0.3–0.5 s/query for NLI on CPU (unverified). No heavy models.

**Risks / open questions**

- Label skew: QPs are 532 enregistrement / 327 succession / 65 income tax, circulars 528 TVA — the opposite of citizen demand; reweight or cap classes.
- Domain shift: titles and QPs are not layman questions; expect 10–20 F1 drop on real queries.
- Intent has no distant labels; 130 examples give ±0.08 F1 confidence — treat intent routing as exploratory.
- Users rarely name a document type or region; those facets will mostly be "any", so gains concentrate on tax type.
- Boosts amplify metadata errors (NL bodies flagged `fr`).

**Verdict**

try-now — the oracle-facet test costs half a day and decides everything; if it shows headroom, LR-on-embeddings + fastText from taxonomy paths is a one-day build.

**Sources**

Inline above; local: `myfin_docs/*/*.md` front-matter `path`, `experiments/data/corpus_c/questions_c.json` (`doc_type` field), `experiments/ideas/27_faceted_search_query_routing.md`, EXPERIMENTS.md §3.8.
