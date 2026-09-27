#!/usr/bin/env python3
"""Moved to the harness: ``rag_eval.mining`` (experiments/common/rag_eval/mining.py, with the reference
grammar in ``rag_eval/legal_refs.py``).  This shim keeps the old invocation working::

    cd experiments/13_lexical_upgrades && uv run python ../18_eval_hygiene/mining/mine_questions.py --report-dir ../18_eval_hygiene/mining
    cd experiments/common && uv run python -m rag_eval.mining --check        # byte-compare a rebuild with experiments/data
"""
import sys

from rag_eval.mining import main

if __name__ == "__main__":
    sys.exit(main())
