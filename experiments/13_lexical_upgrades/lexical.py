"""Experiment 13 – lexical retrieval upgrades, shared machinery.

* :class:`Tokenizer` – the tuned tokenizer of experiment 01 (`base="01"`: French Snowball +
  bm25s French stopwords + question-word list + accent folding) and the variant used for
  corpus C in experiment 09 (`base="03"`: same idea, shorter stoplist, keeps ``145/33``),
  plus the query/document normalisations of method 4 (numbers, article references).
* :class:`FieldIndex` – sparse term-frequency matrices per field (title / heading / body …)
  sharing one vocabulary, with document-level IDF.
* :func:`bm25f_matrix` – BM25 (single field, identical to bm25s ``method="lucene"``) or
  BM25F (weighted fields, per-field length normalisation) as a sparse (units × vocab)
  score matrix; queries are *weighted* term vectors, so pseudo-relevance feedback (RM3) and
  expansion terms are just extra weights.
* :func:`rm3_expand` – RM3-style pseudo-relevance feedback.
* :class:`PMI` – co-occurrence (window ±10) PMI table for query terms, computed once per corpus.
* :func:`collapse_groups` – duplicate collapsing (yearly / version editions of the same text).
"""
from __future__ import annotations

import hashlib
import math
import os
import pickle
import re
import time
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import scipy.sparse as sp
import Stemmer
from bm25s.stopwords import STOPWORDS_FRENCH

from rag_eval import Chunk, Question

CACHE_DIR = Path(os.environ.get("EXP13_CACHE", Path(__file__).parent / ".cache"))

# ── tokenizers ───────────────────────────────────────────────────────────────
_STEMMER = Stemmer.Stemmer("french")

# experiment 01: bm25s French stoplist + interrogatives / modals / fillers
QUESTION_STOPWORDS = {
    "quel", "quelle", "quels", "quelles", "comment", "pourquoi", "combien", "quand", "où",
    "puis", "peux", "peut", "dois", "doit", "faut", "obligé", "obligée", "existe", "fonctionne",
    "etc", "tant", "tous", "toutes", "tout", "toute", "ai", "il", "y", "a",
}
# experiment 03/09 stoplist (used for the corpus-C baseline)
STOP_03 = set("""le la les l un une des du de d et ou à a au aux en dans par pour sur avec sans sous ce cet cette ces
se sa son ses leur leurs mon ma mes ton ta tes notre nos votre vos qui que quoi dont où ne pas plus est sont
été être ont a avoir il elle ils elles on nous vous je tu y ne n s c qu d l lorsque lorsqu si comme mais donc
or ni car tout tous toute toutes même autre autres entre vers chez ainsi aussi alors""".split())


