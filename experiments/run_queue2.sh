#!/bin/bash
# Second sequential queue (round 2 leftovers). Waits for the box to calm down (other agents'
# torch jobs) before starting, then runs one job at a time with all 4 threads.
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1
cd "$(dirname "$0")"
wait_for_load() { while awk '{exit !($1 > 5.0)}' /proc/loadavg; do sleep 120; done; }
run() { echo "=== $(date '+%H:%M:%S') $*"; wait_for_load; ( cd "$1" && shift && uv run python "$@" ) 2>&1 | grep -E "MRR=|Traceback|Error|saved|corpus|trained|pairs"; }
# exp 15: the first fine-tune run died at step 40/88 (box oversubscribed); re-run it alone.
run 15_finetune finetune_ce.py --epochs 2 --corpora A,B,C
echo QUEUE2_DONE
