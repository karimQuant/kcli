"""Tests for kcli."""
import os
import tempfile
from datetime import datetime
from unittest.mock import patch

import numpy as np


def test_add_file() -> None:
    """Tests the add_file function."""
    from kcli.main import Document, add_file
    from kcli.storage import Storage

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp_file:
        tmp_file.write("test content")
        tmp_file_path = tmp_file.name

    doc = add_file(tmp_file_path)
    doc = add_file(tmp_file_path)
    storage = Storage()
    results = storage.query(
        f"SELECT * FROM documents WHERE url = 'file://{tmp_file_path}'"
    )
    assert len(results) == 1
    assert isinstance(doc, Document)
    assert doc.content == "test content"
    assert doc.title == os.path.basename(tmp_file_path)
    assert doc.meta["file_path"] == tmp_file_path
    assert isinstance(doc.created_at, datetime)
    assert doc.embedding is not None
    os.remove(tmp_file_path)


def test_search_knowledge_base() -> None:
    """Test the search_knowledge_base function."""
    from kcli.main import add_file, search_knowledge_base

    # Create temporary files
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp_file1:
        tmp_file1.write("This is the first test document. It contains some keywords.")
        tmp_file_path1 = tmp_file1.name

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp_file2:
        tmp_file2.write("This is the second test document. It also has some keywords.")
        tmp_file_path2 = tmp_file2.name

    # Add files to the knowledge base
    add_file(tmp_file_path1)
    add_file(tmp_file_path2)

    # Search for a query that should match both documents
    search_results = search_knowledge_base("keywords")
    assert (
        f"## {os.path.basename(tmp_file_path1)} (file://{tmp_file_path1})"
        in search_results
    )
    assert (
        "This is the first test document. It contains some keywords." in search_results
    )
    assert (
        f"## {os.path.basename(tmp_file_path2)} (file://{tmp_file_path2})"
        in search_results
    )
    assert (
        "This is the second test document. It also has some keywords." in search_results
    )

    # Search for a query that should match only the first document
    search_results = search_knowledge_base("first test document", limit=1)
    assert (
        f"## {os.path.basename(tmp_file_path1)} (file://{tmp_file_path1})"
        in search_results
    )
    assert (
        "This is the first test document. It contains some keywords." in search_results
    )
    assert (
        f"## {os.path.basename(tmp_file_path2)} (file://{tmp_file_path2})"
        not in search_results
    )

    for i in range(10):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp_file:
            tmp_file.write(f"This is the {i} test document. It also has some keywords.")
            tmp_file_path = tmp_file2.name
        add_file(tmp_file_path)
    # Search for a query that should not match any documents
    search_results = search_knowledge_base(
        "nonexistent query", similarity_threshold=0.9
    )
    assert search_results == ""


def test_crawl_web_content() -> None:
    """Test the crawl_web_content function."""
    from kcli.main import crawl_web_content
    from kcli.storage import Document, Storage

    with patch("kcli.main.process_url") as mock_process_url:
        storage = Storage()
        mock_process_url.return_value = Document(
            content="test content",
            url="https://example.com",
            title="Test Title",
            created_at=datetime.now(),
            embedding=np.ones(storage.embeddings.embedding_size),
            meta={"source": "web"},
        )
        crawl_web_content("https://example.com")
        mock_process_url.assert_called_once_with("https://example.com")

        results = storage.query(
            "SELECT * FROM documents WHERE url = 'https://example.com'"
        )
        assert len(results) == 1
        assert results[0].content == "test content"
        assert results[0].title == "Test Title"
        assert results[0].url == "https://example.com"
        assert (
            results[0].embedding == np.ones(storage.embeddings.embedding_size)
        ).all()
        assert results[0].meta["source"] == "web"
