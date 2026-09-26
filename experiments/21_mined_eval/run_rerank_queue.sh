#!/bin/bash
# Part 2 reranker queue (each job takes the torch lock separately so other agents can interleave).
# Order: cheap mMARCO first (subsample + human), then bge on the subsample (C convex, B convex, C lexical),
# then bge on the human sets (convex top-20) if the budget allows.
cd /home/user/Tax-on-web4AI/experiments/14_ltr_fusion
E=../21_mined_eval
while [ ! -f $E/cache/C_stage1.npz ] || [ ! -f $E/cache/B_stage1.npz ] || [ ! -f $E/cache/C_lex_exp13_lex.npz ]; do sleep 60; done
run() { flock /home/user/Tax-on-web4AI/experiments/.torch.lock env OMP_NUM_THREADS=4 HF_HUB_OFFLINE=1 .venv/bin/python $E/score_rerankers.py "$@"; }
run --corpus B --reranker mmarco-minilm --set sub --cands convex05
run --corpus C --reranker mmarco-minilm --set sub --cands convex05
run --corpus B --reranker mmarco-minilm --set human --cands convex05
run --corpus C --reranker mmarco-minilm --set human --cands convex05
run --corpus C --reranker mmarco-minilm --set sub --cands lex13
run --corpus C --reranker bge-reranker-v2-m3 --set sub --cands convex05 --max-minutes 80
run --corpus B --reranker bge-reranker-v2-m3 --set sub --cands convex05 --max-minutes 60
run --corpus C --reranker bge-reranker-v2-m3 --set sub --cands lex13 --max-minutes 45
run --corpus C --reranker bge-reranker-v2-m3 --set human --cands convex05 --max-minutes 20
run --corpus B --reranker bge-reranker-v2-m3 --set human --cands convex05 --max-minutes 20
echo RERANK_QUEUE_DONE
