#!/bin/bash
cd /home/user/Tax-on-web4AI/experiments/17_lex_rerank
E=../19_canonical_hybrid; PY=../14_ltr_fusion/.venv/bin/python
flock ../.torch.lock env OMP_NUM_THREADS=4 HF_HUB_OFFLINE=1 $PY $E/rerank.py > $E/logs/rerank.log 2>&1 || { echo "rerank failed"; exit 1; }
$PY $E/evaluate.py > $E/logs/evaluate.log 2>&1 || { echo "evaluate failed"; exit 1; }
echo "CHAIN2 DONE"
