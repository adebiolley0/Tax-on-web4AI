#!/bin/bash
# Start the reranker queue only when no other torch job (exp 15 fine-tuning) is running.
cd "$(dirname "$0")"
while pgrep -f "finetune_ce.py" >/dev/null || pgrep -f "build_stage1.py" >/dev/null; do sleep 30; done
echo "box free at $(date '+%H:%M:%S'), starting queue"
./run_rerank_queue.sh
