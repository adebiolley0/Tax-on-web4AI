"""Evaluate the saved fine-tuned cross-encoder (training finished, evaluation was cut off)."""
import sys
from sentence_transformers import CrossEncoder
from finetune_ce import evaluate
path = sys.argv[1] if len(sys.argv) > 1 else "models/mmarco-mMiniLMv2-L12-H384-v1-ft"
evaluate(CrossEncoder(path, max_length=512, device="cpu"), "mmarco-mMiniLMv2-L12-H384-v1-ft-e2", ("A", "B", "C"))
