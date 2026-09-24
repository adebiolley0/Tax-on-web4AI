#!/usr/bin/env python3
"""Experiment 05 – LlamaIndex structure-aware retrievers vs plain chunk retrieval.

Patterns (all retriever-only, no LLM, no query engine, no cloud components):

* ``sentence_splitter``      SentenceSplitter(chunk_size=400 tok, overlap 50) → VectorStoreIndex
* ``hierarchical_automerge`` HierarchicalNodeParser([2048, 512, 128]) → leaf VectorStoreIndex
                             → AutoMergingRetriever (also logs the un-merged leaf run)
* ``sentence_window``        SentenceWindowNodeParser(window_size=3) → VectorStoreIndex
                             → MetadataReplacementPostProcessor("window")
* ``bm25``                   BM25Retriever (bm25s, French stemmer + French stopwords)
                             over the sentence_splitter nodes
* ``fusion_rrf``             QueryFusionRetriever(vector + bm25, mode="reciprocal_rerank",
                             num_queries=1 → no LLM query generation)

Embeddings: intfloat/multilingual-e5-small via HuggingFaceEmbedding (CPU, 2 threads).
Vector store: the default in-memory SimpleVectorStore; indices are persisted under
``.index_cache/<corpus>/<pattern>`` so a crashed run does not re-embed.

Usage:
  uv run python run_llamaindex.py --corpus A
  uv run python run_llamaindex.py --corpus B --patterns sentence_splitter,hierarchical_automerge,fusion_rrf
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
# nltk >= 3.9.2 ("pathsec") refuses to open hard-linked files; uv installs packages with
# hardlinks, so LlamaIndex's bundled _static/nltk_cache (punkt_tab + stopwords, used by
# SentenceSplitter / SentenceWindowNodeParser) is rejected. Use a plain copy instead:
#   cp -rL .venv/lib/python3.12/site-packages/llama_index/core/_static/nltk_cache .nltk_data
_NLTK = Path(__file__).resolve().parent / ".nltk_data"
if _NLTK.exists():
    os.environ.setdefault("NLTK_DATA", str(_NLTK))

import torch  # noqa: E402

torch.set_num_threads(2)

import Stemmer  # noqa: E402
import transformers  # noqa: E402
from llama_index.core import Document, Settings, StorageContext, VectorStoreIndex, load_index_from_storage  # noqa: E402
from llama_index.core.node_parser import (  # noqa: E402
    HierarchicalNodeParser,
    SentenceSplitter,
    SentenceWindowNodeParser,
    get_leaf_nodes,
)
from llama_index.core.postprocessor import MetadataReplacementPostProcessor  # noqa: E402
from llama_index.core.retrievers import AutoMergingRetriever, QueryFusionRetriever  # noqa: E402
from llama_index.core.schema import NodeWithScore, QueryBundle  # noqa: E402
from llama_index.core.storage.docstore import SimpleDocumentStore  # noqa: E402
from llama_index.embeddings.huggingface import HuggingFaceEmbedding  # noqa: E402
from llama_index.retrievers.bm25 import BM25Retriever  # noqa: E402

from rag_eval import (  # noqa: E402
    Question,
    evaluate_rankings,
    load_corpus_a,
    load_corpus_b,
    load_questions_a,
    load_questions_b,
    print_leaderboard,
    save_result,
)
from rag_eval.chunking import _norm  # noqa: E402
from rag_eval.corpora import DATA_DIR  # noqa: E402
from rag_eval.metrics import dedupe_ranked  # noqa: E402

EXP = "05_llamaindex"
MODEL = "intfloat/multilingual-e5-small"
MODEL_TAG = "e5-small"
TOP_K = 50
HERE = Path(__file__).resolve().parent
INDEX_CACHE = HERE / ".index_cache"
ALL_PATTERNS = ["sentence_splitter", "hierarchical_automerge", "sentence_window", "bm25", "fusion_rrf"]

transformers.logging.set_verbosity_error()


# --------------------------------------------------------------------------- setup
def configure_settings() -> HuggingFaceEmbedding:
    """Global LlamaIndex settings: no LLM (MockLLM), local HF embedding, model tokenizer.

    ``Settings.llm`` is *lazy*: the first component that reads it (QueryFusionRetriever
    does, even with num_queries=1) would instantiate ``OpenAI()`` and fail on the missing
    API key. Assigning ``None`` resolves to a ``MockLLM`` and blocks that path.
    """
    Settings.llm = None
    embed = HuggingFaceEmbedding(
        model_name=MODEL,
        query_instruction="query: ",
        text_instruction="passage: ",
        max_length=512,
        device="cpu",
        normalize=True,
        embed_batch_size=32,
    )
    Settings.embed_model = embed
    # chunk_size is counted with this tokenizer. The default is tiktoken cl100k_base
    # (OpenAI's); we use the embedding model's own tokenizer so 400 tokens == 400 e5 tokens
    # and 512 (max_length) is a hard, meaningful ceiling.
    hf_tok = embed._model.tokenizer
    Settings.tokenizer = lambda t: hf_tok.encode(t, add_special_tokens=False)
    return embed


def default_codes_b() -> list[str]:
    rep = json.loads((DATA_DIR / "corpus_b" / "parse_report.json").read_text())
    return [k for k, v in rep.items() if v.get("default_subset")]


def build_documents(corpus: str, limit: int | None) -> tuple[list[Document], list[Question]]:
    """Wrap rag_eval Docs as LlamaIndex Documents.

    Metadata included in the *embedded* text (LlamaIndex default: "key: value" lines
    prepended to every chunk): ``title`` (A), ``title`` + ``heading_path`` (B), i.e. the
    "contextual chunk header" every chunk carries. ``doc_id``/``code`` are excluded from
    the embedding text and only used to map nodes back to documents.
    """
    if corpus == "A":
        docs, questions = load_corpus_a(), load_questions_a()
    else:
        docs, questions = load_corpus_b(codes=default_codes_b()), load_questions_b()
    if limit:
        keep = {d for q in questions[:6] for d in q.expected}
        docs = [d for d in docs if d.doc_id in keep] + [d for d in docs if d.doc_id not in keep][:limit]
        questions = questions[:6]
    out = []
    for d in docs:
        meta = {"doc_id": d.doc_id, "title": d.title}
        excluded = ["doc_id"]
        if corpus == "B":
            meta["code"] = d.meta.get("code")
            excluded.append("code")
            hp = d.meta.get("heading_path") or []
            if hp:
                meta["heading_path"] = " > ".join(hp)
        out.append(Document(id_=d.doc_id, text=_norm(d.text), metadata=meta,
                            excluded_embed_metadata_keys=excluded, excluded_llm_metadata_keys=excluded))
    return out, questions


# --------------------------------------------------------------------------- index build / cache
def build_or_load_index(pattern: str, corpus: str, li_docs: list[Document], embed: HuggingFaceEmbedding,
                        parse_fn, rebuild: bool, persist: bool) -> tuple[VectorStoreIndex, StorageContext, dict]:
    """parse_fn(docs) -> (all_nodes_for_docstore, nodes_to_embed)."""
    d = INDEX_CACHE / corpus / pattern
    timing: dict = {}
    if d.exists() and not rebuild and persist:
        t0 = time.perf_counter()
        sc = StorageContext.from_defaults(persist_dir=str(d))
        index = load_index_from_storage(sc, embed_model=embed)
        timing["index_load_s"] = round(time.perf_counter() - t0, 1)
        timing["index_from_cache"] = True
        print(f"[{pattern}] loaded persisted index from {d} ({len(sc.docstore.docs)} nodes in docstore)", flush=True)
        return index, sc, timing
    t0 = time.perf_counter()
    all_nodes, embed_nodes = parse_fn(li_docs)
    timing["parse_s"] = round(time.perf_counter() - t0, 1)
    docstore = SimpleDocumentStore()
    docstore.add_documents(all_nodes)
    sc = StorageContext.from_defaults(docstore=docstore)
    print(f"[{pattern}] parsed {len(all_nodes)} nodes ({len(embed_nodes)} to embed) in {timing['parse_s']}s; embedding…",
          flush=True)
    t1 = time.perf_counter()
    index = VectorStoreIndex(embed_nodes, storage_context=sc, embed_model=embed, show_progress=True)
    timing["embed_s"] = round(time.perf_counter() - t1, 1)
    timing["index_build_s"] = round(time.perf_counter() - t0, 1)
    timing["n_nodes_embedded"] = len(embed_nodes)
    timing["n_nodes_docstore"] = len(all_nodes)
    print(f"[{pattern}] embedded {len(embed_nodes)} nodes in {timing['embed_s']}s "
          f"({len(embed_nodes) / max(timing['embed_s'], 1e-6):.1f} nodes/s)", flush=True)
    if persist:
        d.mkdir(parents=True, exist_ok=True)
        sc.persist(persist_dir=str(d))
    return index, sc, timing


def parse_sentence_splitter(docs):
    nodes = SentenceSplitter(chunk_size=400, chunk_overlap=50).get_nodes_from_documents(docs)
    return nodes, nodes


def parse_hierarchical(docs):
    nodes = HierarchicalNodeParser.from_defaults(chunk_sizes=[2048, 512, 128]).get_nodes_from_documents(docs)
    return nodes, get_leaf_nodes(nodes)


def parse_sentence_window(docs):
    nodes = SentenceWindowNodeParser.from_defaults(
        window_size=3, window_metadata_key="window", original_text_metadata_key="original_text",
    ).get_nodes_from_documents(docs)
    return nodes, nodes


# --------------------------------------------------------------------------- evaluation
def to_ranking(nws: list[NodeWithScore]) -> list[str]:
    ordered = sorted(nws, key=lambda n: (n.score if n.score is not None else 0.0), reverse=True)  # stable
    return dedupe_ranked(n.node.metadata.get("doc_id") or n.node.ref_doc_id for n in ordered)


def run_queries(retrieve_fn, questions: list[Question]) -> tuple[dict[str, list[str]], dict]:
    rankings, lat = {}, []
    for q in questions:
        t0 = time.perf_counter()
        nws = retrieve_fn(q.question)
        lat.append(time.perf_counter() - t0)
        rankings[q.qid] = to_ranking(nws)
    timing = {"query_mean_ms": round(1000 * statistics.mean(lat), 1),
              "query_p50_ms": round(1000 * statistics.median(lat), 1),
              "query_max_ms": round(1000 * max(lat), 1)}
    return rankings, timing


def record(name: str, corpus: str, questions, rankings, config: dict, timing: dict, save: bool):
    res = evaluate_rankings(name, corpus, questions, rankings, config=config, timing=timing)
    if save:
        save_result(EXP, res)
    print(res.summary(), f"| {timing}", flush=True)
    return res


# --------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="A", choices=["A", "B"])
    ap.add_argument("--patterns", default=",".join(ALL_PATTERNS))
    ap.add_argument("--limit_docs", type=int, default=None, help="smoke test on a subset (no save, no cache)")
    ap.add_argument("--rebuild", action="store_true", help="ignore persisted indices")
    ap.add_argument("--leaderboard", action="store_true")
    a = ap.parse_args()
    if a.leaderboard:
        print_leaderboard(a.corpus); return
    patterns = a.patterns.split(",")
    smoke = a.limit_docs is not None
    save, persist = not smoke, not smoke

    import llama_index.core, llama_index.embeddings.huggingface, llama_index.retrievers.bm25, bm25s  # noqa: E401
    versions = {"llama-index-core": llama_index.core.__version__,
                "torch": torch.__version__, "bm25s": bm25s.__version__}
    t0 = time.perf_counter()
    embed = configure_settings()
    print(f"settings ready in {time.perf_counter() - t0:.1f}s; llm={type(Settings.llm).__name__}; {versions}", flush=True)
    li_docs, questions = build_documents(a.corpus, a.limit_docs)
    print(f"corpus {a.corpus}: {len(li_docs)} documents, {len(questions)} questions", flush=True)
    base_cfg = {"model": MODEL, "top_k": TOP_K, "n_docs": len(li_docs), **versions}

    needs_ss = {"sentence_splitter", "bm25", "fusion_rrf"} & set(patterns)
    ss_index = ss_sc = None
    if needs_ss:
        ss_index, ss_sc, ss_timing = build_or_load_index("sentence_splitter", a.corpus, li_docs, embed,
                                                         parse_sentence_splitter, a.rebuild, persist)
        ss_cfg = {**base_cfg, "chunk_size_tokens": 400, "chunk_overlap": 50, "n_nodes": len(ss_sc.docstore.docs)}

    if "sentence_splitter" in patterns:
        retr = ss_index.as_retriever(similarity_top_k=TOP_K)
        rankings, qt = run_queries(retr.retrieve, questions)
        record(f"llamaindex__sentence_splitter_400__{MODEL_TAG}", a.corpus, questions, rankings,
               {**ss_cfg, "pattern": "SentenceSplitter → VectorIndexRetriever"}, {**ss_timing, **qt}, save)

    if "hierarchical_automerge" in patterns:
        h_index, h_sc, h_timing = build_or_load_index("hierarchical_2048_512_128", a.corpus, li_docs, embed,
                                                      parse_hierarchical, a.rebuild, persist)
        n_leaf = len(get_leaf_nodes(list(h_sc.docstore.docs.values())))
        cfg = {**base_cfg, "chunk_sizes": [2048, 512, 128], "n_nodes_total": len(h_sc.docstore.docs), "n_leaf": n_leaf}
        base_retr = h_index.as_retriever(similarity_top_k=TOP_K)
        rankings, qt = run_queries(base_retr.retrieve, questions)
        record(f"llamaindex__hierarchical_leaf_128__{MODEL_TAG}", a.corpus, questions, rankings,
               {**cfg, "pattern": "HierarchicalNodeParser leaves → VectorIndexRetriever (no merging)"},
               {**h_timing, **qt}, save)
        am = AutoMergingRetriever(base_retr, h_sc, simple_ratio_thresh=0.5, verbose=False)
        rankings, qt = run_queries(am.retrieve, questions)
        record(f"llamaindex__hierarchical_automerge_2048_512_128__{MODEL_TAG}", a.corpus, questions, rankings,
               {**cfg, "simple_ratio_thresh": 0.5, "pattern": "HierarchicalNodeParser → AutoMergingRetriever"},
               {**h_timing, **qt}, save)

    if "sentence_window" in patterns:
        w_index, w_sc, w_timing = build_or_load_index("sentence_window_3", a.corpus, li_docs, embed,
                                                      parse_sentence_window, a.rebuild, persist)
        retr = w_index.as_retriever(similarity_top_k=TOP_K)
        post = MetadataReplacementPostProcessor(target_metadata_key="window")

        def retrieve_window(q: str):
            qb = QueryBundle(q)
            return post.postprocess_nodes(retr.retrieve(qb), query_bundle=qb)

        rankings, qt = run_queries(retrieve_window, questions)
        record(f"llamaindex__sentence_window_3__{MODEL_TAG}", a.corpus, questions, rankings,
               {**base_cfg, "window_size": 3, "n_nodes": len(w_sc.docstore.docs),
                "pattern": "SentenceWindowNodeParser → VectorIndexRetriever → MetadataReplacementPostProcessor"},
               {**w_timing, **qt}, save)

    bm25 = None
    if {"bm25", "fusion_rrf"} & set(patterns):
        t0 = time.perf_counter()
        bm25 = BM25Retriever.from_defaults(docstore=ss_index.docstore, stemmer=Stemmer.Stemmer("french"),
                                           language="french", similarity_top_k=TOP_K)
        bm25_build = round(time.perf_counter() - t0, 1)
        print(f"[bm25] index built over {len(ss_sc.docstore.docs)} sentence_splitter nodes in {bm25_build}s", flush=True)
    if "bm25" in patterns:
        rankings, qt = run_queries(bm25.retrieve, questions)
        record("llamaindex__bm25", a.corpus, questions, rankings,
               {**ss_cfg, "stemmer": "french", "stopwords": "french", "pattern": "BM25Retriever (bm25s)"},
               {"bm25_build_s": bm25_build, **qt}, save)
    if "fusion_rrf" in patterns:
        fusion = QueryFusionRetriever([ss_index.as_retriever(similarity_top_k=TOP_K), bm25],
                                      similarity_top_k=TOP_K, num_queries=1, mode="reciprocal_rerank",
                                      use_async=False, llm=None, verbose=False)
        rankings, qt = run_queries(fusion.retrieve, questions)
        record(f"llamaindex__fusion_rrf__{MODEL_TAG}", a.corpus, questions, rankings,
               {**ss_cfg, "stemmer": "french", "stopwords": "french", "fusion": "reciprocal_rerank", "num_queries": 1,
                "pattern": "QueryFusionRetriever(vector + BM25)"},
               {**ss_timing, "bm25_build_s": bm25_build, **qt}, save)


if __name__ == "__main__":
    main()
