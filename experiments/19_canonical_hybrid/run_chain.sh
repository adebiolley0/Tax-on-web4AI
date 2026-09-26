#!/bin/bash
# after embed.py: retrieval (human + mined) → reranker (lock) → evaluation
cd /home/user/Tax-on-web4AI/experiments/17_lex_rerank
E=../19_canonical_hybrid; PY=../14_ltr_fusion/.venv/bin/python
until grep -q "^done:\|Traceback" $E/logs/embed.log; do sleep 30; done
grep -q Traceback $E/logs/embed.log && { echo "EMBED FAILED"; exit 1; }
$PY $E/retrieve.py > $E/logs/retrieve.log 2>&1 || { echo "retrieve failed"; exit 1; }
$PY $E/retrieve.py --questions mined > $E/logs/retrieve_mined.log 2>&1 || { echo "retrieve mined failed"; exit 1; }
flock ../.torch.lock env OMP_NUM_THREADS=4 HF_HUB_OFFLINE=1 $PY $E/rerank.py > $E/logs/rerank.log 2>&1 || { echo "rerank failed"; exit 1; }
$PY $E/evaluate.py > $E/logs/evaluate.log 2>&1 || { echo "evaluate failed"; exit 1; }
echo "CHAIN DONE"
