"""Core logic for kcli."""
import os
from datetime import datetime
from kcli.embeddings import embeddings
from kcli.storage import Storage, Document
from kcli.crawler import process_url
import asyncio
import logging
from kcli.log import console

storage = Storage()

def add_file(file_path: str) -> Document:
    """Add a local file to the knowledge base."""
    abs_path = os.path.abspath(file_path)
    with open(abs_path, 'r') as f:
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

def search_knowledge_base(query: str, limit: int = 10, similarity_threshold = None) -> str:
    """Search the knowledge base."""
    results = storage.search(query, limit=limit, similarity_threshold=similarity_threshold)
    output = ""
    for doc in results:
        output += f"## {doc.title} ({doc.url})\n\n"
        output += f"{doc.content}\n\n---\n\n"
    console.log(f"Search query: {query}, results: {len(results)}")
    return output

def crawl_web_content(url: str):
    """Crawl and add web content to knowledge base."""
    doc = asyncio.run(process_url(url))
    if doc:
        storage.add(doc)
    else:
        console.log(f"Failed to crawl {url}")

def get_knowledge_base_stats():
    """Display knowledge base statistics."""
    # TODO: Implement storage.get_stats()
    pass
