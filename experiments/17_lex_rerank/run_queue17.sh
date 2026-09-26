#!/bin/bash
# Sequential reranker queue for experiment 17: waits until exp 15's eval_ft.py is gone, then runs one
# torch process at a time with all 4 threads (B and C at max_length 512; B again at 1024 as a check).
cd "$(dirname "$0")"
PY=../14_ltr_fusion/.venv/bin/python
export OMP_NUM_THREADS=4 HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false
until ! pgrep -f "eval_ft.py" >/dev/null; do sleep 30; done
echo "=== $(date +%T) start (eval_ft.py gone); load: $(cat /proc/loadavg)"
run() { log=$1; shift; echo "=== $(date +%T) rerank $*"; $PY rerank.py "$@" --threads 4 > "logs/$log" 2>&1 || echo "FAILED: $*"; tail -2 "logs/$log"; }
run rerank_B.log         --corpus B --depth 50 --max_length 512
run rerank_C.log         --corpus C --depth 50 --max_length 512
run rerank_B_len1024.log --corpus B --depth 50 --max_length 1024 --tag _len1024
echo "=== $(date +%T) queue done"
