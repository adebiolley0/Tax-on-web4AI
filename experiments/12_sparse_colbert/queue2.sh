#!/bin/bash
# Second queue (French SPLADE, added once the disk was freed): starts after queue.sh has finished.
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=0 EXP12_THREADS=2
cd "$(dirname "$0")"
while pgrep -f "[q]ueue.sh" >/dev/null; do sleep 30; done
run() { echo "=== $(date '+%H:%M:%S') $*"; uv run python "$@" 2>&1 | grep --line-buffered -vE "Warning: You are sending|Loading weights|it/s\]" ; echo "=== $(date '+%H:%M:%S') done $1 (rc=${PIPESTATUS[0]})"; }
{
run run_sparse.py --corpus A --model splade-fr
run run_sparse.py --corpus B --model splade-fr --dense e5-small
echo QUEUE2_DONE
} > logs/queue2.log 2>&1
