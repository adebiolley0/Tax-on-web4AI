#!/bin/bash
# Sequential sweep schedule (CPU-only box): wait for the in-flight bge-m3 run, then
# small models on A (3 chunkers), large models on A (whole-doc only: ~1 h per 1k chunks
# at 512 tokens makes chunked runs of 560M models impractical here), then corpus B with
# the small models (raw and cleaned text).
cd "$(dirname "$0")"
until [ -f ../results/02_dense_sweep/A__bge-m3__fixed1500_title.json ]; do sleep 30; done
pkill -f "run_sweep.py --corpus A --models bge-m3" ; sleep 5
uv run python run_sweep.py --corpus A --models static-sim-ml,minilm-l12,e5-small,e5-base,gte-ml-base,modernbert-be --chunkers whole,fixed1500,fixed1500_title
uv run python run_sweep.py --corpus A --models e5-large,solon-large,arctic-l-v2,jina-v3,nomic-v2-moe,bilingual-large,qwen3-0.6b --chunkers whole
uv run python run_sweep.py --corpus B --models e5-small,potion-ml-128m,static-sim-ml --chunkers article_ctx
uv run python run_sweep.py --corpus B --models e5-small --chunkers article_ctx --clean
uv run python run_sweep.py --corpus B --models e5-base,modernbert-be --chunkers article_ctx
uv run python run_sweep.py --corpus B --models e5-base --chunkers article_ctx --clean
echo CHAIN_DONE
