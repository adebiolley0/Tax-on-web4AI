# 85 — Observability for the retrieval service (tracing, quality signals, replay)

**Idea**

Instrument every `search`/`fetch` call as one OpenTelemetry trace with a child span per leg (query prep → BM25 → dense/Qdrant → fusion → rerank → response), carrying scrubbed query text, per-leg latency, candidate ids and scores. Export to a self-hosted trace store (Phoenix first), derive online quality signals from the spans (reranker-score distribution, zero-result rate, filter usage, fetch-after-search rank), and replay logged queries through the existing `rag_eval` harness so offline experiments run on real traffic, not only our ~130 hand-written questions.

**Why it fits this project**

- Idea 55 already wants scrubbed query logs and fetch-after-search weak labels; tracing is the same data with structure and a UI.
- `leaderboard.jsonl` records offline metrics only; once hybrid + reranker ships (03) we will not know whether the reranker is the latency hog on the 4-core CPU box, or how often filters (ideas 27/48) return nothing.
- FastMCP has native OTel instrumentation (`tools/call {name}` spans, `gen_ai.tool.name`, context propagation via `_meta.traceparent`), so the tool boundary is free; only the legs inside need spans.
- Privacy: tax questions contain names, national numbers, health facts. Span attributes must be scrubbed *before* export; the scrubbing layer matters more than the tool.

**Evidence**

- FastMCP telemetry: on by default, `FASTMCP_TELEMETRY_MODE=native|propagation_only|off`, OTLP exporter, `traceparent`/`tracestate` propagation. https://gofastmcp.com/servers/telemetry
- FastMCP middleware (`on_call_tool`, `TimingMiddleware`, `StructuredLoggingMiddleware`) for audit records without OTel. https://gofastmcp.com/servers/middleware
- OpenInference span kinds `RETRIEVER`, `RERANKER`, `EMBEDDING`, `TOOL`; attributes `retrieval.documents.N.document.{id,score,content}`, `reranker.{input_documents,output_documents,model_name,top_k}`. https://github.com/Arize-ai/openinference/blob/main/spec/semantic_conventions.md
- Phoenix self-host: single container, SQLite default or Postgres (`PHOENIX_SQL_DATABASE_URL`), OTLP on 6006 (`/v1/traces`) and 4317 gRPC, "no license fees, no usage limits", evals on traces. https://arize.com/docs/phoenix/self-hosting · https://arize.com/docs/phoenix/deployment/configuration
- Langfuse self-host: Postgres + ClickHouse + Redis + S3, MIT core with EE add-ons; OTLP over HTTP only (`/api/public/otel`, Basic auth), no gRPC; built-in data masking. https://langfuse.com/self-hosting · https://langfuse.com/integrations/native/opentelemetry
- MLflow Tracing: `@mlflow.trace`, `RETRIEVER`/`RERANKER` span types, OTel-compatible, PII redaction hooks, lightweight `mlflow-tracing` package. https://mlflow.org/docs/latest/genai/tracing/
- OTel GenAI semconv moved to its own repo; still in development status (unverified, from memory). https://github.com/open-telemetry/semantic-conventions-genai
- Presidio (MIT) for PII detection; French/Dutch coverage via spaCy models and a Belgian national-number recogniser would be ours to add (language support unverified). https://github.com/microsoft/presidio
- Fetch-after-search as implicit relevance: idea 55, `/home/user/Tax-on-web4AI/experiments/ideas/55_query_logs_feedback_loop.md`.

**How we would implement it**

1. **Spans** (½ day): a `tracer.start_as_current_span` per leg in the search pipeline, OpenInference attributes; `retrieval.documents` holds ids + scores only, never content. Trace-level attributes: `session.id` (hashed MCP session), `filters`, `n_results`, `reranker.top_k`.
2. **Scrubbing processor** (1 day): a custom `SpanProcessor.on_end` that runs regex (national number `NN.NNNN.NN-NNN`, IBAN, amounts, emails) then Presidio `fr`/`nl` over query attributes, replaces with `<PII:type>`, and drops raw text when a `strict` flag is set. Unit-test with synthetic questions. Add `OPENINFERENCE_HIDE_*`-style switches (env vars unverified) for production.
3. **Backend** (½ day): Phoenix container on the same box, Postgres, `BatchSpanProcessor` → OTLP gRPC. Retention 30 days.
4. **Signals** (1 day): nightly script queries Phoenix (or reads a parallel JSONL sink) and computes: p50/p95 per leg, zero-result rate by filter, rerank-score histogram (share of top-1 < threshold = "low-confidence answer"), fetch-after-search rank distribution, reformulation chains per session. Write to `experiments/results/online_metrics.jsonl`; Grafana later if needed.
5. **Replay** (1 day): export scrubbed queries + fetched ids as a `Question` set for `rag_eval`; run 01/03 configs against it and append to `leaderboard.jsonl` with `corpus="live"`.

**Expected gain and cost**

No retrieval-metric gain by itself; it makes the reranker's latency and the zero-result/filter failures visible within the first week of traffic, and yields a growing real-query eval set for ideas 55/58/75. Cost ~4 days plus one small container; span overhead is negligible against a CPU cross-encoder.

**Risks / open questions**

- Scrubbing recall: names of small companies and rare dependants will leak past NER; default to `strict` (hash query, keep only leg scores) until Presidio precision is measured on FR/NL.
- GDPR basis for storing even scrubbed questions; retention and access to the Phoenix UI need a policy (idea 70).
- Which reranker-score threshold means "low confidence" is unknown until we see the distribution.

**Verdict**

**try-now** — half a week, reuses FastMCP's built-in OTel, and it is the prerequisite for every usage-based idea (55, 58, 75) and for safe production operation.

**Sources**

URLs inline above; pipeline reference: `/home/user/Tax-on-web4AI/experiments/03_hybrid_rerank/run_hybrid.py`; server: `/home/user/Tax-on-web4AI/mcp_server/src/tax_mcp/server.py`; harness: `/home/user/Tax-on-web4AI/experiments/common/rag_eval/results.py`.
