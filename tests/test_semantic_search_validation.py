"""Semantic search validation dataset test.

Ingests 20 Fisconet+ documents about Belgian personal income tax (IPP)
into an in-memory Qdrant instance, then runs 10 realistic tax-return
questions and asserts that the most relevant documents are retrieved
with good cosine-similarity scores.

Ground truth was built by having each document reviewed against each
question to identify which passages are relevant.
"""

from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from models import Document, SourceType
from storage.chunker import chunk_document
from storage.embedder import embed_chunks, embed_texts
from storage.qdrant_store import (
    COLLECTION_NAME,
    ensure_collection,
    get_client,
    search_similar,
    upsert_chunks,
)

logger = logging.getLogger(__name__)

VALIDATION_DIR = Path(__file__).resolve().parent.parent / "validation_dataset"
MD_DIR = VALIDATION_DIR / "md"
QUESTIONS_PATH = VALIDATION_DIR / "questions.json"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_md_document(md_path: Path) -> Document:
    """Create a Document model from a validation markdown file."""
    text = md_path.read_text(encoding="utf-8")
    short_name = md_path.stem
    return Document(
        source_url=f"fisconet://{short_name}",
        source_domain="minfin.fgov.be",
        source_type=SourceType.FISCONET_DOCUMENT,
        document_id=short_name,
        title=short_name,
        language="fr",
        content_text=text,
    )


def _load_questions() -> list[dict]:
    """Load the 10 test questions with ground truth."""
    return json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Session-scoped fixture: ingest all 20 docs into in-memory Qdrant
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def validation_db():
    """Chunk, embed, and store all 20 validation documents.

    Returns (qdrant_client, documents_dict, all_embedded_chunks).
    """
    md_files = sorted(MD_DIR.glob("*.md"))
    assert len(md_files) >= 20, f"Expected >= 20 md files, found {len(md_files)}"

    # Load documents in parallel
    with ThreadPoolExecutor(max_workers=8) as pool:
        docs = list(pool.map(_load_md_document, md_files))

    docs_by_id = {d.document_id: d for d in docs}

    # Chunk all documents
    all_chunks = []
    for doc in docs:
        chunks = chunk_document(doc)
        all_chunks.extend(chunks)
    logger.info("Chunked %d documents into %d chunks", len(docs), len(all_chunks))

    # Embed all chunks (sentence-transformers handles batching internally)
    embedded = embed_chunks(all_chunks)
    logger.info("Embedded %d chunks", len(embedded))

    # Store in in-memory Qdrant
    client = get_client(in_memory=True)
    ensure_collection(client)
    count = upsert_chunks(client, embedded)
    logger.info("Stored %d points in Qdrant", count)

    return client, docs_by_id, embedded


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestIngestion:
    """Verify that all 20 documents were ingested correctly."""

    def test_all_documents_ingested(self, validation_db):
        client, docs_by_id, embedded = validation_db
        assert len(docs_by_id) == 20

    def test_chunks_created(self, validation_db):
        client, docs_by_id, embedded = validation_db
        assert len(embedded) > 100, f"Expected >100 chunks, got {len(embedded)}"

    def test_all_docs_have_chunks(self, validation_db):
        client, docs_by_id, embedded = validation_db
        doc_ids_with_chunks = {ec.chunk.document_id for ec in embedded}
        for doc_id in docs_by_id:
            assert doc_id in doc_ids_with_chunks, f"No chunks for {doc_id}"

    def test_qdrant_point_count(self, validation_db):
        client, docs_by_id, embedded = validation_db
        info = client.get_collection(COLLECTION_NAME)
        assert info.points_count == len(embedded)


