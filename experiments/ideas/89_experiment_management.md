# 89 — Reproducibility and experiment management for retrieval research

**Idea**

Keep the current harness and add only what makes a run *re-derivable* and *comparable*: a provenance stamp on every leaderboard row, pydantic run configs with a config hash, a shared cache for reranker scores (generalising `14_ltr_fusion/score_rerankers.py`), TREC-format run/qrels dumps so `ranx`/`ir-measures` can evaluate, fuse and test significance, and git-tracked question sets with a hash. No MLflow, W&B, Hydra or DVC server.

**Why it fits this project**

- The harness already does the hard part: 685 result JSONs and 833 leaderboard rows are git-tracked, per-question ranks are stored, embeddings are keyed by SHA of (model, extra, texts).
- What a row does *not* record: git commit, harness/package versions, question-set hash, model revision, seed. `results.py` writes `ts, experiment, run, corpus, metrics, timing, config` only. After `08_corpus_b_cleanup` and question edits, old rows are silently incomparable; `print_leaderboard`'s "latest per run" rule hides that.
- Reranker scores (the costliest stage after embeddings on CPU) are cached only inside `14_ltr_fusion`, not in `rag_eval.cache`.
- Metrics are hand-rolled (`metrics.py`), unchecked against trec_eval; fusion/statistics (idea 72) would be re-implemented per experiment.
- A one-person, one-box project has no team-server need; MLflow/W&B add a daemon and a second source of truth next to a JSONL git already diffs.

**Evidence**

- ranx: 12 metrics tested against trec_eval, 25 fusion methods (RRF, CombSUM, Weighted Sum, Condorcet, …), 7 normalisations (min-max, ZMUV), paired t-test / Fisher randomisation / Tukey HSD via `compare`, `optimize_fusion`, LaTeX export. https://github.com/AmenRa/ranx
- ir-measures: uniform measure syntax (`nDCG@10`, `RR`, `R@10`), wraps pytrec_eval/trectools, works on TREC files or pandas. https://ir-measur.es/en/latest/
- ir_datasets: catalog + custom-dataset guide; no Belgian/French legal set. https://ir-datasets.com/
- MLflow Tracking: params/metrics/artifacts per run, file store default, sqlite/server optional, `mlflow server` UI. https://mlflow.org/docs/latest/ml/tracking/
- Hydra 1.3: YAML composition, CLI overrides, `-m` multirun, `.hydra/config.yaml` per run; Python 3.6–3.11 on the stable page (we run 3.12 — check before adopting). https://hydra.cc/docs/intro/
- DVC: `.dvc` pointer files, local-folder remote supported, `dvc exp`/`metrics`/`params`. https://doc.dvc.org/start

**How we would implement it**

1. `rag_eval/provenance.py`: `git rev-parse HEAD` + dirty flag, `uv.lock` hash of the calling project, `rag_eval` version, `torch`/`sentence_transformers` versions, question-file SHA, corpus manifest SHA, `OMP_NUM_THREADS`, seed. `append_leaderboard` adds them as `prov`.
2. `RunConfig` (pydantic, frozen): model, model revision, chunker, fusion, reranker, top-k, seed; `config_hash = sha256(model_dump_json())`; the result filename and cache keys use it. Model revisions pinned in one `MODELS` table (today only names are hashed, so updated HF weights would hit a stale cache).
3. `ScoreCache` beside `EmbeddingCache`: key = (reranker, revision, query text, chunk text hash) → float, stored as one `.npz` per (reranker, corpus, chunker) with a dict index; move `score_rerankers.py` onto it.
4. `save_result` also writes `run.trec` (qid Q0 docid rank score tag) and one `qrels.trec` per question set with graded rel (primary=2, secondary=1). Then `ranx.compare` gives paired tests across runs and `ranx.fuse/optimize_fusion` replaces per-experiment fusion code; `ir_measures.calc_aggregate` becomes a CI check that `metrics.py` agrees with trec_eval.
5. Question sets stay in git (they are ~100 KB JSON); add `questions_*.json` version field + changelog and refuse to compare rows whose question hash differs. Large artefacts (1.2 GB `emb_cache`, corpus md) stay gitignored; a `dvc add` with a local-folder remote is optional insurance, not required.
6. Determinism: one `seed_all()` (numpy/torch/random), logged; BM25 and encoding are deterministic on CPU, LightGBM/fine-tuning get 5-seed means (as in `train_ltr.py`).

**Expected gain and cost**

No MRR gain. Gain is trust: every row tells you what code, data and models produced it; stale-cache and question-drift bugs become detectable; fusion and significance tests come free and correct. Cost: ~1–2 days, two pure-Python deps (`ranx`, `ir-measures`), a one-off script to backfill `prov` (commit only) on old rows.

**Risks / open questions**

- `ranx` is numba-based; import time on the 4-core box and Python 3.12 wheels to verify.
- Backfilled provenance for old rows is partial; maybe archive the JSONL as `leaderboard_v0` and restart.
- Adding revision to cache keys invalidates the 1.2 GB cache once (hours of re-encoding).
- Hydra's official 3.12 support is unverified; pydantic + argparse is enough for our flat configs.

**Verdict**

try-now — one to two days, zero compute, and it is the precondition for ideas 72/79 (statistics, overfitting) to mean anything; skip MLflow/W&B/Hydra/DVC-server for a single-box project.

**Sources**

https://github.com/AmenRa/ranx · https://ir-measur.es/en/latest/ · https://ir-datasets.com/ · https://mlflow.org/docs/latest/ml/tracking/ · https://hydra.cc/docs/intro/ · https://doc.dvc.org/start · local: `experiments/common/rag_eval/{results,cache,metrics}.py`, `experiments/14_ltr_fusion/score_rerankers.py`, `experiments/ideas/72_small_sample_evaluation_statistics.md`
