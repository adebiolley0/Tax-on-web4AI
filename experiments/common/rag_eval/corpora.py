"""Corpus and question loaders.

Three corpora are used throughout the experiments (paths below, relative to the repo root):

* **Corpus A** – the 91 Fisconet+ markdown documents in ``ingestion/validation_dataset/md``
  (circulaires, FAQs, rulings, PQs, code excerpts) with the 31 questions of ``questions.json``
  (29 scored: Q13 and Q15 are flagged ``skip``).  Ground truth is at document level.
* **Corpus B** – the article-level corpus parsed from the MyMinfin library PDFs by
  ``experiments/00_pdf_parsing`` (``experiments/data/corpus_b/articles.jsonl``): each *article* is a
  document.  40 human questions (``questions_b.json``) + 304 mined ones (``questions_b_mined.json``).
* **Corpus C** – the 21k Fisconet+ markdown documents in ``myfin_docs/`` (``folder/stem`` ids).
  64 human questions (``questions_c.json``) + 697 mined ones (``questions_c_mined.json``).

Question-file schema (one JSON list per file):

* human sets: ``id``, ``question``, ``expected`` (primary doc ids), ``secondary`` (graded 0.5 in nDCG),
  ``topic``, free-text ``notes``; corpus A uses ``expected_docs`` / ``secondary_docs`` / ``skip``.
* mined sets (:mod:`rag_eval.mining`): the same keys plus ``source`` (``pq`` | ``faq`` | ``ruling``),
  ``source_doc``, ``exclude`` (doc ids removed from a ranking before scoring — the PQ the question was
  copied from), ``label_basis`` (``explicit`` | ``bare`` | ``document``), ``date`` and ``split``
  (informative only: the split is always recomputed from the id, see :func:`question_split`).

Every loader returns :class:`Question` objects; anything beyond ``expected`` / ``secondary`` lands in
``Question.meta`` and :attr:`Question.exclude` reads ``meta["exclude"]``.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPO_ROOT / "experiments" / "data"
CORPUS_A_MD = REPO_ROOT / "ingestion" / "validation_dataset" / "md"
CORPUS_A_MANIFEST = REPO_ROOT / "ingestion" / "validation_dataset" / "manifest.json"
QUESTIONS_A = REPO_ROOT / "ingestion" / "validation_dataset" / "questions.json"
CORPUS_B_JSONL = DATA_DIR / "corpus_b" / "articles.jsonl"
QUESTIONS_B = DATA_DIR / "corpus_b" / "questions_b.json"
QUESTIONS_B_MINED = DATA_DIR / "corpus_b" / "questions_b_mined.json"
CORPUS_C_DIR = REPO_ROOT / "myfin_docs"
QUESTIONS_C = DATA_DIR / "corpus_c" / "questions_c.json"
QUESTIONS_C_MINED = DATA_DIR / "corpus_c" / "questions_c_mined.json"

QUESTION_FILES: dict[str, Path] = {"A": QUESTIONS_A, "B": QUESTIONS_B, "C": QUESTIONS_C}
QUESTION_FILES_MINED: dict[str, Path] = {"B": QUESTIONS_B_MINED, "C": QUESTIONS_C_MINED}
MINED_ID_PREFIX: dict[str, str] = {"B": "MB-", "C": "MC-"}      # mined ids are ``M<corpus>-<SOURCE>-<sha1[:8]>``
SOURCES = ("pq", "faq", "ruling")
LABEL_BASES = ("explicit", "bare", "document")


@dataclass
class Doc:
    doc_id: str
    title: str
    text: str
    meta: dict = field(default_factory=dict)


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    text: str
    title: str = ""
    meta: dict = field(default_factory=dict)


@dataclass
class Question:
    qid: str
    question: str
    expected: list[str]
    secondary: list[str] = field(default_factory=list)
    meta: dict = field(default_factory=dict)

    @property
    def split(self) -> str:
        """``"train"`` or ``"val"`` (50/50, deterministic from the id, see :func:`question_split`).
        Tune anything (fusion weights, k1/b, rerank depth, LTR models, fine-tuning) on ``train``
        only; report on ``val``."""
        return question_split(self.qid)

    @property
    def exclude(self) -> list[str]:
        """Doc ids that :func:`rag_eval.metrics.evaluate_rankings` drops from the ranking before
        scoring (empty for human questions)."""
        return list(self.meta.get("exclude") or [])

    @property
    def is_mined(self) -> bool:
        return is_mined_qid(self.qid)


# ── split protocol ───────────────────────────────────────────────────────────
def question_split(qid: str) -> str:
    """md5 parity of the question id: even → ``train``, odd → ``val``.  Independent of the question
    text and of the file order, so a set can be edited or regenerated without moving questions."""
    h = int(hashlib.md5(qid.encode()).hexdigest(), 16)
    return "train" if h % 2 == 0 else "val"


def filter_split(questions: list[Question], split: str | None) -> list[Question]:
    """Subset for ``"train"`` / ``"val"``; ``None`` or ``"all"`` returns a copy of the whole list."""
    if split in (None, "all"):
        return list(questions)
    if split not in ("train", "val"):
        raise ValueError(f"split must be 'train', 'val', 'all' or None, got {split!r}")
    return [q for q in questions if q.split == split]


def is_mined_qid(qid: str) -> bool:
    return any(qid.startswith(p) for p in MINED_ID_PREFIX.values())


def slice_questions(questions: list[Question]) -> dict[str, list[Question]]:
    """Named slices of a human ∪ mined question list, as reported by the round-3 experiments:
    ``human``, ``mined``, ``mined__src_<pq|faq|ruling>``, ``mined__basis_<explicit|bare|document>``.
    Empty slices are omitted."""
    human = [q for q in questions if not q.is_mined]
    mined = [q for q in questions if q.is_mined]
    out: dict[str, list[Question]] = {"human": human, "mined": mined}
    for src in SOURCES:
        out[f"mined__src_{src}"] = [q for q in mined if q.meta.get("source") == src]
    for basis in LABEL_BASES:
        out[f"mined__basis_{basis}"] = [q for q in mined if q.meta.get("label_basis") == basis]
    return {k: v for k, v in out.items() if v}


# ── corpus A ─────────────────────────────────────────────────────────────────
def load_corpus_a(clean: bool = False) -> list[Doc]:
    """The 91 validation markdown docs.  ``clean=True`` applies the repo's content cleaner
    (requires ``tax_ingestion`` importable)."""
    manifest = {m["short_name"]: m for m in json.loads(CORPUS_A_MANIFEST.read_text())}
    docs: list[Doc] = []
    for p in sorted(CORPUS_A_MD.glob("*.md")):
        text = p.read_text(encoding="utf-8")
        if clean:
            from tax_ingestion.storage.content_cleaner import clean_for_indexing  # type: ignore
            text = clean_for_indexing(text)
        m = manifest.get(p.stem, {})
        docs.append(Doc(doc_id=p.stem, title=m.get("title", p.stem), text=text,
                        meta={k: m.get(k) for k in ("document_type", "document_date", "taxonomies", "keywords")}))
    return docs


def load_questions_a(include_skipped: bool = False) -> list[Question]:
    """Questions flagged ``skip: true`` (Q13, Q15: invalid ground truth, see EXPERIMENTS.md §3.0)
    are excluded unless ``include_skipped``."""
    qs = json.loads(QUESTIONS_A.read_text())
    return [Question(q["id"], q["question"], q["expected_docs"], q.get("secondary_docs", []),
                     {"topic": q.get("topic"), "keywords": q.get("expected_keywords", [])})
            for q in qs if include_skipped or not q.get("skip")]


# ── corpus B ─────────────────────────────────────────────────────────────────
def load_corpus_b(codes: list[str] | None = None) -> list[Doc]:
    """The article-level PDF corpus.  ``codes`` restricts to code identifiers (e.g. ``["cir92"]``)."""
    if not CORPUS_B_JSONL.exists():
        raise FileNotFoundError(f"{CORPUS_B_JSONL} missing – run experiments/00_pdf_parsing first")
    docs: list[Doc] = []
    with CORPUS_B_JSONL.open(encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            if codes and r["code"] not in codes:
                continue
            docs.append(Doc(doc_id=r["id"], title=r["title"], text=r["text"],
                            meta={k: r.get(k) for k in ("code", "article", "heading_path", "source_file", "page")}))
    return docs


def load_questions_b(variant: str | None = None) -> list[Question]:
    """``variant=None``: the 40 human questions; ``"mined"``: :func:`load_questions_mined` ``("B")``."""
    if variant == "mined":
        return load_questions_mined("B")
    if variant is not None:
        raise ValueError(f"variant must be None or 'mined', got {variant!r}")
    qs = json.loads(QUESTIONS_B.read_text())
    return [Question(q["id"], q["question"], q["expected"], q.get("secondary", []),
                     {"topic": q.get("topic"), "notes": q.get("notes")}) for q in qs]


# ── corpus C ─────────────────────────────────────────────────────────────────
_FM_RE = re.compile(r"^---\n(.*?)\n---\n", re.S)


def parse_front_matter(text: str) -> tuple[dict, str]:
    """Split a ``myfin_docs`` markdown file into (front-matter dict, body).  Values are strings, or
    lists for ``["a", "b"]`` fields such as ``path``; files without front matter give ``({}, text)``."""
    m = _FM_RE.match(text)
    if not m:
        return {}, text
    meta: dict = {}
    for line in m.group(1).split("\n"):
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        v = v.strip()
        if v.startswith("[") and v.endswith("]"):
            meta[k.strip()] = [x.strip().strip('"') for x in v[1:-1].split('", "') if x.strip()] if v != "[]" else []
        else:
            meta[k.strip()] = v.strip('"')
    return meta, text[m.end():]


_parse_front_matter = parse_front_matter      # pre-0.3 name, still imported by some experiments


def load_corpus_c(doc_types: list[str] | None = None, max_chars: int | None = None,
                  limit: int | None = None) -> list[Doc]:
    """Load ``myfin_docs``.  ``doc_types`` restricts to folder names; ``max_chars`` truncates very
    long documents (p99 ≈ 118k chars, max 3 MB); ``limit`` stops after that many docs."""
    docs: list[Doc] = []
    for folder in sorted(p for p in CORPUS_C_DIR.iterdir() if p.is_dir()):
        if doc_types and folder.name not in doc_types:
            continue
        for p in sorted(folder.glob("*.md")):
            meta, body = parse_front_matter(p.read_text(encoding="utf-8", errors="replace"))
            body = body.strip()
            if body.startswith("# "):                      # drop the duplicated H1 title line
                body = body.split("\n", 1)[1] if "\n" in body else ""
            if max_chars:
                body = body[:max_chars]
            docs.append(Doc(doc_id=f"{folder.name}/{p.stem}", title=meta.get("title", p.stem), text=body,
                            meta={"document_type": meta.get("document_type", folder.name),
                                  "document_date": meta.get("document_date"), "path": meta.get("path", []),
                                  "guid": meta.get("guid"), "folder": folder.name}))
            if limit and len(docs) >= limit:
                return docs
    return docs


def load_questions_c(variant: str | None = None) -> list[Question]:
    """``variant=None``: the 64 human questions; ``"mined"``: :func:`load_questions_mined` ``("C")``."""
    if variant == "mined":
        return load_questions_mined("C")
    if variant is not None:
        raise ValueError(f"variant must be None or 'mined', got {variant!r}")
    qs = json.loads(QUESTIONS_C.read_text())
    return [Question(q["id"], q["question"], q["expected"], q.get("secondary", []),
                     {"topic": q.get("topic"), "difficulty": q.get("difficulty"), "doc_type": q.get("doc_type")})
            for q in qs]


# ── mined sets and generic entry points ──────────────────────────────────────
def load_questions_mined(corpus: str, path: Path | None = None) -> list[Question]:
    """The regex-mined sets (``questions_<b|c>_mined.json``, regenerated by ``python -m rag_eval.mining``).
    ``meta`` carries ``topic``, ``source``, ``source_doc``, ``exclude``, ``label_basis``, ``date``, ``notes``."""
    path = path or QUESTION_FILES_MINED[corpus]
    qs = json.loads(Path(path).read_text())
    return [Question(q["id"], q["question"], q["expected"], q.get("secondary", []),
                     {"topic": q.get("topic"), "source": q.get("source"), "source_doc": q.get("source_doc"),
                      "exclude": q.get("exclude", []), "label_basis": q.get("label_basis"), "date": q.get("date"),
                      "notes": q.get("notes")}) for q in qs]


def load_questions(corpus: str, variant: str | None = None) -> list[Question]:
    """``variant``: ``None`` (human set), ``"mined"`` or ``"all"`` (human first, then mined)."""
    human = {"A": load_questions_a, "B": load_questions_b, "C": load_questions_c}[corpus]
    if variant is None:
        return human()
    if variant == "mined":
        return load_questions_mined(corpus)
    if variant == "all":
        return human() + load_questions_mined(corpus)
    raise ValueError(f"variant must be None, 'mined' or 'all', got {variant!r}")


def load_corpus(name: str, **kw) -> tuple[list[Doc], list[Question]]:
    """(docs, human questions) of corpus ``"A"`` / ``"B"`` / ``"C"``; ``kw`` go to the corpus loader."""
    if name == "A":
        return load_corpus_a(**kw), load_questions_a()
    if name == "B":
        return load_corpus_b(**kw), load_questions_b()
    if name == "C":
        return load_corpus_c(**kw), load_questions_c()
    raise ValueError(name)
