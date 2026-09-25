#!/bin/bash
# Continuation of run_rerank_queue.sh: waits for the running A/mmarco job, then B/C mmarco, then
# bge-reranker-v2-m3 as a CASCADE (top-30 by mMARCO + top-10 per leg) — the plain union at K=30 is
# not affordable while five torch jobs share the 4 cores (0.6 s/pair observed for MiniLM alone).
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1
cd "$(dirname "$0")"
while pgrep -f "score_rerankers.py --corpus A --reranker mmarco" >/dev/null; do sleep 15; done
run() { echo "=== $(date '+%H:%M:%S') $*"; uv run python score_rerankers.py "$@" 2>&1 | grep --line-buffered -vE "Warning|warn|Loading weights"; }
run --corpus A --reranker mmarco-minilm      # no-op if complete (resume)
run --corpus B --reranker mmarco-minilm
run --corpus C --reranker mmarco-minilm
run --corpus A --reranker bge-reranker-v2-m3 --prefilter mmarco-minilm:30
run --corpus B --reranker bge-reranker-v2-m3 --prefilter mmarco-minilm:30
run --corpus C --reranker bge-reranker-v2-m3 --prefilter mmarco-minilm:20 --legs e5,bm25
echo "=== $(date '+%H:%M:%S') RERANK_QUEUE_DONE"