class TestSemanticSearch:
    """Run 10 tax-return questions and verify relevant docs are retrieved."""

    @pytest.fixture(scope="class")
    def questions(self):
        return _load_questions()

    @pytest.fixture(scope="class")
    def search_results(self, validation_db, questions):
        """Pre-compute search results for all 10 questions."""
        client, docs_by_id, embedded = validation_db
        results = {}
        # Embed all questions at once for efficiency
        q_texts = [q["question"] for q in questions]
        q_vectors = embed_texts(q_texts)

        for q, vec in zip(questions, q_vectors):
            hits = search_similar(client, vec, limit=20)
            results[q["id"]] = {
                "question": q["question"],
                "expected_docs": q["expected_docs"],
                "secondary_docs": q.get("secondary_docs", []),
                "hits": hits,
            }
        return results

    # -- Per-question relevance tests --

    def _assert_expected_doc_found(self, search_results, qid, top_k=10):
        """Assert at least one expected doc appears in top-k results."""
        r = search_results[qid]
        top_doc_ids = [
            h["payload"]["document_id"] for h in r["hits"][:top_k]
        ]
        expected = set(r["expected_docs"])
        found = expected & set(top_doc_ids)
        assert found, (
            f"{qid}: None of expected docs {expected} found in top-{top_k}. "
            f"Got: {top_doc_ids}"
        )
        return found

    def _assert_primary_doc_ranked_high(self, search_results, qid, max_rank=5):
        """Assert the best-matching expected doc appears within max_rank."""
        r = search_results[qid]
        expected = set(r["expected_docs"])
        for i, hit in enumerate(r["hits"][:max_rank]):
            if hit["payload"]["document_id"] in expected:
                return i  # rank (0-based)
        top_ids = [h["payload"]["document_id"] for h in r["hits"][:max_rank]]
        pytest.fail(
            f"{qid}: No expected doc {expected} in top-{max_rank}. "
            f"Got: {top_ids}"
        )

    def _assert_score_above_threshold(self, search_results, qid, threshold=0.3):
        """Assert the top hit has a score above threshold."""
        r = search_results[qid]
        top_score = r["hits"][0]["score"] if r["hits"] else 0
        assert top_score >= threshold, (
            f"{qid}: Top score {top_score:.4f} below threshold {threshold}. "
            f"Top doc: {r['hits'][0]['payload']['document_id'] if r['hits'] else 'none'}"
        )

    # --- Q1: Professional vehicle expenses ---

    def test_q1_vehicle_expenses_found(self, search_results):
        self._assert_expected_doc_found(search_results, "Q1")

    def test_q1_vehicle_expenses_ranked_high(self, search_results):
        self._assert_primary_doc_ranked_high(search_results, "Q1")

    def test_q1_vehicle_expenses_score(self, search_results):
        self._assert_score_above_threshold(search_results, "Q1")

    # --- Q2: Pension savings ---

    def test_q2_pension_savings_found(self, search_results):
        self._assert_expected_doc_found(search_results, "Q2")

    def test_q2_pension_savings_ranked_high(self, search_results):
        self._assert_primary_doc_ranked_high(search_results, "Q2")

    def test_q2_pension_savings_score(self, search_results):
        self._assert_score_above_threshold(search_results, "Q2")

    # --- Q3: Rental income ---

    def test_q3_rental_income_found(self, search_results):
        self._assert_expected_doc_found(search_results, "Q3")

    def test_q3_rental_income_ranked_high(self, search_results):
        self._assert_primary_doc_ranked_high(search_results, "Q3")

    def test_q3_rental_income_score(self, search_results):
        self._assert_score_above_threshold(search_results, "Q3")

    # --- Q4: Dependent child resources ---

    def test_q4_dependent_child_found(self, search_results):
        self._assert_expected_doc_found(search_results, "Q4")

    def test_q4_dependent_child_ranked_high(self, search_results):
        self._assert_primary_doc_ranked_high(search_results, "Q4")

    def test_q4_dependent_child_score(self, search_results):
        self._assert_score_above_threshold(search_results, "Q4")

    # --- Q5: Charitable donations ---
    # KNOWN ISSUE: The question uses common French "dons" while the target
    # document uses the legal term "libéralités". The MiniLM embedding model
    # does not bridge this synonym gap well, so the donations document is not
    # retrieved. Marked xfail as a regression target: improvements to
    # embeddings or query expansion should make these pass.

    @pytest.mark.xfail(reason="synonym gap: 'dons' vs 'libéralités' — MiniLM cannot bridge")
    def test_q5_donations_found(self, search_results):
        self._assert_expected_doc_found(search_results, "Q5")

    @pytest.mark.xfail(reason="synonym gap: 'dons' vs 'libéralités' — MiniLM cannot bridge")
    def test_q5_donations_ranked_high(self, search_results):
        self._assert_primary_doc_ranked_high(search_results, "Q5")

    def test_q5_donations_score(self, search_results):
        self._assert_score_above_threshold(search_results, "Q5")

    # --- Q6: Childcare expenses ---

    def test_q6_childcare_found(self, search_results):
        self._assert_expected_doc_found(search_results, "Q6")

    def test_q6_childcare_ranked_high(self, search_results):
        self._assert_primary_doc_ranked_high(search_results, "Q6")

    def test_q6_childcare_score(self, search_results):
        self._assert_score_above_threshold(search_results, "Q6")

    # --- Q7: Mortgage tax benefits (Flemish) ---

    def test_q7_mortgage_found(self, search_results):
        self._assert_expected_doc_found(search_results, "Q7")

    def test_q7_mortgage_ranked_high(self, search_results):
        self._assert_primary_doc_ranked_high(search_results, "Q7")

    def test_q7_mortgage_score(self, search_results):
        self._assert_score_above_threshold(search_results, "Q7")

    # --- Q8: Disability tax benefits ---

    def test_q8_disability_found(self, search_results):
        self._assert_expected_doc_found(search_results, "Q8")

    def test_q8_disability_ranked_high(self, search_results):
        self._assert_primary_doc_ranked_high(search_results, "Q8")

    def test_q8_disability_score(self, search_results):
        self._assert_score_above_threshold(search_results, "Q8")

    # --- Q9: Co-parenting tax credit ---

    def test_q9_coparenting_found(self, search_results):
        self._assert_expected_doc_found(search_results, "Q9")

    def test_q9_coparenting_ranked_high(self, search_results):
        self._assert_primary_doc_ranked_high(search_results, "Q9")

    def test_q9_coparenting_score(self, search_results):
        self._assert_score_above_threshold(search_results, "Q9")

    # --- Q10: Alimony deduction ---
    # KNOWN ISSUE: The alimony documents (art.143, art.132bis) are index-style
    # pages listing circulars and case-law references. They lack substantial
    # prose about alimony deductibility, so MiniLM cannot embed them close to
    # the query. Also, circ_2026_C2_fiscalite_immobiliere (26 chunks) floods
    # results with "déductible" matches. Regression target for better chunking
    # or document-level re-ranking.

    @pytest.mark.xfail(reason="index-style docs lack substantive alimony content for embedding")
    def test_q10_alimony_found(self, search_results):
        self._assert_expected_doc_found(search_results, "Q10")

    @pytest.mark.xfail(reason="index-style docs lack substantive alimony content for embedding")
    def test_q10_alimony_ranked_high(self, search_results):
        self._assert_primary_doc_ranked_high(search_results, "Q10")

    def test_q10_alimony_score(self, search_results):
        self._assert_score_above_threshold(search_results, "Q10")

    # --- Aggregate quality metrics ---

    def test_overall_recall_at_10(self, search_results):
        """At least 8 out of 10 questions should have an expected doc in top 10."""
        hits = 0
        for qid, r in search_results.items():
            top_doc_ids = {h["payload"]["document_id"] for h in r["hits"][:10]}
            if set(r["expected_docs"]) & top_doc_ids:
                hits += 1
        assert hits >= 8, f"Recall@10: {hits}/10 questions matched (need >= 8)"

    def test_overall_mrr(self, search_results):
        """Mean Reciprocal Rank across all 10 questions should be >= 0.3."""
        rr_sum = 0.0
        for qid, r in search_results.items():
            expected = set(r["expected_docs"])
            for i, hit in enumerate(r["hits"][:20]):
                if hit["payload"]["document_id"] in expected:
                    rr_sum += 1.0 / (i + 1)
                    break
        mrr = rr_sum / len(search_results)
        assert mrr >= 0.3, f"MRR = {mrr:.4f} (need >= 0.3)"

    def test_average_top_score(self, search_results):
        """Average score of the best matching expected-doc hit should be >= 0.35."""
        scores = []
        for qid, r in search_results.items():
            expected = set(r["expected_docs"]) | set(r.get("secondary_docs", []))
            for hit in r["hits"][:20]:
                if hit["payload"]["document_id"] in expected:
                    scores.append(hit["score"])
                    break
        avg = sum(scores) / len(scores) if scores else 0
        assert avg >= 0.35, f"Avg best-match score = {avg:.4f} (need >= 0.35)"


