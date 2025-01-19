"""Embedding operations for kcli."""
import os
from typing import List

import numpy as np
from litellm import embedding


class Embeddings:
    """Handles text-to-vector conversions using LiteLLM."""

    def __init__(self) -> None:
        """Initialize the embedding model."""
        self.model_name = os.environ.get(
            "KCLI_EMBEDDING_MODEL", "text-embedding-ada-002"
        )
        self.chunk_size = 5000
        try:
            test_embedding = self.create_embeddings("test")
            self.embedding_size = len(test_embedding)
        except Exception as e:
            raise RuntimeError(
                f"Embedding model '{self.model_name}' is not available: {str(e)}"
            ) from e

    def create_embeddings(self, text: str) -> np.ndarray:
        """Generate embeddings for a single text."""
        if len(text) > self.chunk_size:
            return self.batch_embed([text])[0]
        response = embedding(model=self.model_name, input=[text])
        return np.array(response.data[0]["embedding"])

    def create_chunks(
        self,
        text: str,
        chunk_size: int = 1000,
        overlap: int = 200,
    ) -> List[str]:
        """Split text into overlapping chunks.

        Args:
        ----
            text: Text to split into chunks
            chunk_size: Maximum size of each chunk in characters
            overlap: Number of characters to overlap between chunks

        Returns:
        -------
            List of text chunks with overlap
        """
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0
        while start < len(text):
            # Find the end of this chunk
            end = start + chunk_size

            # If this is not the last chunk, try to break at a space
            if end < len(text):
                # Look for the last space within the overlap region
                last_space = text.rfind(" ", start, end)
                if last_space != -1:
                    end = last_space

            chunks.append(text[start:end].strip())

            # Move start to create overlap, but don't go backwards
            start = max(start, end - overlap)

        return chunks

    def batch_embed(self, texts: List[str], overlap: int = 200) -> List[np.ndarray]:
        """Generate embeddings for a list of texts, with chunking.

        Args:
        ----
            texts: List of texts to embed
            overlap: Number of characters to overlap between chunks

        Returns:
        -------
            List of embeddings arrays, one per input text
        """
        all_chunks = []
        chunk_counts = []

        # Create chunks for each text
        for text in texts:
            chunks = self.create_chunks(text, self.chunk_size, overlap)
            all_chunks.extend(chunks)
            chunk_counts.append(len(chunks))

        # Get embeddings for all chunks
        response = embedding(model=self.model_name, input=all_chunks)
        chunk_embeddings = [np.array(item["embedding"]) for item in response.data]

        # Combine chunk embeddings for each original text
        results = []
        start_idx = 0
        for count in chunk_counts:
            if count == 1:
                results.append(chunk_embeddings[start_idx])
            else:
                # Average the embeddings of all chunks for this text
                text_embeddings = chunk_embeddings[start_idx : start_idx + count]
                results.append(np.mean(text_embeddings, axis=0))
            start_idx += count
        return results
embeddings = Embeddings()
