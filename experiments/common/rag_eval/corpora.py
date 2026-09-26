"""Corpus and question loaders.

Two corpora are used throughout the experiments:

* **Corpus A** – the 91 Fisconet+ markdown documents in
  ``ingestion/validation_dataset/md`` (circulaires, FAQs, rulings, PQs, code
  excerpts) with the 31 questions in ``questions.json``.  Ground truth is at
  document level.
* **Corpus B** – the article-level corpus parsed from the MyMinfin library PDFs
  (CIR 92, AR/CIR 92, Code TVA, regional codes …) by
  ``experiments/00_pdf_parsing``.  Each *article* is a "document"; ground truth
  is at article level (``experiments/data/corpus_b/questions_b.json``).
"""
from __future__ import annotations

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
        """Deterministic train/validation split (50/50) from a hash of the question id.
        Tune anything (fusion weights, k1/b, rerank depth, LTR models, fine-tuning) on
        ``train`` only; report on ``val``."""
        return question_split(self.qid)


def question_split(qid: str) -> str:
    import hashlib
    h = int(hashlib.md5(qid.encode()).hexdigest(), 16)
    return "train" if h % 2 == 0 else "val"


def filter_split(questions: list, split: str | None) -> list:
    if split in (None, "all"):
        return list(questions)
    return [q for q in questions if q.split == split]


def load_corpus_a(clean: bool = False) -> list[Doc]:
    """Load the 91 validation markdown docs. ``clean=True`` applies the repo's
    content cleaner (requires tax_ingestion importable)."""
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
    """Questions flagged ``skip: true`` in questions.json (Q13, Q15: invalid ground
    truth, see experiments/EXPERIMENTS.md) are excluded unless ``include_skipped``."""
    qs = json.loads(QUESTIONS_A.read_text())
    return [Question(q["id"], q["question"], q["expected_docs"], q.get("secondary_docs", []),
                     {"topic": q.get("topic"), "keywords": q.get("expected_keywords", [])})
            for q in qs if include_skipped or not q.get("skip")]


def load_corpus_b(codes: list[str] | None = None) -> list[Doc]:
    """Load the article-level PDF corpus. ``codes`` optionally restricts to a
    subset of code identifiers (e.g. ["cir92", "tva"])."""
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
    """``variant=None``: the 40 human questions. ``variant="mined"``: the regex-mined set of
    experiments/18_eval_hygiene/mining (questions_b_mined.json; meta carries source / source_doc /
    exclude / label_basis)."""
    if variant == "mined":
        return load_questions_mined("B")
    if variant is not None:
        raise ValueError(variant)
    qs = json.loads(QUESTIONS_B.read_text())
    return [Question(q["id"], q["question"], q["expected"], q.get("secondary", []),
                     {"topic": q.get("topic"), "notes": q.get("notes")}) for q in qs]


def load_questions_mined(corpus: str) -> list[Question]:
    """Mined question sets (experiments/18_eval_hygiene/mining/mine_questions.py). Same schema as the
    human sets plus ``source`` (pq | faq | ruling), ``source_doc``, ``exclude`` (documents removed from the
    ranking before scoring — the PQ a question was copied from) and ``label_basis``."""
    path = {"B": QUESTIONS_B_MINED, "C": QUESTIONS_C_MINED}[corpus]
    qs = json.loads(path.read_text())
    return [Question(q["id"], q["question"], q["expected"], q.get("secondary", []),
                     {"topic": q.get("topic"), "source": q.get("source"), "source_doc": q.get("source_doc"),
                      "exclude": q.get("exclude", []), "label_basis": q.get("label_basis"), "date": q.get("date"),
                      "notes": q.get("notes")}) for q in qs]


def load_corpus(name: str, **kw) -> tuple[list[Doc], list[Question]]:
    if name == "A":
        return load_corpus_a(**kw), load_questions_a()
    if name == "B":
        return load_corpus_b(**kw), load_questions_b()
    if name == "C":
        return load_corpus_c(**kw), load_questions_c()
    raise ValueError(name)


# ── Corpus C: myfin_docs (21k Fisconet+ markdown documents) ─────────────────
CORPUS_C_DIR = REPO_ROOT / "myfin_docs"
QUESTIONS_C = DATA_DIR / "corpus_c" / "questions_c.json"
QUESTIONS_C_MINED = DATA_DIR / "corpus_c" / "questions_c_mined.json"
_FM_RE = re.compile(r"^---\n(.*?)\n---\n", re.S)


def _parse_front_matter(text: str) -> tuple[dict, str]:
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


def load_corpus_c(doc_types: list[str] | None = None, max_chars: int | None = None,
                  limit: int | None = None) -> list[Doc]:
    """Load myfin_docs. ``doc_types`` restricts to folder names; ``max_chars``
    truncates very long documents (p99 ≈ 118k chars, max 3 MB)."""
    docs: list[Doc] = []
    folders = sorted(p for p in CORPUS_C_DIR.iterdir() if p.is_dir())
    for folder in folders:
        if doc_types and folder.name not in doc_types:
            continue
        for p in sorted(folder.glob("*.md")):
            raw = p.read_text(encoding="utf-8", errors="replace")
            meta, body = _parse_front_matter(raw)
            body = body.strip()
            # drop the duplicated H1 title line
            if body.startswith("# "):
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
    """``variant=None``: the 64 human questions; ``variant="mined"``: see :func:`load_questions_mined`."""
    if variant == "mined":
        return load_questions_mined("C")
    if variant is not None:
        raise ValueError(variant)
    qs = json.loads(QUESTIONS_C.read_text())
    return [Question(q["id"], q["question"], q["expected"], q.get("secondary", []),
                     {"topic": q.get("topic"), "difficulty": q.get("difficulty"), "doc_type": q.get("doc_type")})
            for q in qs]