def fold(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


_NUM_GROUPED = re.compile(r"(?<![\d.,])(\d{1,3})((?:[.   ]\d{3})+)(?![\d])")
_ART_SLASH = re.compile(r"(?<![\w/])(\d{1,4})\s*[/^]\s*(\d{1,3})(?![\w/])")
_ART_SUFFIX = re.compile(r"(?<!\w)(\d{1,4})\s*(bis|ter|quater|quinquies|sexies|septies|octies|novies|decies|undecies|duodecies)(?!\w)", re.I)
_ART_ABBR = re.compile(r"(?<!\w)art\.?\s*(?=\d)", re.I)
_ORD = {"1er": "1", "1ère": "1"}


def normalise_numbers(text: str) -> str:
    """'50.000 euros', '50 000 €', '16.720' → '50000 euros' … (thousand groups joined).
    Groups must be exactly 3 digits so article numbers like 2.7.4.1.1 or dates 28.11.2025 are untouched."""
    return _NUM_GROUPED.sub(lambda m: m.group(1) + re.sub(r"\D", "", m.group(2)), text)


def normalise_artrefs(text: str) -> str:
    """'art. 145/33', '145^33', 'article 145 33' → adds the compound token 'a145s33' next to the
    plain digits; '44bis' / '44 bis' → 'a44bis'; 'art.' → 'article'."""
    text = _ART_ABBR.sub("article ", text)
    text = _ART_SLASH.sub(lambda m: f"{m.group(1)} {m.group(2)} a{m.group(1)}s{m.group(2)}", text)
    text = _ART_SUFFIX.sub(lambda m: f"{m.group(1)} a{m.group(1)}{m.group(2).lower()}", text)
    return text


@dataclass(frozen=True)
class Tokenizer:
    base: str = "01"          # "01" (A/B baseline) | "03" (C baseline)
    numbers: bool = False     # normalise_numbers on text and queries
    artrefs: bool = False     # normalise_artrefs on text and queries

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


_STOP01 = {fold(w) for w in set(STOPWORDS_FRENCH) | QUESTION_STOPWORDS}


# ── sparse field index ──────────────────────────────────────────────────────
@dataclass
class FieldIndex:
    """Term-frequency matrices per field over the same units and one shared vocabulary."""
    vocab: dict[str, int]
    fields: dict[str, sp.csr_matrix]          # field → (n_units × V) tf, float32
    n: int

    @property
    def V(self) -> int:
        return len(self.vocab)

    def tf_union(self) -> sp.csr_matrix:
        m = None
        for f in self.fields.values():
            m = f.copy() if m is None else m + f
        return m.tocsr()

    def df(self) -> np.ndarray:
        u = self.tf_union().copy()
        u.data[:] = 1.0
        return np.asarray(u.sum(axis=0)).ravel()

    def idf(self) -> np.ndarray:
        """Lucene IDF on document (unit) frequency over all fields (bm25s method='lucene')."""
        df = self.df()
        return np.log(1.0 + (self.n - df + 0.5) / (df + 0.5)).astype(np.float32)

    def ids(self, tokens: list[str]) -> list[int]:
        return [self.vocab[t] for t in tokens if t in self.vocab]

    def query_vector(self, weights: dict[str, float]) -> np.ndarray:
        q = np.zeros(self.V, dtype=np.float32)
        for t, w in weights.items():
            i = self.vocab.get(t)
            if i is not None:
                q[i] += w
        return q


@dataclass
class TokenStore:
    """Tokenised units: one shared vocabulary, per field a flat id stream + row pointer."""
    vocab: list[str]
    fields: dict[str, tuple[np.ndarray, np.ndarray]]
    n: int

    @classmethod
    def build(cls, units_fields: dict[str, list[list[str]]]) -> "TokenStore":
        vocab: dict[str, int] = {}
        fields = {}
        n = None
        for fname, lists in units_fields.items():
            n = len(lists) if n is None else n
            assert len(lists) == n
            ids: list[int] = []
            rowptr = [0]
            for toks in lists:
                for t in toks:
                    i = vocab.get(t)
                    if i is None:
                        i = vocab[t] = len(vocab)
                    ids.append(i)
                rowptr.append(len(ids))
            fields[fname] = (np.asarray(ids, dtype=np.int32), np.asarray(rowptr, dtype=np.int64))
        return cls(list(vocab), fields, n)

    def streams(self, fname: str) -> list[np.ndarray]:
        ids, rp = self.fields[fname]
        return [ids[rp[i]:rp[i + 1]] for i in range(self.n)]

    def add_field(self, fname: str, lists: list[list[str]]) -> None:
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


def build_index(store: TokenStore, fields: list[str] | None = None) -> FieldIndex:
    V = len(store.vocab)
    n = store.n
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


def extend_index(index: FieldIndex, store: TokenStore, fields: list[str]) -> FieldIndex:
    """Add `fields` of `store` (whose vocabulary may have grown) to an existing index without rebuilding
    the other fields (memory: corpus C)."""
    extra = build_index(store, fields)
    V = len(store.vocab)
    out = {}
    for fname, m in index.fields.items():
        out[fname] = sp.csr_matrix((m.data, m.indices, m.indptr), shape=(index.n, V))
    out.update(extra.fields)
    return FieldIndex(extra.vocab, out, index.n)


def bm25f_matrix(index: FieldIndex, weights: dict[str, float], k1: float = 1.5, b: float | dict[str, float] = 0.75,
                 idf: np.ndarray | None = None) -> sp.csr_matrix:
    """BM25F: pseudo-tf = Σ_f w_f · tf_f / (1 − b_f + b_f · len_f / avglen_f); score = idf · tf'(k1+1)/(k1+tf').
    With one field and weight 1 this is exactly BM25 (bm25s 'lucene')."""
    idf = index.idf() if idf is None else idf
    acc = None
    for fname, w in weights.items():
        if w == 0:
            continue
        tf = index.fields[fname]
        bf = b.get(fname, 0.75) if isinstance(b, dict) else b
        dl = np.asarray(tf.sum(axis=1)).ravel()
        avg = dl.mean() if dl.mean() > 0 else 1.0
        norm = (1.0 - bf + bf * dl / avg).astype(np.float32)
        scale = (w / norm).astype(np.float32)
        part = sp.diags(scale) @ tf
        acc = part if acc is None else acc + part
    acc = acc.tocsr()
    acc.sum_duplicates()
    acc.data = acc.data * (k1 + 1.0) / (k1 + acc.data)
    acc = (acc @ sp.diags(idf)).tocsr()
    return acc


def concat_fields(index: FieldIndex, repeats: dict[str, int]) -> FieldIndex:
    """Cheap BM25F approximation: one field = body + title repeated n times (token concatenation)."""
    m = None
    for fname, r in repeats.items():
        if r == 0:
            continue
        part = index.fields[fname] * float(r)
        m = part if m is None else m + part
    return FieldIndex(index.vocab, {"all": m.tocsr()}, index.n)


# ── scoring helpers ─────────────────────────────────────────────────────────
def scores_for(M: sp.csr_matrix, q: np.ndarray) -> np.ndarray:
    return np.asarray(M @ q).ravel().astype(np.float32)


def to_doc_ranking(scores: np.ndarray, unit_doc: np.ndarray, k_units: int = 3000, top: int = 50,
                   mask: np.ndarray | None = None) -> list[str]:
    """Max-over-units document ranking; units with score ≤ 0 are dropped (bm25s returns them in
    arbitrary order)."""
    s = scores if mask is None else np.where(mask, scores, -1.0)
    k = min(k_units, len(s))
    if k < len(s):
        cand = np.argpartition(-s, k)[:k]
        cand = cand[np.argsort(-s[cand], kind="stable")]
    else:
        cand = np.argsort(-s, kind="stable")
    seen: set[str] = set()
    out: list[str] = []
    for j in cand:
        if s[j] <= 0:
            break
        d = unit_doc[j]
        if d not in seen:
            seen.add(d)
            out.append(d)
            if len(out) >= top:
                break
    return out


# ── RM3 pseudo-relevance feedback ───────────────────────────────────────────
def rm3_expand(index: FieldIndex, tf_union: sp.csr_matrix, dl: np.ndarray, idf: np.ndarray,
               q_weights: dict[str, float], first_pass: np.ndarray, k: int, m: int, lam: float,
               inv_vocab: list[str], unit_doc: np.ndarray | None = None) -> dict[str, float]:
    """Relevance model from the top-k first-pass units: P(w|R) ∝ Σ_d P(d|q)·tf(w,d)/|d|·idf(w)
    (tf-idf weighted); keep the top-m terms, interpolate: λ·q_norm + (1−λ)·expansion."""
    order = np.argsort(-first_pass, kind="stable")
    top = [j for j in order[: max(k * 4, k)] if first_pass[j] > 0]
    if unit_doc is not None:                    # one unit per document among the feedback set
        seen, uniq = set(), []
        for j in top:
            if unit_doc[j] not in seen:
                seen.add(unit_doc[j]); uniq.append(j)
        top = uniq
    top = top[:k]
    if not top:
        return dict(q_weights)
    sc = first_pass[top]
    p_d = sc / sc.sum()
    fb = np.zeros(index.V, dtype=np.float64)
    for j, pd in zip(top, p_d):
        row = tf_union.getrow(j)
        fb[row.indices] += pd * row.data / max(dl[j], 1.0)
    fb *= idf
    cand = np.argsort(-fb)[: m * 2]
    exp_terms = [(inv_vocab[i], fb[i]) for i in cand if fb[i] > 0][:m]
    if not exp_terms:
        return dict(q_weights)
    z = sum(w for _, w in exp_terms)
    qz = sum(q_weights.values()) or 1.0
    out: dict[str, float] = {t: lam * w / qz for t, w in q_weights.items()}
    for t, w in exp_terms:
        out[t] = out.get(t, 0.0) + (1 - lam) * w / z
    return out


# ── PMI co-occurrence expansion ─────────────────────────────────────────────
class PMI:
    """Window (±window) co-occurrence PMI between a set of query terms and every corpus term,
    computed once from the token id streams (cached). Processed in blocks to bound memory."""

    def __init__(self, streams: list[np.ndarray], V: int, qterm_ids: list[int], window: int = 10,
                 min_count: int = 20, min_pair: int = 3, block: int = 4_000_000):
        self.window, self.min_count, self.min_pair = window, min_count, min_pair
        qids = np.asarray(sorted(set(qterm_ids)), dtype=np.int64)
        nq = len(qids)
        pos = np.full(V + 1, -1, dtype=np.int64)
        pos[qids] = np.arange(nq)
        pad = np.full(window, V, dtype=np.int32)
        a = np.concatenate([np.concatenate([s.astype(np.int32), pad]) for s in streams])
        self.N = float(len(a))
        counts = np.bincount(a, minlength=V + 1).astype(np.float64)
        counts[V] = 0
        self.counts = counts
        acc = np.zeros(nq * (V + 1), dtype=np.int64)
        for start in range(0, len(a), block):
            blk = a[start: start + block + window].astype(np.int64)
            for o in range(1, window + 1):
                left, right = blk[:-o], blk[o:]
                for x, y in ((left, right), (right, left)):
                    qi = pos[x]
                    msk = (qi >= 0) & (y != V) & (x != y)
                    keys = qi[msk] * (V + 1) + y[msk]
                    acc += np.bincount(keys, minlength=len(acc))
        nz = np.nonzero(acc)[0]
        cnt = acc[nz].astype(np.float64)
        qi_of = nz // (V + 1)
        w_of = nz % (V + 1)
        del acc
        pmi = np.log((cnt * self.N) / (counts[qids[qi_of]] * counts[w_of] * 2 * window))
        ok = (cnt >= min_pair) & (counts[w_of] >= min_count)
        self.qids, self.V = qids, V
        self.table: dict[int, list[tuple[int, float]]] = {}
        for qi, w, p in zip(qi_of[ok], w_of[ok], pmi[ok]):
            self.table.setdefault(int(qids[qi]), []).append((int(w), float(p)))
        for k in self.table:
            self.table[k].sort(key=lambda x: -x[1])

    def expand(self, term_id: int, top: int = 3) -> list[tuple[int, float]]:
        return self.table.get(term_id, [])[:top]


def pmi_expand_weights(weights: dict[str, float], pmi: "PMI", vocab: dict[str, int], inv_vocab: list[str],
                       w_exp: float, top: int = 3) -> dict[str, float]:
    """Add the top-`top` PMI neighbours of every query term (weight w_exp × term weight)."""
    out = dict(weights)
    extra: dict[str, float] = {}
    for t, c in weights.items():
        i = vocab.get(t)
        if i is None:
            continue
        for wid, _p in pmi.expand(i, top):
            extra[inv_vocab[wid]] = extra.get(inv_vocab[wid], 0.0) + w_exp * c
    for t, x in extra.items():
        out[t] = out.get(t, 0.0) + x
    return out


# ── duplicate collapsing (corpus C) ────────────────────────────────────────
_YEAR_ED = re.compile(r"\s*\((?:revenus|ex\.? d'imp\.?|exercice d'imposition)\s*20\d\d\)\*{0,2}", re.I)
_VERSION = re.compile(r"\s*\(version\s*\d+\)", re.I)
_REV_TAIL = re.compile(r"\s*-\s*revenus\s*20\d\d\s*-\s*exercice d'imposition\s*20\d\d", re.I)
_NUM_YEAR = re.compile(r"^num[ée]ro\s+(\d+)/20\d\d$", re.I)


def group_key(doc_id: str, title: str, meta: dict) -> str:
    """Documents that are yearly / version editions of the same text share a key.
    Regional twins are *not* collapsed (they are different law)."""
    t = title.strip().rstrip("*").strip()
    t2 = _YEAR_ED.sub("", t)
    t2 = _VERSION.sub("", t2)
    t2 = _REV_TAIL.sub("", t2)
    m = _NUM_YEAR.match(t2)
    folder = meta.get("folder") or doc_id.split("/")[0]
    if m:                                       # Forfaits 'Numéro 198/2015' ↔ '198 - …'
        return f"{folder}::forfait::{m.group(1)}"
    if folder == "forfaits":
        m2 = re.match(r"^(\d+)\s*-", t2)
        if m2:
            return f"{folder}::forfait::{m2.group(1)}"
    if t2 == t and folder != "faq":
        return doc_id                           # not an edition → its own group
    return f"{folder}::{fold(t2.lower())}"


def collapse_groups(doc_ids: list[str], keys: dict[str, str], prefer: dict[str, float]) -> dict[str, str]:
    """doc → representative doc of its group (the member with the highest `prefer` value)."""
    groups: dict[str, list[str]] = defaultdict(list)
    for d in doc_ids:
        groups[keys[d]].append(d)
    rep = {}
    for g, members in groups.items():
        r = max(members, key=lambda d: (prefer.get(d, 0.0), d))
        for d in members:
            rep[d] = r
    return rep


# ── region / doc-type cues ─────────────────────────────────────────────────
DOCTYPE_TOKEN = {
    "Circulaires": "dtcirc", "Décisions anticipées (L 24.12.2002)": "dtruling", "Décisions anticipées (art. 345 CIR 92)": "dtruling",
    "Décisions anticipées (AR 03.05.1999)": "dtruling", "Questions parlementaires": "dtqp", "Jurisprudence belge": "dtjur",
    "Jurisprudence européenne": "dtjureu", "Conventions préventives de la double imposition": "dtcpdi",
    "Arrêtés royaux": "dtar", "Arrêtés ministériels": "dtam", "Forfaits": "dtforfait", "FAQ": "dtfaq",
    "Commentaires (dont Rép. RJ)": "dtcom", "Code et législation": "dtcode",
    "Législation et règlementation régionale et locale": "dtregio", "Communications": "dtcomm", "Avis": "dtavis",
    "Règlementation européenne": "dtregeu", "Traités et accords internationaux": "dttraite",
}
# query cue → doc-type token (matched on the accent-folded lower-cased question)
DOCTYPE_CUES = [
    (r"\bcirculaire", "dtcirc"), (r"\bruling|decision anticipee|service des decisions anticipees|\bsda\b", "dtruling"),
    (r"question parlementaire|le ministre|\bdepute", "dtqp"),
    (r"\barret\b|\bjugement|\btribunal|cour d'appel|cour de cassation|cour constitutionnelle|\bjuge\b|jurisprudence", "dtjur"),
    (r"cour de justice|\bcjue\b|europeen", "dtjureu"), (r"convention (?:preventive|fiscale|belgo)|double imposition|\bcpdi\b|frontalier", "dtcpdi"),
    (r"arrete royal|\bar/cir|\bar cir", "dtar"), (r"\bforfait", "dtforfait"), (r"\bfaq\b", "dtfaq"),
    (r"commentaire|\bcom\.?ir|repertoire", "dtcom"), (r"\bcir\s*92|\barticle\s+\d|\bart\.\s*\d|code des|\bcode\b", "dtcode"),
]
REGION_TOKEN = {"wal": "regwal", "bxl": "regbxl", "vla": "regvla"}
_REGION_DOC_WORDS = {
    "wal": ["region wallonne", "wallon", "wallonie"],
    "bxl": ["bruxelles-capitale", "bruxelles capitale", "bruxellois", "region de bruxelles"],
    "vla": ["region flamande", "flamand", "vlaams", "flandre", "autorite flamande"],
}


def region_of_text(*parts: str) -> str | None:
    t = fold(" ".join(p for p in parts if p).lower())
    for r, words in _REGION_DOC_WORDS.items():
        if any(w in t for w in words):
            return r
    return None


def doctype_cues(question: str) -> list[str]:
    q = fold(question.lower())
    return [tok for pat, tok in DOCTYPE_CUES if re.search(pat, q)]


# ── evaluation helpers ─────────────────────────────────────────────────────
def split_line(res) -> str:
    m = res.metrics
    return (f"train MRR={m.get('train_mrr', 0):.3f} H@1={m.get('train_hit@1', 0):.3f} | "
            f"val MRR={m.get('val_mrr', 0):.3f} H@1={m.get('val_hit@1', 0):.3f} R@10={m.get('val_recall@10', 0):.3f} | "
            f"all MRR={m['mrr']:.3f} H@1={m['hit@1']:.3f} R@10={m['recall@10']:.3f}")


def cache_path(name: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / name


def cached(name: str, fn):
    p = cache_path(name)
    if p.exists():
        with p.open("rb") as fh:
            return pickle.load(fh)
    obj = fn()
    with p.open("wb") as fh:
        pickle.dump(obj, fh, protocol=pickle.HIGHEST_PROTOCOL)
    return obj
