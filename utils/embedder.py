from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Tuple

_model = None


def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks."""
    words = text.split()
    chunks = []

    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i : i + chunk_size])
        if chunk:
            chunks.append(chunk)

    return chunks


def embed_texts(texts: List[str]) -> np.ndarray:
    """Generate embeddings for a list of texts."""
    model = get_model()
    embeddings = model.encode(texts, show_progress_bar=False)
    return embeddings


def create_embeddings(chunks: List[str]) -> List[Tuple[str, np.ndarray]]:
    """Create embeddings for text chunks."""
    if not chunks:
        return []

    embeddings = embed_texts(chunks)
    return list(zip(chunks, embeddings))


if __name__ == "__main__":
    test_texts = ["Hello world", "This is a test", "Embedding texts"]
    embeddings = embed_texts(test_texts)
    print(f"Created {len(embeddings)} embeddings with shape {embeddings[0].shape}")
