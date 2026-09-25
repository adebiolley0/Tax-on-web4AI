#!/bin/bash
# Sequential job queue for experiment 12 (one torch job at a time, 2 threads: the box has
# 4 cores shared with other experiments). Cheap/informative jobs first, 560M-class last.
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=0 EXP12_THREADS=2
cd "$(dirname "$0")"
mkdir -p logs
run() { echo "=== $(date '+%H:%M:%S') $*"; uv run python "$@" 2>&1 | grep -vE "Warning: You are sending|Loading weights|it/s\]" ; echo "=== $(date '+%H:%M:%S') done $1 (rc=${PIPESTATUS[0]})"; }
{
run run_sparse.py  --corpus A --model opensearch
run run_colbert.py --corpus A --model colbert-fr
run run_sparse.py  --corpus B --model opensearch --dense e5-small
run run_colbert.py --corpus B --model colbert-fr --dense e5-small
run run_bgem3.py   --corpus A
run run_colbert.py --corpus A --model jina-colbert-v2
echo QUEUE_DONE
} > logs/queue.log 2>&1
