import pytest
from app.rag.chunking import split_markdown_by_headings, chunk_text
from app.rag.retriever import compute_rrf, cosine_similarity


def test_markdown_heading_split():
    md = "# Heading 1\nContent 1\n\n## Subheading 1.1\nContent 1.1"
    sections = split_markdown_by_headings(md)
    assert len(sections) == 2
    assert sections[0]["heading"] == "Heading 1"
    assert "Content 1" in sections[0]["text"]
    assert sections[1]["heading"] == "Subheading 1.1"


def test_chunk_text_size_and_overlap():
    sections = [{"heading": "Prices", "text": "A" * 1500}]
    chunks = chunk_text(sections, chunk_size=800, chunk_overlap=100)
    assert len(chunks) >= 2
    for c in chunks:
        assert c["heading"] == "Prices"
        assert len(c["content"]) <= 1000


def test_cosine_similarity():
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    assert pytest.approx(cosine_similarity(v1, v2)) == 1.0

    v3 = [0.0, 1.0, 0.0]
    assert pytest.approx(cosine_similarity(v1, v3)) == 0.0


def test_rrf_scoring():
    vec_ranks = {"doc_a": 1, "doc_b": 2}
    kw_ranks = {"doc_a": 2, "doc_b": 1}
    scores = compute_rrf(vec_ranks, kw_ranks, k=60)
    assert "doc_a" in scores
    assert "doc_b" in scores
    assert scores["doc_a"] > 0
    assert pytest.approx(scores["doc_a"]) == pytest.approx(scores["doc_b"])
