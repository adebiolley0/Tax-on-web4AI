"""Registry of open-weight embedding models used in the sweep.

Every entry: HF id, query/passage prefixes (or prompt names), max sequence
length used for the sweep (capped at 512 tokens for CPU throughput unless the
model is meant for long context), and loader kind.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ModelSpec:
    key: str
    hf_id: str
    q_prefix: str = ""
    d_prefix: str = ""
    max_seq: int = 512
    kind: str = "st"            # "st" (sentence-transformers) | "model2vec"
    trust_remote_code: bool = False
    params_m: int = 0
    dim: int = 0
    notes: str = ""
    st_kwargs: dict = field(default_factory=dict)
    encode_kwargs: dict = field(default_factory=dict)
    q_encode_kwargs: dict = field(default_factory=dict)


MODELS: dict[str, ModelSpec] = {m.key: m for m in [
    ModelSpec("potion-ml-128m", "minishlab/potion-multilingual-128M", kind="model2vec", params_m=128, dim=256,
              notes="static (model2vec) embeddings – ~1000x faster than transformers, speed floor"),
    ModelSpec("minilm-l12", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", params_m=118, dim=384,
              max_seq=512, notes="repo baseline (docker-compose default)"),
    ModelSpec("e5-small", "intfloat/multilingual-e5-small", "query: ", "passage: ", params_m=118, dim=384),
    ModelSpec("e5-base", "intfloat/multilingual-e5-base", "query: ", "passage: ", params_m=278, dim=768),
    ModelSpec("e5-large", "intfloat/multilingual-e5-large", "query: ", "passage: ", params_m=560, dim=1024),
    ModelSpec("gte-ml-base", "Alibaba-NLP/gte-multilingual-base", trust_remote_code=True, params_m=305, dim=768,
              notes="8k ctx; no prefixes"),
    ModelSpec("modernbert-be", "Parallia/Fairly-Multilingual-ModernBERT-Embed-BE", params_m=150, dim=768,
              notes="Belgian FR/NL/DE/EN ModernBERT embed"),
    ModelSpec("bge-m3", "BAAI/bge-m3", params_m=568, dim=1024, notes="dense head only here; 8k ctx"),
    ModelSpec("arctic-l-v2", "Snowflake/snowflake-arctic-embed-l-v2.0", "query: ", "", params_m=568, dim=1024),
    ModelSpec("solon-large", "OrdalieTech/Solon-embeddings-large-0.1", "query : ", "", params_m=560, dim=1024,
              notes="French-specialised (Ordalie); query prefix 'query : '"),
    ModelSpec("jina-v3", "jinaai/jina-embeddings-v3", trust_remote_code=True, params_m=570, dim=1024,
              notes="task LoRA adapters retrieval.query / retrieval.passage",
              encode_kwargs={"task": "retrieval.passage", "prompt_name": "retrieval.passage"},
              q_encode_kwargs={"task": "retrieval.query", "prompt_name": "retrieval.query"}),
    ModelSpec("qwen3-0.6b", "Qwen/Qwen3-Embedding-0.6B",
              "Instruct: Given a question about Belgian tax law, retrieve the legal text that answers it\nQuery: ", "",
              params_m=600, dim=1024, notes="decoder LLM embedder; last-token pooling; slow on CPU"),
    ModelSpec("static-sim-ml", "sentence-transformers/static-similarity-mrl-multilingual-v1", params_m=100, dim=1024,
              notes="static embeddings (sentence-transformers), very fast"),
    ModelSpec("nomic-v2-moe", "nomic-ai/nomic-embed-text-v2-moe", "search_query: ", "search_document: ",
              trust_remote_code=True, params_m=475, dim=768, notes="MoE, 305M active"),
    ModelSpec("bilingual-large", "Lajavaness/bilingual-embedding-large", trust_remote_code=True, params_m=560, dim=1024,
              notes="FR/EN specialised"),
]}
