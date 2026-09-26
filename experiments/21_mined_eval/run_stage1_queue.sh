#!/bin/bash
# Part 1 stage-1 builds: e5 query embeddings under the torch lock (tiny), then the numpy/bm25s stage-1 cache.
cd /home/user/Tax-on-web4AI/experiments/14_ltr_fusion
for C in B C; do
  flock /home/user/Tax-on-web4AI/experiments/.torch.lock env OMP_NUM_THREADS=4 HF_HUB_OFFLINE=1 \
    .venv/bin/python ../21_mined_eval/embed_queries.py --corpus $C
  env OMP_NUM_THREADS=4 .venv/bin/python ../21_mined_eval/build_stage1.py --corpus $C
done
echo STAGE1_QUEUE_DONE
