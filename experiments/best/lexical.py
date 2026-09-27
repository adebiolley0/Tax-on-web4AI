"""Lexical stage: the exp-13 tokenizer, BM25F over fields, cue tokens and a persistent :class:`LexicalIndex`.

* :class:`Tokenizer` – exp-01 French normalisation (Snowball stem, bm25s French stoplist + question-word list, accent
  folding) with the exp-13 thousand-group number normalisation (``"50.000 euros" → "50000 euros"``).
* :class:`TokenStore` / :class:`FieldIndex` / :func:`bm25f_matrix` – sparse per-field term-frequency matrices sharing
  one vocabulary, Lucene IDF on unit frequency over all fields, BM25F with per-field length normalisation. With one
  field and weight 1 this is exactly bm25s ``method="lucene"`` (asserted in exp 13).
* cue tokens (exp 13 stage 4b): corpus B units carry a ``cue`` field with their region and code-family token
  (``dtcir92``, ``regwal`` …); a question adds the code-family tokens its wording implies (:func:`b_code_cues`).
* :class:`LexicalIndex` – build from :class:`corpus.LexicalUnits` (+ optional reception field), pickle / load,
  score a question (unit scores, max-over-units document scores, document ranking).
"""
from __future__ import annotations

import pickle
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import scipy.sparse as sp
import Stemmer
from bm25s.stopwords import STOPWORDS_FRENCH

from config import LEX_CONFIG, RECEPTION
from corpus import LexicalUnits, region_of_code

# ── tokenizer ────────────────────────────────────────────────────────────────────────────────────────────────
_STEMMER = Stemmer.Stemmer("french")
QUESTION_STOPWORDS = {
    "quel", "quelle", "quels", "quelles", "comment", "pourquoi", "combien", "quand", "où",
    "puis", "peux", "peut", "dois", "doit", "faut", "obligé", "obligée", "existe", "fonctionne",
    "etc", "tant", "tous", "toutes", "tout", "toute", "ai", "il", "y", "a",
}
STOP_03 = set("""le la les l un une des du de d et ou à a au aux en dans par pour sur avec sans sous ce cet cette ces
se sa son ses leur leurs mon ma mes ton ta tes notre nos votre vos qui que quoi dont où ne pas plus est sont
été être ont a avoir il elle ils elles on nous vous je tu y ne n s c qu d l lorsque lorsqu si comme mais donc
or ni car tout tous toute toutes même autre autres entre vers chez ainsi aussi alors""".split())


