"""Persist experiment results: one JSON per run + a shared leaderboard JSONL.

* ``experiments/results/<experiment>/<corpus>__<safe_name(run)>.json`` – the full
  :class:`~rag_eval.metrics.RunResult` (``name``, ``corpus``, ``config``, ``metrics``,
  ``per_question``, ``timing``, ``provenance``); the per-question ranks are what
  :mod:`rag_eval.stats` compares.
* ``experiments/results/leaderboard.jsonl`` – one appended row per save: ``ts``, ``experiment``,
  ``run``, ``corpus``, the flattened metrics, ``timing``, ``config`` and ``prov``.

**Provenance stamp** (``provenance`` in the JSON, ``prov`` in the row): short git commit + dirty flag,
UTC time, host, harness version, Python version, the question file(s) actually scored
(``questions_file`` / ``questions_sha256``; several files are joined with ``+`` when a run mixes the
human and the mined set — the file is inferred from the question ids, or passed as ``questions``), the
SHA-256 of the sorted question ids, and a corpus fingerprint (number of docs + SHA-256 of the sorted
doc ids: the source on disk, or the exact ``docs`` passed to :func:`save_result`).  Rows written
before the stamp existed simply lack it; nothing is ever rewritten.
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
from typing import Iterable

from rag_eval.corpora import (CORPUS_A_MD, CORPUS_B_JSONL, CORPUS_C_DIR, MINED_ID_PREFIX, QUESTION_FILES,
                              QUESTION_FILES_MINED, REPO_ROOT, Question, is_mined_qid)
from rag_eval.metrics import RunResult

RESULTS_DIR = REPO_ROOT / "experiments" / "results"
LEADERBOARD = RESULTS_DIR / "leaderboard.jsonl"


def safe_name(name: str) -> str:
    """Sanitised run name used in result file names (``<corpus>__<safe_name>.json``)."""
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in name)


def result_path(experiment: str, corpus: str, run: str) -> Path:
    return RESULTS_DIR / experiment / f"{corpus}__{safe_name(run)}.json"


# ── provenance ───────────────────────────────────────────────────────────────
def _sha256_file(p: Path) -> str | None:
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()
    except OSError:
        return None


def _sha256_ids(ids: Iterable) -> str:
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
    """Doc ids of a corpus *source on disk* without reading the texts (A: md stems, B: article ids
    in ``articles.jsonl``, C: ``folder/stem`` of ``myfin_docs``); ``None`` when unavailable."""
    try:
        if corpus == "A":
            return [p.stem for p in CORPUS_A_MD.glob("*.md")]
        if corpus == "B":
            with CORPUS_B_JSONL.open(encoding="utf-8") as fh:
                return [json.loads(line)["id"] for line in fh]
        if corpus == "C":
            return [f"{d.name}/{p.stem}" for d in CORPUS_C_DIR.iterdir() if d.is_dir() for p in d.glob("*.md")]
    except OSError:
        return None
    return None


@functools.lru_cache(maxsize=8)
def corpus_fingerprint(corpus: str) -> dict:
    """``{"n_docs", "ids_sha256"}`` of the corpus source on disk (cached per process).  This
    fingerprints what is *available*; pass ``docs=`` to :func:`save_result` for the exact subset."""
    ids = corpus_doc_ids(corpus)
    if ids is None:
        return {"n_docs": None, "ids_sha256": None}
    return {"n_docs": len(ids), "ids_sha256": _sha256_ids(ids)}


def docs_fingerprint(docs: Iterable) -> dict:
    """Fingerprint of an explicit list of docs (``Doc`` objects or doc-id strings)."""
    ids = [getattr(d, "doc_id", d) for d in docs]
    return {"n_docs": len(ids), "ids_sha256": _sha256_ids(ids)}


def question_files(corpus: str, qids: Iterable[str]) -> list[Path]:
    """The question file(s) the ids come from: the human file when any id is a human id, the mined
    file when any id is a mined one (``MB-`` / ``MC-`` prefix), both (human first) for a mixed set."""
    qids = list(qids)
    out: list[Path] = []
    if any(not is_mined_qid(q) for q in qids) and corpus in QUESTION_FILES:
        out.append(QUESTION_FILES[corpus])
    if any(q.startswith(MINED_ID_PREFIX.get(corpus, "\0")) for q in qids) and corpus in QUESTION_FILES_MINED:
        out.append(QUESTION_FILES_MINED[corpus])
    return out


def harness_version() -> str:
    from rag_eval import __version__
    return __version__


def build_provenance(result: RunResult, docs: Iterable | None = None,
                     questions: list[Question] | None = None) -> dict:
    """Assemble the provenance stamp for a run (cheap: git + file hashes + id listing).
    ``questions`` only serves to identify the question file(s); by default they are inferred from
    the scored ids."""
    commit, dirty = git_commit()
    qids = [q.qid for q in questions] if questions is not None else list(result.per_question)
    qfiles = question_files(result.corpus, qids)
    fp = docs_fingerprint(docs) if docs is not None else corpus_fingerprint(result.corpus)
    return {
        "git": commit,
        "git_dirty": dirty,
        "utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "host": socket.gethostname(),
        "harness": harness_version(),
        "python": platform.python_version(),
        "questions_file": "+".join(str(f.relative_to(REPO_ROOT)) for f in qfiles) or None,
        "questions_sha256": "+".join(_sha256_file(f) or "?" for f in qfiles) or None,
        "qids_sha256": _sha256_ids(result.per_question.keys()),
        "n_qids": len(result.per_question),
        "corpus_n_docs": fp["n_docs"],
        "corpus_ids_sha256": fp["ids_sha256"],
        "corpus_fingerprint_source": "docs" if docs is not None else "disk",
        "omp_threads": os.environ.get("OMP_NUM_THREADS"),
        "argv": " ".join(sys.argv)[:500],
    }


# ── saving / loading ─────────────────────────────────────────────────────────
def save_result(experiment: str, result: RunResult, docs: Iterable | None = None,
                questions: list[Question] | None = None, results_dir: Path | None = None) -> Path:
    """Write the run JSON and append a leaderboard row; returns the JSON path.  ``docs`` (``Doc``
    objects or ids) fingerprints the exact documents indexed, otherwise the corpus on disk is
    fingerprinted.  A stamp already present in ``result.provenance`` is kept.  ``results_dir``
    redirects both files (tests, scratch runs)."""
    if not result.provenance:
        result.provenance = build_provenance(result, docs, questions)
    root = Path(results_dir) if results_dir else RESULTS_DIR
    d = root / experiment
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{result.corpus}__{safe_name(result.name)}.json"
    p.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=1))
    append_leaderboard(experiment, result, root / LEADERBOARD.name)
    return p


def append_leaderboard(experiment: str, result: RunResult, path: Path = LEADERBOARD) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "experiment": experiment, "run": result.name,
           "corpus": result.corpus, **result.metrics, "timing": result.timing, "config": result.config}
    if result.provenance:
        row["prov"] = result.provenance
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_result(path: Path) -> RunResult:
    """Read a run JSON back into a :class:`RunResult`."""
    d = json.loads(Path(path).read_text())
    return RunResult(d["name"], d["corpus"], d.get("config", {}), d["metrics"], d["per_question"],
                     d.get("timing", {}), d.get("provenance", {}))


def read_leaderboard(corpus: str | None = None, path: Path = LEADERBOARD) -> list[dict]:
    """Latest row per (experiment, run, corpus), optionally for one corpus."""
    rows = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    if corpus:
        rows = [r for r in rows if r["corpus"] == corpus]
    latest: dict = {}
    for r in rows:
        latest[(r["experiment"], r["run"], r["corpus"])] = r
    return list(latest.values())


def print_leaderboard(corpus: str | None = None, top: int = 40, path: Path = LEADERBOARD) -> None:
    """Top runs by full-set MRR (latest row per run).  For the split protocol use :mod:`rag_eval.splits`."""
    rows = sorted(read_leaderboard(corpus, path), key=lambda r: -r["mrr"])[:top]
    print(f"{'corpus':6s} {'experiment':22s} {'run':52s} {'MRR':>6s} {'nDCG5':>6s} {'H@1':>6s} {'H@5':>6s} {'R@10':>6s} {'git':>8s}")
    for r in rows:
        git = (r.get("prov") or {}).get("git") or "-"
        print(f"{r['corpus']:6s} {r['experiment'][:22]:22s} {r['run'][:52]:52s} {r['mrr']:6.3f} {r['ndcg@5']:6.3f} "
              f"{r['hit@1']:6.3f} {r['hit@5']:6.3f} {r['recall@10']:6.3f} {git:>8s}")

