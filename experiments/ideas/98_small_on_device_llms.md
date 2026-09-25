# 98 — Small on-device LLMs (Qwen3-0.6B/1.7B, Gemma-3n, Phi-4-mini) as query rewriters / rerankers on CPU

**Idea**

Run a sub-2B open-weight LLM locally through llama.cpp (GGUF, Q8_0/Q4_K_M) on the 4-core box in two query-path roles: (a) a *query rewriter* that turns a layman question into 3–8 statute-vocabulary keywords appended to the original query (never replacing it) before French BM25 / hybrid; (b) a *pointwise reranker* (Qwen3-Reranker-0.6B, yes/no logits) replacing bge-reranker-v2-m3. Both work without DeepSeek; the plumbing is reused verbatim when the hosted LLM arrives (ideas 46, 52).

**Why it fits this project**

The dominant failure on B and C is the layman ↔ statute vocabulary gap (EXPERIMENTS.md §3.2, §4), which retrieval-only fixes barely move (idea 34: +0.01–0.03). A local model needs no key, keeps taxpayer questions on the box (idea 86), and is the only LLM we can put behind the MCP `search` tool in this phase. The machine suits it: Xeon with AVX-512 VNNI (llama.cpp int8 kernels), ~5 GB free RAM, and `run_queue.sh` discipline.

**Evidence**

- Qwen3-0.6B: 0.44B non-embedding params, 28 layers, 32k ctx, Apache-2.0, `/no_think` switch, 100+ languages, GGUF available (verified). Gemma-3n-E2B: 2B effective params, restrictive Gemma licence, Global-MMLU-Lite 59.0 (verified). Phi-4-mini: 3.8B, MIT, French supported, multilingual MMLU 49.3 (verified) — too slow here.
- Qwen3-Reranker-0.6B: Apache-2.0, yes/no-token scoring, MMTEB-R 66.4 vs 72.7 for 4B (verified). MIRACL-fr 60.5 vs 61.7 for bge-reranker-v2-m3 (LAMAR table via idea 08) — **no French gain**.
- llama.cpp supports Qwen3 embedding (#15023) and reranking (#15824); `llama-server --rerank` exposes `/v1/rerank`; `--cache-prompt` and slot save/restore cache a fixed few-shot prefix; `ggml-org/Qwen3-Reranker-0.6B-Q8_0-GGUF` exists (all verified).
- LLM query expansion beats PRF, CoT prompts best (Jagerman et al. 2023, verified); "expansion improves scores for weaker models but generally harms stronger models" over 24 retrievers (Weller et al. 2024, verified). Our stack is strong on A/C, weak on B.
- Throughput on this box (**unverified**, extrapolated from public 4–8-core AVX-512 llama.cpp numbers): Qwen3-0.6B Q8_0 ≈ 250–500 tok/s prefill, 20–35 tok/s decode; 1.7B Q4_K_M ≈ 100–200 / 10–18; Gemma-3n-E2B ≈ 8–12 decode; Phi-4-mini Q4 ≈ 60–100 / 5–8. Consistent with idea 06's 15–30 s per 3k-token prompt.

**How we would implement it**

1. `experiments/10_small_llm_query` (uv project; `llama-cpp-python` with AVX-512 or a `llama-server` binary). Download Qwen3-0.6B / 1.7B GGUF; measure real tok/s with `llama-bench -t 4` and record it.
2. `rewrite.py`: system text + 4 few-shot pairs from idea 34's lexicon (*précompte professionnel, quotité exemptée, RDT…*) + question, `/no_think`, ≤40 output tokens, greedy, JSON list of terms; prefix cached. Post-filter: strip any generated `art. NNN` (hallucination guard) and terms absent from the corpus vocabulary. Cache in `experiments/data/rewrites/{model}_{prompt_hash}.json` keyed by question id.
3. Add an optional `variants` field to `rag_eval.corpora.Question` and `--query_variant` to `01_bm25/run_bm25.py` and `09_corpus_c/run_corpus_c.py`; run original vs original+expansion on A/B/C plus convex fusion of both BM25 runs; `evaluate_rankings` → `append_leaderboard`, validation split, paired bootstrap (idea 72).
4. Reranker: `llama-server --rerank -m Qwen3-Reranker-0.6B-Q8_0.gguf`, 30 candidates at 512 tokens, as an HTTP entry in `03_hybrid_rerank/RERANKERS`; compare MRR and wall time with bge on identical candidates.
5. If (3) gives ≥ +0.03 on B: optional pre-step in `mcp_server.py` with a 3 s timeout falling back to the raw query.

**Expected gain and cost**

Rewriter: B +0.01–0.05 MRR, C ±0.02, A ≈ 0 (Weller effect) — **speculation**; 1.7B likely a little better on Belgian terms. Latency per query (**unverified**): 0.6B ≈ 2–3 s for a 300-token prompt + 40 output tokens (≈1.5 s with cached prefix), 1.7B ≈ 5–6 s, Phi-4-mini ≈ 10 s. RAM +0.7–1.5 GB. Reranker: 30 × ~600-token pairs ≈ 18k prefill tokens ≈ 40–70 s/query — slower than bge (20–24 s, 3–6 s after idea 08/81) with no quality gain. Engineering: 2–3 days for steps 1–3, +1 for 4. No GPU, no hosted LLM.

**Risks / open questions**

- A 0.6B model knows little Belgian tax vocabulary; without lexicon few-shots it may emit French-French terms (*URSSAF*). Hallucinated article numbers are the concrete danger — hence append-only plus citation stripping.
- Gains may be nil on A/C and could lower H@1; keep the raw query as a fused leg.
- ggml and torch reranker on 4 cores contend (§3.3); serialise and measure end-to-end latency.
- Gemma licence is not permissive; Phi-4-mini is too slow; the practical family is Qwen3.
- 29–64 questions cannot resolve ±0.02 deltas.

**Verdict**

try-now — a 2–3 day CPU-only A/B of Qwen3-0.6B/1.7B as an append-only keyword rewriter is cheap, private, and builds the exact harness the DeepSeek rewrite (idea 46) will reuse; the reranker role is a skip on this hardware (no French gain over bge, 2–3× slower).

**Sources**

- https://huggingface.co/Qwen/Qwen3-0.6B · https://huggingface.co/Qwen/Qwen3-Reranker-0.6B · https://huggingface.co/ggml-org/Qwen3-Reranker-0.6B-Q8_0-GGUF
- https://huggingface.co/google/gemma-3n-E2B-it · https://huggingface.co/microsoft/Phi-4-mini-instruct
- https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md · https://github.com/ggml-org/llama.cpp/pull/14029 (→ merged #15023, #15824)
- https://arxiv.org/abs/2305.03653 (Jagerman et al.) · https://arxiv.org/abs/2309.08541 (Weller et al.)
- Ideas 06, 08, 11, 34, 46, 49, 52, 69, 72, 81, 86; `experiments/EXPERIMENTS.md` §3.2–3.4, §4.
