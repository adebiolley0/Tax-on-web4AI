# 65 — Automatic document quality scoring and filtering

**Idea**

Compute cheap, inspectable features per document (length, dot-leader/TOC ratio, citation density, tax-term density, "abrogé"/"opgeheven" markers, body language, document type, title informativeness) and derive a `quality` score in [0, 1], an `is_index` flag and a `status` (current / abrogated / indexation-notice). Hard-drop only unambiguous junk (index pages, non-French bodies, sub-300-char stubs); keep everything else and apply the score as a *prior* at retrieval and as a triage signal in an ingestion QA report. Rules first; a tiny classifier (logistic regression / fastText) trained from the existing manual include/exclude classification once rules plateau.

**Why it fits this project**

Corpus C (exp 09) inventoried exactly this noise: index pages, TOC-only documents, 1–2 kB stubs, Dutch bodies flagged `fr` (≈ half the rulings), abrogated codes beside current ones, non-tax law, indexation notices. `MYFIN_ARBORESCENCE.md` § Classification already holds a human include/exclude decision per Fisconet+ section — free weak supervision. Exp 08 showed boilerplate removal alone gives BM25 +0.03 MRR / +0.075 hit@1, so ingestion hygiene is a measured lever. CPU-only, model-free, minutes over 21k documents.

**Evidence**

- Gopher (Rae et al. 2021) rules: word-count bounds, mean word length 3–10, symbol-to-word ratio < 0.1, < 90 % bullet lines, ≥ 80 % alphabetic words. https://arxiv.org/abs/2112.11446
- C4 (Raffel et al. 2020): terminal-punctuation lines, ≥ 5 sentences, langdetect ≥ 0.99. https://arxiv.org/abs/1910.10683
- CCNet (Wenzek et al. 2020): fastText language ID + KenLM perplexity buckets. https://arxiv.org/abs/1911.00359
- RefinedWeb / FineWeb-Edu: heuristic pipelines beat naive filters; a small classifier trained on a few hundred k labelled pages beats the heuristics. https://arxiv.org/abs/2306.01116 · https://arxiv.org/abs/2406.17557 · https://huggingface.co/HuggingFaceFW/fineweb-edu-classifier
- DCLM (Li et al. 2024): a fastText quality classifier outperforms every heuristic combination tried. https://arxiv.org/abs/2406.11794
- Dolma / datatrove implement these filters as reusable Python. https://arxiv.org/abs/2402.00159 · https://github.com/huggingface/datatrove
- Pile of Law, MultiLegalPile: source-level curation, language ID and dedup before release. https://arxiv.org/abs/2207.00220 · https://arxiv.org/abs/2306.02069
- Retrieval priors: Bendersky, Croft & Diao (WSDM 2011) — readability, stop-word fraction, entropy as document priors improve retrieval; Kraaij et al. (SIGIR 2002) entry-page priors. https://dl.acm.org/doi/10.1145/1935826.1935849 · https://dl.acm.org/doi/10.1145/564376.564383
- Engine hooks: Elasticsearch `rank_feature`, Vespa rank-profile features. https://www.elastic.co/docs/reference/query-languages/query-dsl/query-dsl-rank-feature-query

(Thresholds quoted from memory — verify before coding.)

**How we would implement it**

1. `src/ingestion/quality.py::score_document(md) -> QualityReport`: `n_chars`, `n_sentences`, `dot_leader_ratio` (lines matching `\.{4,}|…` or bare `Art. N` lists), `heading_to_body_ratio`, `commentaire_na` (`## Commentaire` empty/`N/A`), `citation_density` (art./§/M.B./Numac/circ. per 1k chars), `tax_term_density`, `lang` (lingua-py on the body, not the metadata), abrogation markers in title/first 500 chars, indexation-notice pattern, `title_topicless`.
2. Rules: `is_index = dot_leader_ratio > 0.3 or commentaire_na or heading_to_body_ratio > 0.6`; `drop = is_index or lang != fr or n_chars < 300`; `status = abrogated` from title/preamble only.
3. Classifier: labels from the arborescence include/exclude tables + ~300 hand-labelled documents; scikit-learn logistic regression on features + char n-gram TF-IDF; keep only if it beats rules on the held-out sample, per document type.
4. Retrieval: store `quality`, `status`, `lang` as metadata; fuse as `score × (0.5 + 0.5·quality)` (or a log-prior in the convex-fusion stage of exp 03/09); exclude `abrogated` unless the query carries a year/historical cue (idea 41 supplies the temporal layer).
5. QA report per crawl: `quality` histogram per document type, 50 lowest-scored kept and 50 highest-scored dropped documents for spot review, drift vs previous crawl.

**Expected gain and cost**

Hard drop ≈ 10–20 % of corpus C; +0.02–0.05 MRR on C from fewer junk candidates in the reranker's top-30. Ingestion cost seconds; engineering 1–2 days for rules + report, +1 day for the classifier; only new dependency is a language detector.

**Risks / open questions**

- Short ≠ junk: a one-line AR article or tariff table is legally decisive — length is never a sole drop criterion; hence down-weight, not delete.
- "Abrogé" in a body usually refers to *another* provision; restrict the marker to title/preamble.
- Section-level weak labels are noisy at document level; without the hand-labelled sample the classifier just learns the section.
- Prior strength must be tuned per fusion setup; too strong masks rare-but-relevant documents.
- Overlaps ideas 26 (dedup) and 41 (temporal validity); run this first, they consume its metadata.

**Verdict**

try-now — rule-based features plus a retrieval prior are a day of work, need no model, address the inventoried noise in corpus C directly, and give the QA visibility every later ingestion change will need.

**Sources**

URLs inline above · experiments/09_corpus_c/README.md · experiments/08_corpus_b_cleanup/README.md · MYFIN_ARBORESCENCE.md § Classification · AGENTS.md § Document filtering policy.
