# best – the best measured retrieval pipelines, as one runnable package

This folder is the distilled result of the retrieval experiments (`experiments/EXPERIMENTS.md`): one clean,
documented implementation of the best system found for each corpus, with the code it needs copied in (nothing is
imported from the other `experiments/NN_*` folders, which can be deleted; git history keeps them). It reproduces the
measured numbers rank for rank (§2) and answers new questions with the same models (§4).

| corpus | pipeline | measured (source) | round-1 bar |
|---|---|---|---|
| **B** statute articles (5,853 default subset of the legal-code PDFs) | z-score convex fusion, fixed equal weights, of reception-BM25F + French ColBERT + e5-small; **length gate**: ≤ 25 words → mMARCO-MiniLM over the best 3 chunks of the top-30 articles, β 0.8 with the fused score; longer → reception + e5 un-reranked | human val **0.613** / all **0.628**, mined (304) **0.534** (exp 22 §2.5) | val 0.570 / all 0.522 |
| **C** Fisconet+ documents (21,259) | exp-13 BM25F (title ×8, k1 0.9 / b 0.4, tok01 + numbers) over fixed1200_title chunks → top-20 chunks → bge-reranker-v2-m3 (512 tokens, reranker score only) → documents by best chunk, lexical tail | human val **0.688** / all **0.719** (exp 17, `lex13+bge@20`) | val 0.665 / all 0.703 |
| **A** the repo's 91 validation documents | whole-document BM25, exp-01 tokenizer, k1 1.5 / b 0.75 | val **0.736** / all 0.695 (exp 01) | val 0.736 / all 0.703 |

MRR at document level; "val" = the md5-parity validation half never used for any choice; "all" = the full human set.
The C headline of 0.733 in EXPERIMENTS.md §2 is the β 0.7 interpolated variant of the same run (val 0.675, β chosen on
train and worse on val, §3.11); the pipeline shipped here is the reranker-only depth 20, the train-selected point.

## 1. Files

| file | what |
|---|---|
| `config.py` | every fixed constant: model ids, chunking, the exp-13 lexical configs, reception field, fusion weights, gate threshold, depths, β; `qkey()` (question-text cache key), `fingerprint()` (chunk universe) |
| `corpus.py` | loaders (A / B / C through `rag_eval`), exp-08 `clean_article` / `region_of_code`, the chunk `Universe` (B: article_ctx_1200 = 10,869 chunks; C: fixed1200_title = 201,404) and the lexical units per corpus |
| `lexical.py` | exp-13 `Tokenizer` (+ number normalisation), sparse `TokenStore` / `FieldIndex`, `bm25f_matrix`, cue tokens, `LexicalIndex` (build / save / load / score, optional reception field) |
| `reception.py` | exp-11 reference grammar + exp-20 reception extraction: citing sentences and titles per statute article from `myfin_docs` (`--exclude-mined` = leak-free variant for the mined evaluation sets) |
| `dense.py` | e5-small: chunk vectors from the shared `experiments/data/emb_cache`, query vectors cached per question text (`cache/q_e5.npz`), on-the-fly encoding otherwise |
| `colbert.py` | PyLate colbert-fr (exp-12 set-up: `<unk>` markers, 48-token queries): persisted fp16 token index (`index/B_colbert/`, 0.6 GB), exact MaxSim, per-question score cache |
| `fusion.py` | z-score convex fusion, min-max interpolation, chunk → document max |
| `rerank.py` | mMARCO-MiniLM and bge-reranker-v2-m3 wrappers with a (question text, chunk index) score cache stamped with the chunk-universe fingerprint |
| `gate.py` | the length gate (25 words) |
| `pipeline.py` | `retrieve_b / retrieve_c / retrieve_a(question, k)` → `Result(route, hits=[Hit(doc_id, rank, score, reranked, title, passages)])`; CLI `python pipeline.py B "question"` |
| `evaluate.py` | runs the pipelines on the stored question sets through `rag_eval`, saves as experiment `best`, compares per-question ranks with the source runs |
| `build_indexes.py` | builds `index/` (lexical pickles, reception, ColBERT token index, e5 chunk vectors) |
| `import_caches.py` | one-off: re-keys the score caches of exps 17 / 21 / 22 by question text and links the exp-20 reception and exp-22 ColBERT index into `cache/` and `index/` (skips sources that no longer exist) |
| `cache/`, `index/` | git-ignored; `runs/` holds the evaluation outputs (`tables.md`, `eval_*.json`) |

## 2. Reproduction (`runs/tables.md`, `experiments/results/best/*.json`, leaderboard rows `best`)

All four evaluations were run from the caches only (no cross-encoder or ColBERT scoring beyond what the experiments
had already scored; e5 query vectors and ColBERT rows imported from exps 21 / 22, mMARCO pairs from exp 22, bge pairs
from exp 17). Every per-question rank is identical to the run that measured the pipeline:

