#!/bin/bash
# Score all (question, candidate chunk) pairs once per corpus and reranker, sequentially
# (one torch job at a time on this 4-core box; 2 threads so other work keeps two cores).
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1
cd "$(dirname "$0")"
run() { echo "=== $(date '+%H:%M:%S') $*"; uv run python score_rerankers.py "$@" 2>&1 | grep -vE "Warning|warn|Loading weights"; }
run --corpus A --reranker mmarco-minilm
run --corpus B --reranker mmarco-minilm
run --corpus C --reranker mmarco-minilm
run --corpus A --reranker bge-reranker-v2-m3
run --corpus B --reranker bge-reranker-v2-m3
run --corpus C --reranker bge-reranker-v2-m3 --legs e5,bm25   # potion leg dropped: keeps the 0.7 s/pair job < 1 h
echo "=== $(date '+%H:%M:%S') RERANK_QUEUE_DONE"
