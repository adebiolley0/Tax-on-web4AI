"""Cross-encoder rerankers with a (question text, chunk index) score cache.

* mMARCO-MiniLM-L12 (``MMARCO_ID``): corpus B, short questions only (exp 22 gate); ≈ 0.11 s / pair on 4 cores.
* bge-reranker-v2-m3 (``BGE_ID``): corpus C (exp 17); ≈ 1 s / pair on 4 cores, reranker score only.
Both at max_length 512 (exp 17: same quality as 1024, −20 % time). Caches live in ``cache/<corpus>_<name>.npz`` and
carry the chunk-universe fingerprint; ``cache_only=True`` raises instead of loading a model (evaluation mode).
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import numpy as np

from budget import NO_DEADLINE, Deadline
from config import BGE_ID, CACHE, LIVE_BATCH, MMARCO_ID, RERANK_MAX_LENGTH, qkey
from corpus import Universe

MODELS = {"mmarco": MMARCO_ID, "bge": BGE_ID}
BATCH = {"mmarco": 16, "bge": 8}


class ScoreCache:
    """(question key, chunk index) → score; npz with a side-car json (model, max_length, fingerprint)."""

    def __init__(self, path: Path, model: str, uni: Universe):
        self.path = Path(path)
        self.meta = {"model": model, "max_length": RERANK_MAX_LENGTH, "corpus": uni.corpus, "n_chunks": uni.n_chunks, "fingerprint": uni.fingerprint()}
        self.table: dict[tuple[str, int], float] = {}
        if self.path.exists():
            side = self.path.with_suffix(".json")
            if side.exists():
                m = json.loads(side.read_text())
                assert m.get("fingerprint") == self.meta["fingerprint"] and m.get("model") == model, f"{self.path}: model / chunk universe differ"
            z = np.load(self.path, allow_pickle=False)
            self.table = {(str(q), int(c)): float(s) for q, c, s in zip(z["qkey"], z["chunk_idx"], z["score"])}
        self._dirty = False

    def get(self, question: str, chunk_idx: int) -> float | None:
        return self.table.get((qkey(question), int(chunk_idx)))

    def put(self, question: str, chunk_idx: int, score: float) -> None:
        self.table[(qkey(question), int(chunk_idx))] = float(score)
        self._dirty = True

    def save(self) -> None:
        if not self._dirty:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        keys = sorted(self.table)
        np.savez(self.path, qkey=np.array([k[0] for k in keys], dtype="U40"), chunk_idx=np.array([k[1] for k in keys], dtype=np.int64),
                 score=np.array([self.table[k] for k in keys], dtype=np.float32))
        self.path.with_suffix(".json").write_text(json.dumps({**self.meta, "n_pairs": len(keys)}, indent=1))
        self._dirty = False


class Reranker:
    def __init__(self, name: str, uni: Universe, cache_only: bool = False, threads: int = 4, use_cache: bool = True):
        assert name in MODELS
        self.name, self.uni, self.cache_only, self.threads, self.use_cache = name, uni, cache_only, threads, use_cache
        self.model_id = MODELS[name]
        self.cache = ScoreCache(CACHE / f"{uni.corpus}_{name}.npz", self.model_id, uni)
        self._ce = None
        self.last_scored = 0

    def _model(self):
        if self._ce is None:
            os.environ.setdefault("HF_HUB_OFFLINE", "1")
            os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
            import torch
            from sentence_transformers import CrossEncoder
            torch.set_num_threads(self.threads)
            t0 = time.perf_counter()
            self._ce = CrossEncoder(self.model_id, max_length=RERANK_MAX_LENGTH, device="cpu")
            self.load_s = time.perf_counter() - t0
        return self._ce

    def warm(self) -> None:
        """Load the model and run one pair (untimed start-up cost of a live process)."""
        self._model().predict([("échauffement", self.uni.chunks[0].text)], show_progress_bar=False)

    def score(self, question: str, chunk_idx: list[int], deadline: Deadline = NO_DEADLINE) -> np.ndarray:
        """Scores of (question, chunk) pairs in the order given; cache first (unless ``use_cache`` is off), model for
        the rest. Under an active deadline the pairs go in LIVE_BATCH mini-batches with a rate check after each."""
        out = np.zeros(len(chunk_idx), dtype=np.float32)
        todo = []
        for j, c in enumerate(chunk_idx):
            s = self.cache.get(question, c) if self.use_cache else None
            if s is None:
                todo.append((j, int(c)))
            else:
                out[j] = s
        if todo:
            if self.cache_only:
                raise KeyError(f"{self.name}: {len(todo)} pairs not cached for: {question[:60]}…")
            order = sorted(todo, key=lambda jc: len(self.uni.chunks[jc[1]].text))
            pairs = [(question, self.uni.chunks[c].text) for _, c in order]
            m, stage = self._model(), f"{self.name} ({len(pairs)} pairs)"
            if deadline.active:
                bs, t0, parts = LIVE_BATCH[self.name], time.perf_counter(), []
                for i in range(0, len(pairs), bs):
                    parts.append(m.predict(pairs[i:i + bs], batch_size=bs, show_progress_bar=False))
                    deadline.check_rate(stage, min(i + bs, len(pairs)), len(pairs), t0)
                sc = np.concatenate([np.atleast_1d(np.asarray(p, dtype=np.float32)) for p in parts])
            else:
                sc = np.asarray(m.predict(pairs, batch_size=BATCH[self.name], show_progress_bar=False), dtype=np.float32)
            for (j, c), s in zip(order, sc):
                out[j] = s
                if self.use_cache:
                    self.cache.put(question, c, float(s))
            self.last_scored += len(todo)
            if self.use_cache:
                self.cache.save()
        return out