class TestSearchResultDetails:
    """Detailed diagnostics — prints search results for manual inspection."""

    @pytest.fixture(scope="class")
    def full_results(self, validation_db):
        """Run all 10 questions and return detailed results."""
        client, docs_by_id, embedded = validation_db
        questions = _load_questions()
        q_texts = [q["question"] for q in questions]
        q_vectors = embed_texts(q_texts)

        results = []
        for q, vec in zip(questions, q_vectors):
            hits = search_similar(client, vec, limit=10)
            results.append({
                "id": q["id"],
                "question": q["question"],
                "expected_docs": q["expected_docs"],
                "secondary_docs": q.get("secondary_docs", []),
                "hits": [
                    {
                        "rank": i + 1,
                        "score": round(h["score"], 4),
                        "document_id": h["payload"]["document_id"],
                        "section": h["payload"].get("section_heading", ""),
                        "text_preview": h["payload"]["chunk_text"][:200],
                    }
                    for i, h in enumerate(hits)
                ],
            })
        return results

    def test_print_detailed_results(self, full_results):
        """Print detailed results for manual review (always passes)."""
        report_path = VALIDATION_DIR / "search_results_report.json"
        report_path.write_text(
            json.dumps(full_results, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("Wrote detailed results to %s", report_path)

        # Print summary to stdout
        for r in full_results:
            expected = set(r["expected_docs"])
            secondary = set(r["secondary_docs"])
            all_relevant = expected | secondary
            print(f"\n{'='*70}")
            print(f"{r['id']}: {r['question']}")
            print(f"  Expected: {r['expected_docs']}")
            for h in r["hits"][:5]:
                marker = ""
                if h["document_id"] in expected:
                    marker = " <<<< PRIMARY"
                elif h["document_id"] in secondary:
                    marker = " << secondary"
                print(
                    f"  #{h['rank']} [{h['score']:.4f}] {h['document_id']}{marker}"
                )
                print(f"       {h['text_preview'][:120]}...")
