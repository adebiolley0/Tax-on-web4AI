# 63 — Boilerplate removal and section zoning (rules vs small learned line classifiers)

**Idea**

Replace the ad-hoc preamble regex (exp 08 `cleanup.py`) with a two-stage *zoning* step run once at ingestion: (1) split each Fisconet+ markdown into lines/paragraphs and label every block with a zone — `title-repeat`, `amendment-history`, `toc`, `index-list` (aperçu documentaire), `keywords`, `sharepoint-residue`, `body`, `annex`, `signature`; (2) index only `body` (+ `annex` when tabular) while storing the zone spans so `fetch` returns the untouched original. Stage 1 starts as rules (jusText-style block features: length, stopword density, link/reference density, digit ratio, position, regex hits), which also weakly label a few thousand blocks to train a logistic-regression / small CRF over cheap features (or `potion` static embeddings) that generalises beyond the regexes.

**Why it fits this project**

- Cleaning is already the cheapest proven gain: preamble stripping gave BM25 on B 0.346 → 0.372 and e5-small 0.438 → 0.466 (EXPERIMENTS.md §3.8). The 21k corpus (C) adds TOC-only docs, SharePoint `<span>` residue, repeated titles, keyword lines, index lists — none covered by the current regex.
- Zoning also feeds other ideas: dropping index-only documents (ingestion policy), `document_type`/TOC detection (ideas 24, 26), and clean chunk boundaries for ≤1,200-char chunks.
- CPU-only and LLM-free: features are bag-of-cheap-signals; a 100k-line classifier trains in seconds.
- Provenance is a hard requirement (citable legal text): zone spans, not deletions.

**Evidence**

- Web boilerplate: trafilatura's 990-doc benchmark (docs, 2026-08): trafilatura F1 0.924, jusText 0.862, readability 0.826, boilerpipe (boilerpy3) 0.807 — rule/heuristic stacks with stopword density + length + link density remain competitive; jusText thresholds: `LENGTH_LOW 70`, `LENGTH_HIGH 200`, `STOPWORDS 0.30/0.32`, `MAX_LINK_DENSITY 0.2`, plus context-sensitive relabelling of short blocks between good/bad neighbours (algorithm.rst).
- Boilerpipe (Kohlschütter, WSDM 2010): shallow text features (word count, link density, text density) + decision tree beat DOM-heavy methods; reported retrieval-effectiveness gains from removal (unverified numbers — page 404).
- Web2Text (ECIR 2018, arXiv 1801.02607): CNN potentials + HMM over the block sequence, SOTA on CleanEval and *improved retrieval on ClueWeb12* — sequence context matters, exact gains unverified here.
- Legal zoning: SemEval-2023 LegalEval rhetorical roles (preamble/facts/analysis/ruling…): baseline F1 54.7, best 72.4 with transformers; BiLSTM-CRF competitive — but this is semantic zoning of judgments, much harder than our structural zoning.
- Local: regex preamble stripping +0.026 MRR (BM25) / +0.028 (e5-small) on B, exp 08.

**How we would implement it**

1. **Block features** (per line/paragraph): char length, stopword ratio (French list already in BM25 pipeline), digit/punct ratio, ratio of tokens matching `Art\.|§|M\.B\.|Numac|AR|L\.`, uppercase ratio, relative position (0–1), distance to first heading, duplicate-of-title flag, markdown heading depth, bullet-list run length, `<span>`/`&nbsp;` residue flag.
2. **Weak labels**: extend `_PREAMBLE_LINE`/`_NOTE_TAIL` with TOC (`^\d+(\.\d+)*\s+\S` runs, "Table des matières"), signature (`Le Ministre|Pour le Ministre|Namur, le|Bruxelles, le`), keywords (`Mots[- ]cl[ée]s|Trefwoorden`), index lists (`## Commentaire` empty/N/A per MYFIN_ARBORESCENCE). Label ~3k blocks from 300 stratified docs; hand-check 300 in a spreadsheet (2–3 h).
3. **Model**: `sklearn` LogisticRegression / LightGBM on features + previous/next block predictions (a cheap "context-sensitive" pass à la jusText), or `sklearn-crfsuite` for true sequence labelling. Evaluate per-zone F1 against the hand-checked set.
4. **Provenance**: store `zones: [{start, end, label, conf}]` in the document manifest; chunker reads `body` spans; `fetch` returns original markdown with an optional `clean=true` flag. Never rewrite the source `.md`.
5. **Measure**: rerun harness on B and C with (a) regex-only, (b) classifier, (c) classifier + index-list document drop; append to `leaderboard.jsonl`.

**Expected gain and cost**

+0.01–0.04 MRR on C (regex gave +0.03 on B; C has more noise types, but BM25 on C is already 0.577 with descriptive titles), larger effects on hit@1 and on dense legs, and fewer garbage chunks reaching the reranker (latency). Cost: ~2 days engineering, 3 h labelling, seconds of training, negligible at ingestion.

**Risks / open questions**

- Over-stripping: "annexe" tables and amendment dates are sometimes the answer (temporal questions, idea 41); keep zones retrievable via metadata rather than deleted.
- Weak-label leakage: a classifier trained on regex output may just relearn the regex; the hand-checked slice must include regex misses.
- Dutch bodies need NL stopword features.
- Which zone gains actually transfer to C is unmeasured; the +0.03 came from a 40-question set.

**Verdict**

**try-now** — the +0.03 regex result is the strongest cheap signal in the log, and generalising it with weak labels plus a feature classifier costs two CPU-free days while keeping the source text intact.

**Sources**

- https://trafilatura.readthedocs.io/en/latest/evaluation.html
- https://aclanthology.org/2021.acl-demo.15.pdf (trafilatura)
- https://github.com/miso-belica/jusText/blob/main/doc/algorithm.rst
- https://arxiv.org/abs/1801.02607 (Web2Text)
- Kohlschütter et al., *Boilerplate Detection using Shallow Text Features*, WSDM 2010 (boilerpipe; original page 404)
- https://aclanthology.org/2023.semeval-1.318.pdf (LegalEval rhetorical roles)
- https://arxiv.org/abs/2306.01116 (RefinedWeb; trafilatura in LLM data pipelines — not verified in detail)
- Local: `experiments/08_corpus_b_cleanup/cleanup.py`, `experiments/EXPERIMENTS.md` §3.8–3.9, `MYFIN_ARBORESCENCE.md` § Classification
