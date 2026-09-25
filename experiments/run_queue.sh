#!/bin/bash
# Single sequential job queue: on this 4-core CPU box, concurrent torch jobs thrash on
# OpenMP spin-waits (measured 10x-40x slowdowns). Run one job at a time with all threads.
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1
cd "$(dirname "$0")"
run() { echo "=== $(date '+%H:%M:%S') $*"; ( cd "$1" && shift && uv run python "$@" ) 2>&1 | grep -E "MRR=|Traceback|Error|shard|saved|corpus"; }
run 03_hybrid_rerank run_hybrid.py --corpus A --model bge-m3 --chunker fixed1500_title --fusions rrf,convex0.5 --rerankers bge-reranker-v2-m3 --rerank_top 30
run 09_corpus_c run_corpus_c.py --runs bm25_chunk --rerank_base bm25 --rerankers mmarco-minilm --rerank_top 30
run 03_hybrid_rerank run_hybrid.py --corpus A --model bge-m3 --chunker fixed1500_title --fusions convex0.5 --rerank_base convex0.5 --rerankers bge-reranker-v2-m3,bge-reranker-base --rerank_top 30
run 09_corpus_c run_corpus_c.py --runs bm25_chunk --rerank_base bm25 --rerankers bge-reranker-v2-m3 --rerank_top 30
run 09_corpus_c encode_corpus.py --model e5-small --chunker fixed1200_title
run 09_corpus_c run_corpus_c.py --model e5-small --runs dense,rrf,convex0.3,convex0.5,convex0.7
run 09_corpus_c run_corpus_c.py --model e5-small --runs convex0.5 --rerank_base convex0.5 --rerankers bge-reranker-v2-m3 --rerank_top 30
run 02_dense_sweep run_sweep.py --corpus B --models e5-small --chunkers article_ctx_1200
run 02_dense_sweep run_sweep.py --corpus B --models e5-small --chunkers article_ctx_1200 --clean
run 03_hybrid_rerank run_hybrid.py --corpus B --model e5-small --chunker article_ctx_1200 --fusions dense,bm25,rrf,convex0.3,convex0.5,convex0.7 --rerankers mmarco-minilm,bge-reranker-v2-m3 --rerank_top 30
run 02_dense_sweep run_sweep.py --corpus B --models e5-base --chunkers article_ctx_1200 --clean
run 02_dense_sweep run_sweep.py --corpus B --models e5-base --chunkers article_ctx
echo QUEUE_DONE
