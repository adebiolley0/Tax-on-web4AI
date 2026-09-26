#!/bin/bash
# Second pass once run_chain1b.sh is done and both colbert query variants exist (q256, q256 trimmed):
# legs (attach variants) → stage 1 (query length selected on mined train) → mMARCO pairs of the final pipeline (lock)
# → bge on the human set for the final pipeline only (lock; budget) → evaluation → ranker
set -u
cd "$(dirname "$0")"
PY=../14_ltr_fusion/.venv/bin/python
LOCK="flock ../.torch.lock env OMP_NUM_THREADS=4 HF_HUB_OFFLINE=1"
until grep -q "chain done" logs/chain.log 2>/dev/null && [ -f cache/B_colbert_scores_q256.npz ] && [ -f cache/B_colbert_scores_q256t.npz ]; do sleep 60; done
$PY legs.py > logs/legs2.log 2>&1 || { echo "legs2 failed"; exit 1; }
$PY run_stage1.py > logs/stage1_2.log 2>&1 || { echo "stage1_2 failed"; exit 1; }
$LOCK $PY rerank_score.py --what mmarco > logs/mmarco2.log 2>&1 || { echo "mmarco2 failed"; exit 1; }
$LOCK $PY rerank_score.py --what bge --no-bge-mined > logs/bge2.log 2>&1 || { echo "bge2 failed"; exit 1; }
$PY run_rerank.py > logs/rerank_eval2.log 2>&1 || { echo "rerank eval2 failed"; exit 1; }
$PY ltr.py > logs/ltr2.log 2>&1 || { echo "ltr2 failed"; exit 1; }
echo "chain2 done"
