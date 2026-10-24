from pathlib import Path
from app.services.ai.rag import KnowledgeBase, _chunk, _tokens


def test_chunk_basic():
    """Chunking should split text into overlapping chunks of the given size."""
    text = "abcdefghijklmnopqrstuvwxyz"
    chunks = _chunk(text, size=10, overlap=5)
    assert len(chunks) > 1
    assert chunks[0] == "abcdefghij"
    assert chunks[1] == "fghijklmno"


def test_chunk_empty():
    """Empty text should produce no chunks."""
    assert _chunk("") == []


def test_chunk_shorter_than_size():
    """Text shorter than chunk size should return a single chunk."""
    chunks = _chunk("hello", size=100, overlap=5)
    assert chunks == ["hello"]


def test_tokens_basic():
    """Tokenization should extract lowercase alphanumeric tokens."""
    tokens = _tokens("Hello, World! 123")
    assert tokens == {"hello", "world", "123"}


def test_tokens_empty():
    """Empty text should produce no tokens."""
    assert _tokens("") == set()


def test_knowledge_base_retrieve():
    """KnowledgeBase.retrieve should return relevant chunks for a query."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        docs_dir = Path(tmpdir)
        (docs_dir / "test.md").write_text(
            "OpenSSH is a secure shell protocol used for remote login."
        )
        kb = KnowledgeBase(docs_dir=docs_dir)
        results = kb.retrieve("OpenSSH")
        assert len(results) > 0
        assert any("OpenSSH" in chunk for chunk in results)


def test_knowledge_base_retrieve_no_match():
    """Query with no matching tokens should return empty results."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        docs_dir = Path(tmpdir)
        (docs_dir / "test.md").write_text("OpenSSH security")
        kb = KnowledgeBase(docs_dir=docs_dir)
        results = kb.retrieve("apache nginx")
        assert results == []


def test_knowledge_base_empty():
    """KnowledgeBase with no docs should return empty results."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        docs_dir = Path(tmpdir)
        kb = KnowledgeBase(docs_dir=docs_dir)
        results = kb.retrieve("anything")
        assert results == []