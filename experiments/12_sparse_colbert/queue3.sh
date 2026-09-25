#!/bin/bash
# Re-ordered queue (the 105k-vocab OpenSearch MLM head costs ~58 min per 1,000 chunks at 2 threads on
# the loaded box, so the corpus-B sparse runs go last). Waits for the colbert-fr A job started by queue.sh.
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=0 EXP12_THREADS=2
cd "$(dirname "$0")"
while pgrep -f "[r]un_colbert.py --corpus A --model colbert-fr" >/dev/null; do sleep 30; done
run() { echo "=== $(date '+%H:%M:%S') $*"; uv run python "$@" 2>&1 | grep --line-buffered -vE "Warning: You are sending|Loading weights|it/s\]|LOAD REPORT|^Key|^---|linear.weight|Notes|UNEXPECTED|mean_resizing|torch_dtype" ; echo "=== $(date '+%H:%M:%S') done $1 (rc=${PIPESTATUS[0]})"; }
{
run run_colbert.py --corpus B --model colbert-fr --dense e5-small
run run_bgem3.py   --corpus A
run run_colbert.py --corpus A --model jina-colbert-v2
run run_sparse.py  --corpus A --model splade-fr
run run_sparse.py  --corpus B --model splade-fr --dense e5-small
run run_sparse.py  --corpus B --model opensearch --dense e5-small
echo QUEUE3_DONE
} > logs/queue3.log 2>&1
