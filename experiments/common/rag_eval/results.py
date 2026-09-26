"""Persist experiment results: one JSON per run + a shared leaderboard JSONL.

Every saved run carries a *provenance stamp* (``result.provenance`` in the JSON, ``prov``
in the leaderboard row): short git commit (+ dirty flag), UTC time, hostname, harness
version, the SHA-256 of the question-set file and of the sorted question ids actually
scored, and a corpus fingerprint (number of documents + SHA-256 of the sorted doc ids).
Rows written before this field existed simply lack it; nothing is rewritten.
"""
from __future__ import annotations

import functools
import hashlib
import json
import os
import platform
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from rag_eval.corpora import (REPO_ROOT, CORPUS_A_MD, CORPUS_B_JSONL, CORPUS_C_DIR, QUESTIONS_A, QUESTIONS_B,
                              QUESTIONS_C)
from rag_eval.metrics import RunResult

RESULTS_DIR = REPO_ROOT / "experiments" / "results"
LEADERBOARD = RESULTS_DIR / "leaderboard.jsonl"

_QUESTION_FILES = {"A": QUESTIONS_A, "B": QUESTIONS_B, "C": QUESTIONS_C}


def safe_name(name: str) -> str:
    """Sanitised run name used in result file names (``<corpus>__<safe_name>.json``)."""
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in name)


# ── provenance helpers ──────────────────────────────────────────────────────
def _sha256_file(p: Path) -> str | None:
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()
    except OSError:
        return None


def _sha256_ids(ids) -> str:
    h = hashlib.sha256()
    for i in sorted(ids):
        h.update(str(i).encode("utf-8"))
        h.update(b"\n")
    return h.hexdigest()


def git_commit() -> tuple[str | None, bool | None]:
    """(short commit, dirty?) of the repo, or (None, None) when git is unavailable."""
    try:
        head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT, capture_output=True,
                              text=True, timeout=10)
        if head.returncode != 0:
            return None, None
        st = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=REPO_ROOT,
                            capture_output=True, text=True, timeout=30)
        dirty = bool(st.stdout.strip()) if st.returncode == 0 else None
        return head.stdout.strip(), dirty
    except (OSError, subprocess.SubprocessError):
        return None, None


def corpus_doc_ids(corpus: str) -> list[str] | None:
    """Doc ids of a corpus *source on disk* without reading the texts (A: md stems,
    B: article ids in ``articles.jsonl``, C: ``folder/stem`` of ``myfin_docs``)."""
    try:
        if corpus == "A":
            return [p.stem for p in CORPUS_A_MD.glob("*.md")]
        if corpus == "B":
            ids = []
            with CORPUS_B_JSONL.open(encoding="utf-8") as fh:
                for line in fh:
                    ids.append(json.loads(line)["id"])
            return ids
        if corpus == "C":
            return [f"{d.name}/{p.stem}" for d in CORPUS_C_DIR.iterdir() if d.is_dir() for p in d.glob("*.md")]
    except OSError:
        return None
    return None


@functools.lru_cache(maxsize=8)
def corpus_fingerprint(corpus: str) -> dict:
    """``{"n_docs", "ids_sha256"}`` of the corpus source on disk (cached per process).
    This fingerprints what is *available*, not the subset a run may have indexed; pass
    ``docs=`` to :func:`save_result` to fingerprint the exact documents used."""
    ids = corpus_doc_ids(corpus)
    if ids is None:
        return {"n_docs": None, "ids_sha256": None}
    return {"n_docs": len(ids), "ids_sha256": _sha256_ids(ids)}


def docs_fingerprint(docs) -> dict:
    """Fingerprint of an explicit list of docs / doc ids (``Doc`` objects or strings)."""
    ids = [getattr(d, "doc_id", d) for d in docs]
    return {"n_docs": len(ids), "ids_sha256": _sha256_ids(ids)}


def harness_version() -> str:
    try:
        from rag_eval import __version__
        return __version__
    except ImportError:
        return "unknown"


def build_provenance(result: RunResult, docs=None) -> dict:
    """Assemble the provenance stamp for a run (cheap: git + file hashes + id listing)."""
    commit, dirty = git_commit()
    qfile = _QUESTION_FILES.get(result.corpus)
    fp = docs_fingerprint(docs) if docs is not None else corpus_fingerprint(result.corpus)
    return {
        "git": commit,
        "git_dirty": dirty,
        "utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "host": socket.gethostname(),
        "harness": harness_version(),
        "python": platform.python_version(),
        "questions_file": str(qfile.relative_to(REPO_ROOT)) if qfile else None,
        "questions_sha256": _sha256_file(qfile) if qfile else None,
        "qids_sha256": _sha256_ids(result.per_question.keys()),
        "n_qids": len(result.per_question),
        "corpus_n_docs": fp["n_docs"],
        "corpus_ids_sha256": fp["ids_sha256"],
        "corpus_fingerprint_source": "docs" if docs is not None else "disk",
        "omp_threads": os.environ.get("OMP_NUM_THREADS"),
        "argv": " ".join(sys.argv)[:500],
    }


# ── saving ──────────────────────────────────────────────────────────────────
def save_result(experiment: str, result: RunResult, docs=None) -> Path:
    """Write ``results/<experiment>/<corpus>__<run>.json`` and append a leaderboard row.
    ``docs`` (optional list of ``Doc`` or ids) fingerprints the exact documents indexed;
    otherwise the corpus source on disk is fingerprinted."""
    if not getattr(result, "provenance", None):
        result.provenance = build_provenance(result, docs)
    d = RESULTS_DIR / experiment
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{result.corpus}__{safe_name(result.name)}.json"
    p.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=1))
    append_leaderboard(experiment, result)
    return p


def append_leaderboard(experiment: str, result: RunResult) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    row = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "experiment": experiment, "run": result.name,
           "corpus": result.corpus, **result.metrics, "timing": result.timing, "config": result.config}
    prov = getattr(result, "provenance", None)
    if prov:
        row["prov"] = prov
    with LEADERBOARD.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def print_leaderboard(corpus: str | None = None, top: int = 40) -> None:
    rows = [json.loads(l) for l in LEADERBOARD.read_text().splitlines() if l.strip()]
    if corpus:
        rows = [r for r in rows if r["corpus"] == corpus]
    # keep latest row per (experiment, run, corpus)
    latest: dict = {}
    for r in rows:
        latest[(r["experiment"], r["run"], r["corpus"])] = r
    rows = sorted(latest.values(), key=lambda r: -r["mrr"])[:top]
    print(f"{'corpus':6s} {'experiment':22s} {'run':52s} {'MRR':>6s} {'nDCG5':>6s} {'H@1':>6s} {'H@5':>6s} {'R@10':>6s} {'git':>8s}")
    for r in rows:
        git = (r.get("prov") or {}).get("git") or "-"
        print(f"{r['corpus']:6s} {r['experiment'][:22]:22s} {r['run'][:52]:52s} {r['mrr']:6.3f} {r['ndcg@5']:6.3f} "
              f"{r['hit@1']:6.3f} {r['hit@5']:6.3f} {r['recall@10']:6.3f} {git:>8s}")


if __name__ == "__main__":
    import sys as _sys
    print_leaderboard(_sys.argv[1] if len(_sys.argv) > 1 else None)