| corpus | question set | n | MRR train | MRR **val** | MRR all | H@1 all | R@10 all | bar (val / all) | identical ranks vs source run |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| B | human | 40 | 0.639 | **0.613** | 0.628 | 0.450 | 0.900 | 0.570 / 0.522 | 40/40 (`22_reception_colbert/B__gate_T25__mmarco_b0.8__rec_e5.json`) |
| B | mined | 304 | 0.523 | **0.545** | 0.534 | 0.438 | 0.760 | 0.570 / 0.522 | 304/304 (`22_reception_colbert/B__gate_T25__mmarco_b0.8__rec_e5__mined.json`) |
| C | human | 64 | 0.757 | **0.688** | 0.719 | 0.625 | 0.891 | 0.665 / 0.703 | 64/64 (`17_lex_rerank/C__lex13_bge_20.json`) |
| A | human | 29 | 0.666 | **0.736** | 0.695 | 0.586 | 0.897 | 0.736 / 0.703 | 29/29 (`01_bm25/A__doc_stem_stop_qstop_noaccent.json`) |

Routes on B: 35 of the 40 human questions take the mMARCO route, 7 of the 304 mined ones (the gate is in practice a
population switch, exp 22). The mined evaluation uses the leak-free reception field (no sentence from a mined
question's source document); production uses the full field.

## 3. Setup and running

Until this folder has its own venv, run it with an existing one (round-3 rule: no new torch venv on this box):

```bash
cd experiments/14_ltr_fusion                      # torch + sentence-transformers + bm25s + scipy + rag_eval  (no PyLate)
uv run python ../best/import_caches.py            # once, while the old experiment folders still exist (26 s)
uv run python ../best/build_indexes.py --corpus B # lexical index (4 s) [+ reception 54 s if index/B_reception.json is missing]
uv run python ../best/build_indexes.py --corpus C # lexical index over 201k chunks (2.5 min)
uv run python ../best/build_indexes.py --corpus A
uv run python ../best/evaluate.py --corpus all    # cache-only; B 23 s, C 35 s, A 1 s
```

Anything that has to run a model goes under the torch lock with 4 threads, and ColBERT needs PyLate
(`../12_sparse_colbert/.venv` until `uv sync` here):

```bash
cd experiments/best
LOCK="flock ../.torch.lock env OMP_NUM_THREADS=4 HF_HUB_OFFLINE=1"
$LOCK ../12_sparse_colbert/.venv/bin/python pipeline.py B "Puis-je déduire les frais de garde de mes enfants ?"
$LOCK ../14_ltr_fusion/.venv/bin/python pipeline.py C "Quel est le délai pour introduire une réclamation ?"
$LOCK ../12_sparse_colbert/.venv/bin/python build_indexes.py --corpus B --colbert   # only if index/B_colbert is missing (38 min)
$LOCK ../14_ltr_fusion/.venv/bin/python build_indexes.py --corpus C --encode        # only if the e5 chunk vectors left data/emb_cache (hours)
$LOCK ../12_sparse_colbert/.venv/bin/python colbert.py --sets human,mined           # refill cache/B_colbert_scores.npz (4 min)
```

Later, as a standalone project: `cd experiments/best && uv sync && uv run python evaluate.py --corpus all`
(`pyproject.toml`: torch CPU, sentence-transformers, PyLate, bm25s, PyStemmer, numpy, scipy, `rag_eval` from
`../common` as a path dependency; `lightgbm` / `scikit-learn` under the optional `learned` extra). Models are read from
the HF cache (`HF_HUB_OFFLINE=1` works).

From Python:

```python
from pipeline import retrieve_b, retrieve_c, retrieve_a
res = retrieve_b("Puis-je déduire les frais de garde de mes enfants de moins de 14 ans ?", k=5)
res.route            # 'short: rec+colbert+e5 → mMARCO@30 β0.8'
for h in res.hits:   # Hit(doc_id='cir92:145/35', rank=1, score=1.0, reranked=True, title=…, stage1_score=…, passages=[Passage(chunk_idx, chunk_id, text, score)])
    ...
```

`RetrieverB(cache_only=True)` / `RetrieverC(cache_only=True)` raise instead of loading a model on a cache miss
(evaluation mode). Caches are keyed by question text and stamped with the chunk-universe fingerprint, so a changed
corpus invalidates them by assertion rather than silently.

## 4. Cost per query (4 CPU threads, this box; measured with `pipeline.py`, models already loaded)

| corpus | stage | cost |
|---|---|---|
| B | reception BM25F (8,035 units + reception field) | 3 ms |
| B | e5-small query encoding + dot product over 10,869 chunks | 0.13 s |
| B | colbert-fr query encoding + brute-force MaxSim over 10,869 chunks (fp16 token index in RAM/mmap) | 2.2 s (0.7 s of it MaxSim) |
| B | mMARCO-MiniLM, ≈ 70 pairs (best 3 chunks × 30 articles), 512 tokens | 8–10 s |
| B | **short question, total** / long question (no ColBERT, no reranker) | **≈ 11 s** / 0.15 s |
| C | exp-13 BM25F over 201k chunks | 25–30 ms |
| C | bge-reranker-v2-m3, 20 pairs, 512 tokens | 20–40 s (1–2 s per pair on this CPU; exp 17: 0.94 s/pair) |
| A | whole-document BM25 | 1 ms |

Model loads (once per process): e5-small ≈ 13 s, colbert-fr + token index ≈ 24 s, mMARCO ≈ 4 s, bge ≈ 4 s,
corpus C load + lexical index ≈ 35 s. Cached questions cost 5–30 ms end to end. A GPU brings the cross-encoders to
well under a second; PLAID/Voyager would bring MaxSim to milliseconds (exp 12 probed it).

One-off index costs: reception extraction 54 s; lexical indexes 4 s (B) / 2.5 min (C); ColBERT corpus encoding
38 min (B, 210 ms / chunk); e5 chunk vectors ≈ 10 min (B) / hours (C, 201k chunks) — the latter two are kept in
`index/` and `experiments/data/emb_cache`.

## 5. Design decisions (one line each, with the EXPERIMENTS.md section that measured it)

1. **Lexical stage = the exp-13 configuration** (exp-01 tokenizer, BM25F title / heading fields, thousand-group
   number normalisation, per-corpus k1 / b, exp-08 preamble cleanup on B; no RM3 / PMI): confirmed at n = 304 / 697
   (B +0.048, max-T p < 0.001) — §3.11, §3.12 (exp 21), §4 amendment 1.
2. **Reception field on B**: each article indexed with the sentences (and titles) of the documents that cite it —
   +0.115 MRR lexical on 304 mined questions (p < 0.001), the only LLM-free fix of the paraphrase gap — §3.12 (exp 20),
   amendment 8. Dense reception vectors added nothing, so the field is lexical only.
3. **Three legs, fixed equal z-score weights** (reception-BM25F, colbert-fr, e5-small): best B first stage on the
   human set (val 0.545 / all 0.638, R@30 0.95), weights pre-registered, never tuned — train-tuned weights do not
   transfer (§3.10) and RRF is refuted at p < 0.001 (§3.12 exp 21, amendment 9).
4. **ColBERT with the 48-token query window**: 256 tokens collapses on short questions (val 0.432 → 0.129) — §3.12 (exp 22).
5. **Length gate at 25 words**: mMARCO @30 with β 0.8 is +0.092 on the human set (p 0.012) but destructive on long
   document-like questions (−0.18 to −0.30, p < 0.001); the un-reranked reception + e5 fusion is the best long-side
   system (routing bge there is worse, −0.114); T chosen on train splits only — §3.12 (exps 21, 22), amendment 8.
6. **Best 3 chunks per article, doc = max, β 0.8 interpolation** with the fused score (exp-14 value, not re-tuned) — §3.10, §3.12.
7. **C: lexical → bge @20, reranker score only, 512 tokens**: val 0.688 vs bar 0.665, full 0.719 vs 0.703; the first
   stage barely matters behind bge, depth 20–30 flat, β interpolation loses on val, 512 = 1024 tokens — §3.11 (exp 17),
   amendments 4 and 10 (rerank chunks, not one chunk per document — exp 19).
8. **A: whole-document BM25**: the honest best first stage on A (oof 0.695, val 0.736); every reranker or fusion on
   A is within noise of it on 12 validation questions — §3.2, §3.10.
9. **Chunks of ≤ 1,200 chars with title / heading-path prefix** (token-safe for 512-token encoders) — §3.3, §4 item 1.
10. **Caches keyed by question text + chunk-universe fingerprint**: every experiment's score cache was keyed by
    question id and chunk index, which is meaningless for new questions or a re-parsed corpus.

**Left out on purpose.** The learned rankers (exp 21 LightGBM-tiny on mined labels, exp 24 pooled labels) tie the
bars on the human sets and need the exp-21 40-feature table over a different candidate universe — not worth a module
for a tie (§3.12; the `learned` extra keeps the dependencies available). The exp-19 rule-based ingestion layer
(quality filter, boilerplate zoning, edition canonicalisation, facets) brought no ranking gain (§3.12) and is 25 kB of
rules; it belongs in the ingestion pipeline of the MCP server, not here — its absence shows as yearly editions of the
same CIR 92 article ranking 1-2-3 on C (see the live example in §3). The exp-20 intent bank is an answer object, not a
fusion leg (§3.12). Region / document-type filters are metadata for the MCP `search` tool, not a retrieval stage.

## 6. What a new corpus needs

Re-parse → `build_indexes.py` for the lexical indexes (and `reception.py` if the statute corpus changed), the e5 chunk
vectors (`--encode`) and the ColBERT token index (`--colbert`); the score caches invalidate themselves through the
fingerprint. Re-run `evaluate.py` and compare with `runs/tables.md`; a human-set delta below 0.10 is undecidable
(§3.12, amendment 13) — use the mined sets and `rag_eval.stats` first.
