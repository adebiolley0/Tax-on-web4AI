from rag_eval.chunking import article_chunks, fixed_chunks, whole_doc


def test_whole_doc(toy_docs):
    ch = whole_doc(toy_docs)
    assert [c.chunk_id for c in ch] == ["docA#0", "docB#0"]
    assert ch[0].title == "Document A" and ch[0].meta["heading_path"] == ["Livre I", "Chapitre 2"]
    assert ch[0].meta is not toy_docs[0].meta
    assert len(whole_doc(toy_docs, max_chars=50)[0].text) == 50


def test_fixed_chunks_respect_budget_and_cover_text(toy_docs):
    ch = fixed_chunks(toy_docs, max_chars=500, overlap=60)
    ids = [c.chunk_id for c in ch]
    assert len(ids) == len(set(ids)) and all(c.doc_id in ("docA", "docB") for c in ch)
    a = [c for c in ch if c.doc_id == "docA"]
    assert len(a) >= 3
    assert all(len(c.text) <= 500 + 60 + 1 for c in a)
    assert "Dernier paragraphe court." in "".join(c.text for c in a)
    assert "## Section 2" in "".join(c.text for c in a)
    assert [c.text for c in ch if c.doc_id == "docB"] == ["Un tout petit document."]
    pref = fixed_chunks(toy_docs, max_chars=500, overlap=0, prefix_title=True)
    assert all(c.text.startswith("Document A\n\n") for c in pref if c.doc_id == "docA")
    single = fixed_chunks(toy_docs, max_chars=100_000)
    assert len(single) == 2


def test_article_chunks_prefix_context(toy_docs):
    ch = article_chunks(toy_docs, max_chars=600, overlap=50)
    a = [c for c in ch if c.doc_id == "docA"]
    assert len(a) > 1 and all(c.text.startswith("Document A\nLivre I > Chapitre 2\n\n") for c in a)
    b = [c for c in ch if c.doc_id == "docB"]
    assert b[0].text == "Document B\n\nUn tout petit document."
    assert article_chunks(toy_docs, prefix_context=False)[-1].text == "Un tout petit document."
