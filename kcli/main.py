"""Core logic for kcli."""
import asyncio
import os
from datetime import datetime
from typing import Optional
from rich.table import Table
from kcli.crawler import process_url
from kcli.embeddings import embeddings
from kcli.log import console
from kcli.storage import Document, Storage
from rich import box

storage = Storage()


def add_file(file_path: str) -> Document:
    """Add a local file to the knowledge base."""
    abs_path = os.path.abspath(file_path)
    with open(abs_path) as f:
        content = f.read()
    embedding = embeddings.create_embeddings(content)
    doc = Document(
        content=content,
        url=f"file://{abs_path}",
        title=os.path.basename(abs_path),
        created_at=datetime.now(),
        embedding=embedding,
        meta={"file_path": abs_path},
    )
    storage.add(doc)
    return doc


def search_knowledge_base(
    query: str, limit: int = 10, similarity_threshold: Optional[float] = None
) -> str | None:
    """Search the knowledge base."""
    results = storage.search(
        query, limit=limit, similarity_threshold=similarity_threshold
    )
    if not results:
        return None
    table_result = Table(
        title=f"({len(results)}) Search Results",
        header_style="bold magenta",
        show_lines=True,
    )
    table_result.add_column("date", justify="right", style="dim")
    table_result.add_column("Title", justify="left", style="cyan")
    table_result.add_column("Content", justify="left", min_width=60)
    for _, doc in enumerate(results):
        table_result.add_row(
            doc.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            doc.title,
            doc.content[:50],
        )
    return table_result


def crawl_web_content(url: str) -> None:
    """Crawl and add web content to knowledge base."""
    doc = asyncio.run(process_url(url))
    if doc:
        storage.add(doc)
    else:
        console.log(f"Failed to crawl {url}")


def get_knowledge_base_stats() -> None:
    """Display knowledge base statistics."""
    # TODO: Implement storage.get_stats()
    pass
