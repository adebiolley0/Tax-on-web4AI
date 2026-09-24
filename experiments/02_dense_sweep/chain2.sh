#!/bin/bash
# Follow-up to chain.sh: token-safe chunking on corpus B (experiment-05 finding: 26 % of
# article_ctx chunks exceed 512 e5 tokens).
cd "$(dirname "$0")"
until grep -q "CHAIN_DONE" chain.log; do sleep 60; done
uv run python run_sweep.py --corpus B --models e5-small --chunkers article_ctx_1200
uv run python run_sweep.py --corpus B --models e5-small --chunkers article_ctx_1200 --clean
uv run python run_sweep.py --corpus B --models e5-base --chunkers article_ctx_1200 --clean
echo CHAIN2_DONE
