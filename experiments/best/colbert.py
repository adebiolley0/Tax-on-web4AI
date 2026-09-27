#!/usr/bin/env python3
"""French ColBERT leg (antoinelouis/colbertv1-camembert-base-mmarcoFR through PyLate; exp 12 / 22).

* :class:`ColbertIndex` – the fp16 token matrix of every chunk (B: 10,869 chunks, ≈ 3 M tokens × 128 d = 0.6 GB)
  persisted under ``index/B_colbert/`` (``build`` encodes the corpus: 38 min on 4 cores, torch lock);
* query encoding with the exp-12 set-up (``<unk>`` markers, 48-token query window — 256 collapses on short
  questions, exp 22) and exact brute-force MaxSim over all chunks (0.7 s / query on CPU);
* :class:`ColbertScoreCache` – (question text → chunk-score row) cache so the stored question sets need no PyLate
  process (``cache/B_colbert_scores.npz``).

Needs the PyLate venv for anything that is not cached (``../12_sparse_colbert/.venv`` until ``uv sync`` here).
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import numpy as np

from config import CACHE, COLBERT_ID, COLBERT_QUERY_LENGTH, INDEX, qkey
from corpus import Universe
from fusion import doc_max

COLBERT_KW = dict(query_prefix="<unk>", document_prefix="<unk>", query_length=COLBERT_QUERY_LENGTH, document_length=512)
# The Stanford checkpoint was trained with colbert-ai on a CamemBERT tokenizer whose vocabulary has no '[unused0]' /
# '[unused1]' markers: colbert-ai mapped both to <unk>. PyLate would instead add the tokens and mis-size the
# embedding matrix, so the training set-up is reproduced explicitly with "<unk>" prefixes (exp 12).


def load_model(threads: int = 4):
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    import torch
    from pylate import models
    torch.set_num_threads(threads)
    t0 = time.perf_counter()
    m = models.ColBERT(model_name_or_path=COLBERT_ID, device="cpu", **COLBERT_KW)
    return m, time.perf_counter() - t0


def encode(m, texts, is_query: bool, bs: int = 8, verbose: bool = False) -> list[np.ndarray]:
    out = []
    t0 = time.perf_counter()
    for i in range(0, len(texts), 512):
        embs = m.encode(texts[i:i + 512], batch_size=bs, is_query=is_query, show_progress_bar=False, convert_to_numpy=True)
        out.extend(np.asarray(e, dtype=np.float16) for e in embs)
        if verbose and not is_query and len(texts) > 512:
            print(f"  encoded {len(out)}/{len(texts)} ({time.perf_counter() - t0:.0f}s)", flush=True)
    return out


def _pad_stack(embs, torch):
    n, d = len(embs), embs[0].shape[1]
    lmax = max(e.shape[0] for e in embs)
    out = torch.zeros((n, lmax, d), dtype=torch.float32)
    mask = torch.zeros((n, lmax), dtype=torch.bool)
    for i, e in enumerate(embs):
        out[i, : e.shape[0]] = torch.as_tensor(np.asarray(e, dtype=np.float32))
        mask[i, : e.shape[0]] = True
    return out, mask


def maxsim(q_embs: list[np.ndarray], d_embs: list[np.ndarray], doc_batch: int = 128) -> np.ndarray:
    """(nq, n_docs) MaxSim: Σ over query tokens of max over doc tokens of q·d (padding masked)."""
    import torch
    Q, qmask = _pad_stack(q_embs, torch)
    nq, n = Q.shape[0], len(d_embs)
    out = torch.zeros((nq, n), dtype=torch.float32)
    with torch.inference_mode():
        for s in range(0, n, doc_batch):
            Db, mb = _pad_stack(d_embs[s:s + doc_batch], torch)
            sim = torch.einsum("qid,bjd->qbij", Q, Db)
            sim = sim.masked_fill(~mb[None, :, None, :], -1e4)
            best = sim.amax(dim=-1) * qmask[:, None, :]
            out[:, s:s + doc_batch] = best.sum(-1)
    return out.numpy()


class ColbertIndex:
    """Persisted token matrix of a chunk universe + query scoring."""

    def __init__(self, folder: Path, uni: Universe, threads: int = 4):
        self.folder, self.uni, self.threads = Path(folder), uni, threads
        meta = json.loads((self.folder / "meta.json").read_text())
        assert meta["n_chunks"] == uni.n_chunks, f"ColBERT index has {meta['n_chunks']} chunks, universe {uni.n_chunks}"
        self.meta = meta
        toks = np.load(self.folder / "tokens.npy", mmap_mode="r")
        lens = np.load(self.folder / "lengths.npy")
        off = np.concatenate([[0], np.cumsum(lens)])
        self.d_embs = [toks[off[i]:off[i + 1]] for i in range(uni.n_chunks)]      # fp16 memmap views
        self._m = None

    @staticmethod
    def path(corpus: str) -> Path:
        return INDEX / f"{corpus}_colbert"

    @classmethod
    def build(cls, uni: Universe, folder: Path | None = None, bs: int = 8, threads: int = 4) -> "ColbertIndex":
        folder = Path(folder or cls.path(uni.corpus))
        folder.mkdir(parents=True, exist_ok=True)
        m, load_s = load_model(threads)
        t0 = time.perf_counter()
        d_embs = encode(m, uni.texts, False, bs, verbose=True)
        enc_s = time.perf_counter() - t0
        np.save(folder / "tokens.npy", np.concatenate(d_embs, axis=0).astype(np.float16))
        np.save(folder / "lengths.npy", np.array([e.shape[0] for e in d_embs], dtype=np.int32))
        (folder / "meta.json").write_text(json.dumps({"model": COLBERT_ID, "n_chunks": uni.n_chunks, "fingerprint": uni.fingerprint(),
                                                       "n_tokens": int(sum(e.shape[0] for e in d_embs)), "encode_s": round(enc_s, 1),
                                                       "model_load_s": round(load_s, 1), **{k: v for k, v in COLBERT_KW.items()}}))
        print(f"  colbert index {folder}: {uni.n_chunks} chunks encoded in {enc_s:.0f}s", flush=True)
        return cls(folder, uni, threads)

    def encode_queries(self, questions: list[str]) -> list[np.ndarray]:
        if self._m is None:
            self._m, _ = load_model(self.threads)
        return encode(self._m, questions, True, 16)

    def scores(self, questions: list[str], qblock: int = 32) -> np.ndarray:
        """(nq, n_chunks) MaxSim scores, brute force."""
        q_embs = self.encode_queries(questions)
        out = np.zeros((len(questions), self.uni.n_chunks), dtype=np.float32)
        for s in range(0, len(questions), qblock):
            out[s:s + qblock] = maxsim(q_embs[s:s + qblock], self.d_embs)
        return out


class ColbertScoreCache:
    """question text → chunk-score row (float32, n_chunks), with the universe fingerprint checked on load."""

    def __init__(self, uni: Universe, path: Path | None = None):
        self.uni = uni
        self.path = Path(path or CACHE / f"{uni.corpus}_colbert_scores.npz")
        self.rows: dict[str, np.ndarray] = {}
        self.fp = uni.fingerprint()
        if self.path.exists():
            z = np.load(self.path, allow_pickle=False)
            assert str(z["fingerprint"]) == self.fp and z["scores"].shape[1] == uni.n_chunks, f"{self.path}: chunk universe differs"
            self.rows = {str(k): v for k, v in zip(z["keys"], z["scores"])}
        self._dirty = False

    def get(self, question: str) -> np.ndarray | None:
        return self.rows.get(qkey(question))

    def put(self, question: str, row: np.ndarray) -> None:
        self.rows[qkey(question)] = np.asarray(row, dtype=np.float32)
        self._dirty = True

    def save(self) -> None:
        if not self._dirty:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        keys = sorted(self.rows)
        np.savez(self.path, keys=np.array(keys, dtype="U40"), scores=np.stack([self.rows[k] for k in keys]),
                 fingerprint=np.array(self.fp), model=np.array(COLBERT_ID), query_length=np.array(COLBERT_QUERY_LENGTH))
        self._dirty = False


class ColbertLeg:
    def __init__(self, uni: Universe, cache_only: bool = False, threads: int = 4):
        self.uni, self.cache_only, self.threads = uni, cache_only, threads
        self.cache = ColbertScoreCache(uni)
        self._index: ColbertIndex | None = None

    @property
    def index(self) -> ColbertIndex:
        if self._index is None:
            self._index = ColbertIndex(ColbertIndex.path(self.uni.corpus), self.uni, self.threads)
        return self._index

    def chunk_scores(self, question: str) -> np.ndarray:
        row = self.cache.get(question)
        if row is None:
            if self.cache_only:
                raise KeyError(f"ColBERT scores not cached for: {question[:60]}…")
            row = self.index.scores([question])[0]
            self.cache.put(question, row)
            self.cache.save()
        return row

    def doc_scores(self, chunk_scores: np.ndarray) -> np.ndarray:
        return doc_max(chunk_scores, self.uni.chunk_doc, self.uni.n_docs, fill=-1e4)


if __name__ == "__main__":       # score a question set into the cache: flock ../.torch.lock env OMP_NUM_THREADS=4 python colbert.py --corpus B --sets human,mined
    import argparse
    from corpus import universe_b
    from rag_eval import load_questions_b, load_questions_mined
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="B", choices=["B"])
    ap.add_argument("--sets", default="human,mined")
    ap.add_argument("--build", action="store_true", help="encode the corpus first if index/B_colbert is missing")
    a = ap.parse_args()
    uni = universe_b()
    if a.build and not (ColbertIndex.path("B") / "meta.json").exists():
        ColbertIndex.build(uni)
    leg = ColbertLeg(uni)
    qs = []
    if "human" in a.sets:
        qs += load_questions_b()
    if "mined" in a.sets:
        qs += load_questions_mined("B")
    todo = [q.question for q in qs if leg.cache.get(q.question) is None]
    print(f"{len(qs)} questions, {len(todo)} to score", flush=True)
    if todo:
        t0 = time.perf_counter()
        sc = leg.index.scores(todo)
        for q, row in zip(todo, sc):
            leg.cache.put(q, row)
        leg.cache.save()
        print(f"scored in {time.perf_counter() - t0:.0f}s ({(time.perf_counter() - t0) / len(todo):.2f} s/query incl. query encoding)")
