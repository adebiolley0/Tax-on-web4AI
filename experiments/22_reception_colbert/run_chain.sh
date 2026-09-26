#!/bin/bash
# Experiment 22 chain after colbert_scores.py (queued separately under the torch lock):
#   legs (no lock) → stage 1 (no lock) → mMARCO scoring (lock) → bge scoring (lock) → reranked evaluation → learned ranker
set -u
cd "$(dirname "$0")"
PY=../14_ltr_fusion/.venv/bin/python
LOCK="flock ../.torch.lock env OMP_NUM_THREADS=4 HF_HUB_OFFLINE=1"
while [ ! -f cache/B_colbert_scores.npz ]; do sleep 60; done
sleep 5
$PY legs.py > logs/legs.log 2>&1 || { echo "legs failed"; exit 1; }
$PY run_stage1.py > logs/stage1.log 2>&1 || { echo "stage1 failed"; exit 1; }
$LOCK $PY rerank_score.py --what mmarco > logs/mmarco.log 2>&1 || { echo "mmarco failed"; exit 1; }
$PY run_rerank.py > logs/rerank_eval1.log 2>&1 || echo "rerank eval (mmarco only) failed"
$LOCK $PY rerank_score.py --what bge > logs/bge.log 2>&1 || { echo "bge failed"; exit 1; }
$PY run_rerank.py > logs/rerank_eval.log 2>&1 || { echo "rerank eval failed"; exit 1; }
$PY ltr.py > logs/ltr.log 2>&1 || { echo "ltr failed"; exit 1; }
echo "chain done"
