"""Handles storage operations for kcli."""
import json
import os
import pathlib
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import hnswlib
import numpy as np

from kcli.embeddings import Embeddings
from kcli.log import console

storage = None
embedding = None

VECTOR_DIM: Optional[int] = None
DB_PATH: Optional[str] = None
INDEX_PATH: Optional[str] = None


def configure() -> None:
    """Configure the storage."""
    global embedding
    global VECTOR_DIM
    global DB_PATH
    global INDEX_PATH

    DB_PATH = os.environ.get(
        "KCLI_DB_PATH", f"{pathlib.Path.home()}/.config/kcli.sqlite"
    )
    INDEX_PATH = os.environ.get(
        "KCLI_INDEX_PATH", f"{pathlib.Path.home()}/.config/kcli.index.ann"
    )
    if not os.path.exists(DB_PATH):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    embedding = Embeddings()
    VECTOR_DIM = embedding.embedding_size


@dataclass
class Document:
    """Represents a document with its content and metadata."""
    content: str
    url: Optional[str]
    title: str
    created_at: datetime
    embedding: Optional[np.ndarray]
    meta: Dict[str, Any]


class Storage:
    """Handles storage operations for kcli."""

    def __init__(self: "Storage") -> None:
        """Initialize the storage."""
        global DB_PATH
        global INDEX_PATH
        global VECTOR_DIM
        if not DB_PATH:
            configure()

        self.db_path = DB_PATH
        self.index_path = INDEX_PATH

        # Initialize SQLite connection
        self.db = sqlite3.connect(self.db_path)
        self._create_table()
        # Initialize hnswlib index
        self.index = hnswlib.Index(space="cosine", dim=VECTOR_DIM)
        if os.path.exists(self.index_path):
            self.index.load_index(self.index_path)
        else:
            self.index.init_index(max_elements=10000, ef_construction=200, M=16)
        self.embeddings = Embeddings()

    def _create_table(self: "Storage") -> None:
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT,
                url TEXT,
                title TEXT,
                created_at TEXT,
                embedding float[768],
                meta TEXT
            );
            """
        )

    def query(self: "Storage", query: str) -> List[Document]:
        """Search for a query in the knowledge base."""
        cursor = self.db.cursor()  # Use existing connection
        cursor.execute(query)
        rows = cursor.fetchall()
        docs = []
        for row in rows:
            docs.append(
                Document(
                    content=row[1],
                    url=row[2],
                    title=row[3],
                    created_at=datetime.fromisoformat(row[4]),
                    embedding=np.array(json.loads(row[5])),
                    meta=eval(row[6]) if row[6] else {},
                )
            )
        return docs

    def add(self: "Storage", doc: Document) -> None:
        """Add a document to the storage.

        Args:
        ----
            doc: The document to add to storage
        """
        # First add to SQLite
        cursor = self.db.cursor()
        cursor.execute("SELECT id FROM documents WHERE content = ?", (doc.content,))
        existing_doc = cursor.fetchone()
        if existing_doc:
            console.log("Document already in the database, skipping.")
            return
        cursor.execute(
            """
            INSERT INTO documents (content, url, title, created_at, embedding, meta)
            VALUES (?, ?, ?, ?, ?, ?)
            RETURNING id
            """,
            (
                doc.content,
                doc.url,
                doc.title,
                doc.created_at.isoformat(),
                json.dumps(np.array(doc.embedding).tolist())
                if doc.embedding is not None
                else None,
                str(doc.meta),
            ),
        )
        doc_id = cursor.fetchone()[0]
        self.db.commit()

        # Then add to hnswlib index
        if doc.embedding is not None:
            self.index.add_items(np.array([doc.embedding]), np.array([doc_id]))
            self.index.save_index(self.index_path)
        console.log(f"Document inserted: {doc_id}")

    def _brut_force_search(
        self: "Storage", query: str, limit: int = 10, similarity_threshold: Optional[float] = None
    ) -> List[Document]:
        query_embedding = self.embeddings.create_embeddings(query)
        # Fetch all documents from SQLite
        cursor = self.db.cursor()
        cursor.execute("SELECT id, content, embedding FROM documents")
        rows = cursor.fetchall()

        # Calculate cosine similarity for each document
        similarities = []
        for row in rows:
            doc_id, content, embedding = row
            if embedding is not None:
                embedding = np.array(json.loads(embedding))
                similarity = np.dot(query_embedding, embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(embedding)
                )
                if similarity_threshold is None or similarity >= similarity_threshold:
                    similarities.append((doc_id, similarity))

        # Sort by similarity and get top results
        similarities.sort(key=lambda x: x[1], reverse=True)
        top_results = similarities[:limit]

        # Fetch documents from SQLite
        doc_ids = [doc_id for doc_id, _ in top_results]
        placeholders = ",".join("?" * len(doc_ids))
        cursor.execute(
            f"""
            SELECT content, url, title, created_at, embedding, meta
            FROM documents
            WHERE id IN ({placeholders})
            """,
            doc_ids,
        )
        rows = cursor.fetchall()
        return [
            Document(
                content=row[0],
                url=row[1],
                title=row[2],
                created_at=datetime.fromisoformat(row[3]),
                embedding=np.array(json.loads(row[4])) if row[4] else None,
                meta=row[5] if row[5] else {},
            )
            for row in rows
        ]

    def search(
        self: "Storage", query: str, limit: int = 10, similarity_threshold: Optional[float] = None
    ) -> List[Document]:
        """Search for a query in the knowledge base."""
        if self.index.element_count > 100:
            return self._hnsw_search(query, limit, similarity_threshold)
        else:
            return self._brut_force_search(query, limit, similarity_threshold)

    def _hnsw_search(
        self: "Storage", query: str, limit: int = 10, similarity_threshold: Optional[float] = None
    ) -> List[Document]:
        query_embedding = self.embeddings.create_embeddings(query)
        max(1, min(limit, self.index.element_count - 1))
        # Search in hnswlib index
        try:
            labels, distances = self.index.knn_query(query_embedding, k=limit)
            # filter results based on similarity threshold
            if similarity_threshold is not None:
                filtered_results = [
                    label
                    for label, distance in zip(labels[0], distances[0])
                    if 1 - distance >= similarity_threshold
                ]
            else:
                filtered_results = labels[0]
            doc_ids = filtered_results.tolist()
        except RuntimeError as err:
            if "M is too small" in err.args[0]:
                console.log("Not enough data to do search returning all the documents")
                doc_ids = self.index.get_ids_list()
            else:
                raise err
        # Fetch documents from SQLite
        placeholders = ",".join("?" * len(doc_ids))
        cursor = self.db.cursor()
        cursor.execute(
            f"""
            SELECT content, url, title, created_at, embedding, meta
            FROM documents
            WHERE id IN ({placeholders})
            """,
            doc_ids,
        )
        rows = cursor.fetchall()
        return [
            Document(
                content=row[0],
                url=row[1],
                title=row[2],
                created_at=datetime.fromisoformat(row[3]),
                embedding=np.array(json.loads(row[4])) if row[4] else None,
                meta=row[5] if row[5] else {},
            )
            for row in rows
        ]

    def close(self: "Storage") -> None:
        """Close database connection."""
        self.db.close()

    def __enter__(self: "Storage") -> "Storage":
        """Enter the context manager."""
        return self

    def __exit__(
        self: "Storage", exc_type: type, exc_val: Exception, exc_tb: str
    ) -> None:
        """Exit the context manager, closing connections.

        Args:
        ----
            exc_type: The type of the exception that was raised
            exc_val: The instance of the exception that was raised
            exc_tb: The traceback of the exception that was raised
        """
        """Close database connection and save index."""
        self.close()
        if hasattr(self, "index"):
            self.index.save_index(self.index_path)


if __name__ == "__main__":
    storage = Storage()
    storage.add(Document("test", "test", "test", datetime.now(), np.array([1, 2, 3]), {}))