def fold(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


_STOP01 = {fold(w) for w in set(STOPWORDS_FRENCH) | QUESTION_STOPWORDS}
_NUM_GROUPED = re.compile(r"(?<![\d.,])(\d{1,3})((?:[.   ]\d{3})+)(?![\d])")
_ART_SLASH = re.compile(r"(?<![\w/])(\d{1,4})\s*[/^]\s*(\d{1,3})(?![\w/])")
_ART_SUFFIX = re.compile(r"(?<!\w)(\d{1,4})\s*(bis|ter|quater|quinquies|sexies|septies|octies|novies|decies|undecies|duodecies)(?!\w)", re.I)
_ART_ABBR = re.compile(r"(?<!\w)art\.?\s*(?=\d)", re.I)


def normalise_numbers(text: str) -> str:
    """'50.000 euros', '50 000 €', '16.720' → '50000 euros' (groups of exactly 3 digits, so 2.7.4.1.1 / 28.11.2025 stay)."""
    return _NUM_GROUPED.sub(lambda m: m.group(1) + re.sub(r"\D", "", m.group(2)), text)


def normalise_artrefs(text: str) -> str:
    """'art. 145/33' → adds the compound token 'a145s33'; '44bis' → 'a44bis' (not used by the final configs)."""
    text = _ART_ABBR.sub("article ", text)
    text = _ART_SLASH.sub(lambda m: f"{m.group(1)} {m.group(2)} a{m.group(1)}s{m.group(2)}", text)
    return _ART_SUFFIX.sub(lambda m: f"{m.group(1)} a{m.group(1)}{m.group(2).lower()}", text)


@dataclass(frozen=True)
class Tokenizer:
    base: str = "01"          # "01" (exp 01 tokenizer) | "03" (exp 03 / 09 tokenizer, reference only)
    numbers: bool = False
    artrefs: bool = False

    @property
    def key(self) -> str:
        return f"tok{self.base}" + ("+num" if self.numbers else "") + ("+art" if self.artrefs else "")

    def __call__(self, text: str) -> list[str]:
        if self.numbers:
            text = normalise_numbers(text)
        if self.artrefs:
            text = normalise_artrefs(text)
        t = fold(text.lower())
        if self.base == "01":
            toks = [w for w in re.findall(r"\w+", t) if len(w) > 1 or w.isdigit()]
            toks = [w for w in toks if w not in _STOP01]
        else:
            toks = [w for w in re.findall(r"[a-z0-9]+(?:/[0-9]+)*", t) if w not in STOP_03 and len(w) > 1]
        return _STEMMER.stemWords(toks)


# ── sparse field index ───────────────────────────────────────────────────────────────────────────────────────
@dataclass
class TokenStore:
    """Tokenised units: one shared vocabulary; per field a flat id stream + row pointer."""
    vocab: list[str]
    fields: dict[str, tuple[np.ndarray, np.ndarray]]
    n: int

    @classmethod
    def build(cls, units_fields: dict[str, list[list[str]]]) -> "TokenStore":
        st = cls([], {}, len(next(iter(units_fields.values()))))
        for fname, lists in units_fields.items():
            st.add_field(fname, lists)
        return st

    def add_field(self, fname: str, lists: list[list[str]]) -> None:
        assert len(lists) == self.n
        vocab = {t: i for i, t in enumerate(self.vocab)}
        ids: list[int] = []
        rowptr = [0]
        for toks in lists:
            for t in toks:
                i = vocab.get(t)
                if i is None:
                    i = vocab[t] = len(vocab); self.vocab.append(t)
                ids.append(i)
            rowptr.append(len(ids))
        self.fields[fname] = (np.asarray(ids, dtype=np.int32), np.asarray(rowptr, dtype=np.int64))

    def without(self, *fnames: str) -> "TokenStore":
        return TokenStore(list(self.vocab), {f: v for f, v in self.fields.items() if f not in fnames}, self.n)


@dataclass
class FieldIndex:
    vocab: dict[str, int]
    fields: dict[str, sp.csr_matrix]          # field → (n_units × V) tf, float32
    n: int

    @property
    def V(self) -> int:
        return len(self.vocab)

    def idf(self) -> np.ndarray:
        """Lucene IDF on unit frequency over the union of all fields (bm25s method='lucene')."""
        u = None
        for f in self.fields.values():
            u = f.copy() if u is None else u + f
        u = u.tocsr()
        u.data[:] = 1.0
        df = np.asarray(u.sum(axis=0)).ravel()
        return np.log(1.0 + (self.n - df + 0.5) / (df + 0.5)).astype(np.float32)

    def query_vector(self, weights: dict[str, float]) -> np.ndarray:
        q = np.zeros(self.V, dtype=np.float32)
        for t, w in weights.items():
            i = self.vocab.get(t)
            if i is not None:
                q[i] += w
        return q


def build_index(store: TokenStore, fields: list[str] | None = None) -> FieldIndex:
    V, n = len(store.vocab), store.n
    out = {}
    for fname in (fields or list(store.fields)):
        ids, rowptr = store.fields[fname]
        doc = np.repeat(np.arange(n, dtype=np.int64), np.diff(rowptr))
        key = doc * V + ids.astype(np.int64)
        uk, cnt = np.unique(key, return_counts=True)
        m = sp.csr_matrix((cnt.astype(np.float32), (uk // V, uk % V)), shape=(n, V))
        m.sum_duplicates()
        out[fname] = m
    return FieldIndex({t: i for i, t in enumerate(store.vocab)}, out, n)


def bm25f_matrix(index: FieldIndex, weights: dict[str, float], k1: float = 1.5, b: float | dict[str, float] = 0.75) -> sp.csr_matrix:
    """BM25F: pseudo-tf = Σ_f w_f · tf_f / (1 − b_f + b_f · len_f / avglen_f); score = idf · tf'(k1+1)/(k1+tf')."""
    idf = index.idf()
    acc = None
    for fname, w in weights.items():
        if w == 0:
            continue
        tf = index.fields[fname]
        bf = b.get(fname, 0.75) if isinstance(b, dict) else b
        dl = np.asarray(tf.sum(axis=1)).ravel()
        avg = dl.mean() if dl.mean() > 0 else 1.0
        norm = (1.0 - bf + bf * dl / avg).astype(np.float32)
        part = sp.diags((w / norm).astype(np.float32)) @ tf
        acc = part if acc is None else acc + part
    acc = acc.tocsr()
    acc.sum_duplicates()
    acc.data = acc.data * (k1 + 1.0) / (k1 + acc.data)
    return (acc @ sp.diags(idf)).tocsr()


def scores_for(M: sp.csr_matrix, q: np.ndarray) -> np.ndarray:
    return np.asarray(M @ q).ravel().astype(np.float32)


def to_doc_ranking(scores: np.ndarray, unit_doc: np.ndarray, doc_ids: list[str], k_units: int = 3000, top: int = 50) -> list[str]:
    """Max-over-units document ranking; units with score ≤ 0 are dropped."""
    k = min(k_units, len(scores))
    if k < len(scores):
        cand = np.argpartition(-scores, k)[:k]
        cand = cand[np.argsort(-scores[cand], kind="stable")]
    else:
        cand = np.argsort(-scores, kind="stable")
    seen: set[int] = set()
    out: list[str] = []
    for j in cand:
        if scores[j] <= 0:
            break
        d = int(unit_doc[j])
        if d not in seen:
            seen.add(d)
            out.append(doc_ids[d])
            if len(out) >= top:
                break
    return out


# ── cue tokens (exp 13 stage 4b, exp 17 `b_code_cues`) ──────────────────────────────────────────────────────
REGION_TOKEN = {"wal": "regwal", "bxl": "regbxl", "vla": "regvla"}
_B_CODE_CUES = [(r"\btva\b|taxe sur la valeur", "dtctva"), (r"\btva\b|facture", "dtartva"), (r"succession|deces|decede|herit", "dtcsucc"),
                (r"enregistrement|donation|achete|achat|vente d'un|droits de vente", "dtcenr"), (r"circulation|immatricul|voiture|mise en circulation", "dtcta"),
                (r"impot des societes|societe|impot des personnes|declaration|revenus", "dtcir92"), (r"flandre|flamand|gand|louvain|anvers", "dtvcf"),
                (r"precompte immobilier|bruxelles", "dtcbpf")]


def b_code_cues(question: str) -> list[str]:
    q = fold(question.lower())
    return [tok for pat, tok in _B_CODE_CUES if re.search(pat, q)]


def b_cue_tokens(unit_meta: list[dict]) -> list[list[str]]:
    out = []
    for meta in unit_meta:
        code = meta.get("code", "")
        toks = [REGION_TOKEN[r] for r in region_of_code(code).split(",") if r in REGION_TOKEN]
        toks.append("dt" + re.sub(r"_(wal|bxl|vla)$", "", code))
        out.append(toks)
    return out


# ── the index object ─────────────────────────────────────────────────────────────────────────────────────────
class LexicalIndex:
    """BM25F index of one corpus under its exp-13 configuration, optionally with the reception field (B)."""

    def __init__(self, corpus: str, store: TokenStore, unit_doc: np.ndarray, doc_ids: list[str], unit_texts: list[str] | None,
                 cfg: dict | None = None, reception: dict | None = None):
        self.corpus = corpus
        self.cfg = cfg or LEX_CONFIG[corpus]
        self.tok = Tokenizer(**self.cfg["tokenizer"])
        self.store = store                    # base fields only (title / heading / body / cue)
        self.unit_doc = np.asarray(unit_doc, dtype=np.int64)
        self.doc_ids = list(doc_ids)
        self.unit_texts = unit_texts
        self.n_docs = len(doc_ids)
        self.reception_info: dict | None = None
        self._build_matrix(reception)

    # building ------------------------------------------------------------------------------------------------
    @classmethod
    def build(cls, units: LexicalUnits, reception: dict | None = None, cfg: dict | None = None, verbose: bool = True) -> "LexicalIndex":
        cfg = cfg or LEX_CONFIG[units.corpus]
        tok = Tokenizer(**cfg["tokenizer"])
        fields = {f: [tok(t) for t in texts] for f, texts in units.fields.items()}
        store = TokenStore.build(fields)
        if cfg.get("doctype_w"):
            store.add_field("cue", b_cue_tokens(units.unit_meta))
        if verbose:
            print(f"  tokenised {units.corpus} ({tok.key}): {store.n} units, V={len(store.vocab)}", flush=True)
        return cls(units.corpus, store, units.unit_doc, units.doc_ids, units.unit_texts, cfg, reception)

    def _build_matrix(self, reception: dict | None) -> None:
        cfg = self.cfg
        weights = {f: w for f, w in cfg["weights"].items() if w > 0 and f in self.store.fields}
        b = dict(cfg["b"])
        store = self.store
        if reception is not None:
            from reception import reception_tokens  # local import: reception.py imports lexical.Tokenizer
            store = store.without(RECEPTION["field"])
            store.add_field(RECEPTION["field"], reception_tokens(reception, self.tok, self.unit_doc, self.doc_ids))
            weights[RECEPTION["field"]] = RECEPTION["weight"]
            b[RECEPTION["field"]] = RECEPTION["b"]
            self.reception_info = {"variant": RECEPTION["variant"], "weight": RECEPTION["weight"], "b": RECEPTION["b"],
                                   "articles": len(reception), "source": reception.get("__source__", "") if isinstance(reception, dict) else ""}
        self.index = build_index(store, list(weights))
        self.M = bm25f_matrix(self.index, weights, k1=cfg["k1"], b=b)
        self.weights = weights

    def set_reception(self, reception: dict | None) -> None:
        """Swap the reception field (e.g. full ↔ leak-free variant); IDF is recomputed since it spans all fields."""
        self._build_matrix(reception)

    # persistence -----------------------------------------------------------------------------------------------
    def save(self, path: Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        base = self.store.without(RECEPTION["field"])
        with path.open("wb") as fh:
            pickle.dump({"corpus": self.corpus, "cfg": self.cfg, "vocab": base.vocab, "fields": base.fields, "n": base.n,
                         "unit_doc": self.unit_doc, "doc_ids": self.doc_ids}, fh, protocol=pickle.HIGHEST_PROTOCOL)

    @classmethod
    def load(cls, path: Path, reception: dict | None = None, unit_texts: list[str] | None = None) -> "LexicalIndex":
        """Unit texts are not pickled (C: 240 MB of chunk text); pass them from the corpus when passages are needed."""
        with Path(path).open("rb") as fh:
            d = pickle.load(fh)
        store = TokenStore(d["vocab"], d["fields"], d["n"])
        return cls(d["corpus"], store, d["unit_doc"], d["doc_ids"], unit_texts, d["cfg"], reception)

    # querying --------------------------------------------------------------------------------------------------
    def query_weights(self, question: str) -> dict[str, float]:
        w = {t: float(c) for t, c in Counter(self.tok(question)).items()}
        if self.cfg.get("doctype_w"):
            for dt in b_code_cues(question):
                w[dt] = w.get(dt, 0) + self.cfg["doctype_w"]
        return w

    def unit_scores(self, question: str) -> np.ndarray:
        return scores_for(self.M, self.index.query_vector(self.query_weights(question)))

    def doc_scores(self, question: str, unit_scores: np.ndarray | None = None) -> np.ndarray:
        """Max over the units of every document (0 for documents without a matching unit)."""
        s = self.unit_scores(question) if unit_scores is None else unit_scores
        out = np.zeros(self.n_docs, dtype=np.float64)
        np.maximum.at(out, self.unit_doc, s.astype(np.float64))
        return out

    def top_units(self, unit_scores: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray]:
        """Top-k units with a positive score, descending (stable)."""
        k = min(k, len(unit_scores))
        cand = np.argpartition(-unit_scores, k - 1)[:k]
        cand = cand[np.argsort(-unit_scores[cand], kind="stable")]
        cand = cand[unit_scores[cand] > 0]
        return cand, unit_scores[cand]

    def doc_ranking(self, unit_scores: np.ndarray, top: int = 50) -> list[str]:
        return to_doc_ranking(unit_scores, self.unit_doc, self.doc_ids, top=top)
