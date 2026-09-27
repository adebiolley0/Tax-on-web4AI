# `rag_eval` — the shared evaluation harness

Pure-Python package (numpy; scipy for `stats`); experiments install it editable (`rag-eval = { path = "../common", editable = true }`).

## API (`from rag_eval import …`)

| area | names |
|---|---|
| documents | `Doc(doc_id, title, text, meta)`, `load_corpus_a(clean=False)` (91 md files), `load_corpus_b(codes=None)` (articles.jsonl), `load_corpus_c(doc_types, max_chars, limit)` (21k `myfin_docs`), `load_corpus("A"\|"B"\|"C")` → (docs, human questions), `parse_front_matter` |
| questions | `Question(qid, question, expected, secondary, meta)` with `.split`, `.exclude`, `.is_mined`; `load_questions_a/b/c()`, `load_questions_b("mined")`, `load_questions_mined("B"\|"C")`, `load_questions(corpus, None\|"mined"\|"all")`, `question_split`, `filter_split(qs, "train"\|"val"\|None)`, `slice_questions(qs)` |
| chunking | `whole_doc`, `fixed_chunks(max_chars, overlap, heading_split, prefix_title)`, `article_chunks(max_chars, overlap, prefix_context)` → `Chunk(chunk_id="<doc>#<i>", doc_id, text, title, meta)` |
| metrics | `evaluate_rankings(name, corpus, questions, rankings, config, timing, secondary_weight=0.5)` → `RunResult`; `dedupe_ranked` |
| results | `save_result(experiment, result, docs=None, questions=None)`, `load_result`, `print_leaderboard(corpus)`, `build_provenance`; `rag_eval.splits.split_metrics` |
| cache | `EmbeddingCache().get_or_compute(model, texts, encode, extra)` → `experiments/data/emb_cache/<key>.npy`; `cache_key` |
| stats | `from rag_eval.stats import compare_runs, compare_loaded, paired_stats, compare_many, min_detectable_delta` |
| mining | `python -m rag_eval.mining`; `rag_eval.legal_refs` (reference grammar) |

## Question sets

| file | n | ids | notes |
|---|---|---|---|
| `ingestion/validation_dataset/questions.json` | 31 (29 scored) | `Q1…` | corpus A; `expected_docs`, `secondary_docs`, `skip` |
| `experiments/data/corpus_b/questions_b.json` | 40 | `B1…` | human, article ids such as `cir92:130` |
| `experiments/data/corpus_c/questions_c.json` | 64 | `C1…` | human, `folder/stem` ids |
| `experiments/data/corpus_b/questions_b_mined.json` | 304 | `MB-<PQ\|FAQ\|RUL>-<sha1[:8]>` | mined, see below |
| `experiments/data/corpus_c/questions_c_mined.json` | 697 | `MC-…` | mined |

Common keys: `id`, `question`, `expected` (primary targets: rank of the first one drives MRR / hit@k,
all of them drive recall@k), `secondary` (relevance 0.5 in nDCG only), `topic`, `notes`. Mined sets add
`source` (`pq` parliamentary question, `faq` heading, `ruling` objet), `source_doc`, `date`,
`label_basis` (`explicit` = a named code was cited, `bare` = "article N" resolved with the document's
domain, `document` = the source itself is the target), `split` (informative) and **`exclude`**: doc ids
removed from a ranking *before* scoring — for PQ questions the PQ the text was copied from, which would
otherwise be a trivial rank-1 hit. `evaluate_rankings` applies `exclude` for every question (empty on
the human sets). The human sets are never edited; the mined sets are regenerated, never hand-edited.

## Metrics and split protocol

`evaluate_rankings` scores document-level rankings (chunk hits are deduplicated to their first document):
MRR, hit@1/3/5/10, recall@5/10, nDCG@5/10, plus `train_*` / `val_*` (MRR, hit@1, hit@5, recall@10, n).
`per_question[qid] = {rank, rr, top5, expected, split}` is stored with every run so later paired
comparisons need no re-run. **Split**: `question_split(qid)` = md5 parity of the id (even → train, odd →
val; A 14/15, B 24/16, C 34/30, mined B 145/159, C 352/345). Choose every parameter on `train` only and
report `val`; the bars in `EXPERIMENTS.md` are val numbers. `python -m rag_eval.splits C` prints the
val-sorted leaderboard recomputed from the stored ranks.

## Saved results and provenance

`save_result("NN_exp", result)` writes `experiments/results/NN_exp/<corpus>__<safe_name>.json` and
appends a row to `experiments/results/leaderboard.jsonl` (`ts, experiment, run, corpus, metrics…,
timing, config, prov`). The **provenance stamp** (`provenance` / `prov`) records git commit + dirty flag,
UTC time, host, harness and Python versions, the question file(s) the scored ids come from with their
SHA-256 (`file1+file2` when a run mixes human and mined questions), the SHA-256 of the sorted question
ids, and a corpus fingerprint (n docs + SHA-256 of the sorted doc ids of the source on disk, or of the
`docs=` actually indexed). `print_leaderboard("C")` lists the best runs by full-set MRR.

## Paired statistics

```
python -m rag_eval.stats C 09_corpus_c/bm25__fixed1200_title__bm25+bge-reranker-v2-m3@30 17_lex_rerank/lex13+bge@20 --split val [--ks 1,5,10] [--json]
```
Δ = B − A per question on the shared ids: paired t-test, exact sign-flip test (≤ 20 non-zero deltas,
Monte-Carlo above), BCa bootstrap 95 % CI, wins/losses/ties, effect size, minimum detectable delta at that
n (`questions_needed` inverts it). `compare_many(baseline, candidates)` adds a Westfall–Young max-T correction.

## Regenerating the mined sets

```
cd experiments/common && uv run python -m rag_eval.mining --check      # rebuild to a temp dir, byte-compare (≈ 30 s)
cd experiments/common && uv run python -m rag_eval.mining [--report-dir DIR]   # rewrite experiments/data/…_mined.json
```
Regex only (`rag_eval.legal_refs`: article grammar, code-family hints, title keys), no LLM; filters and
caps are documented in `rag_eval/mining.py`. Ids hash the source document, so text-cleaning edits never
move a question between splits; no target or source of the 133 human questions appears in a mined set.

## Tests

`cd experiments/common && uv run --with pytest pytest -q` — 28 tests, ≈ 1.5 s, no models, no corpora:
toy-ranking metrics (incl. `exclude`, secondary weight), split determinism, chunkers, stats on synthetic
paired data, `save_result` round-trip with provenance in a temp dir, schema of the real question files.
