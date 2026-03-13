import numpy as np
from typing import List, Tuple, Optional


class VectorStore:
    def __init__(self):
        self.chunks: List[str] = []
        self.embeddings: List[np.ndarray] = []

    def add(self, chunks: List[str], embeddings: List[np.ndarray]):
        """Add chunks and their embeddings to the store."""
        self.chunks.extend(chunks)
        self.embeddings.extend(embeddings)

    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[str]:
        """Search for most similar chunks to the query embedding."""
        if not self.embeddings:
            return []

        query_embedding = query_embedding.reshape(1, -1)
        embeddings_matrix = np.array(self.embeddings)

        similarities = np.dot(embeddings_matrix, query_embedding.T).flatten()

        top_indices = np.argsort(similarities)[-top_k:][::-1]

        return [self.chunks[i] for i in top_indices if similarities[i] > 0.1]

    def is_empty(self) -> bool:
        """Check if the vector store is empty."""
        return len(self.chunks) == 0


if __name__ == "__main__":
    store = VectorStore()
    print("VectorStore initialized")
