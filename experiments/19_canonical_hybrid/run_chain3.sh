#!/bin/bash
cd /home/user/Tax-on-web4AI/experiments/17_lex_rerank
E=../19_canonical_hybrid; PY=../14_ltr_fusion/.venv/bin/python
$PY $E/retrieve.py > $E/logs/retrieve2.log 2>&1 || { echo "retrieve failed"; exit 1; }
flock ../.torch.lock env OMP_NUM_THREADS=4 HF_HUB_OFFLINE=1 $PY $E/rerank.py > $E/logs/rerank2.log 2>&1 || { echo "rerank failed"; exit 1; }
$PY $E/evaluate.py > $E/logs/evaluate2.log 2>&1 || { echo "evaluate failed"; exit 1; }
echo "CHAIN3 DONE"
