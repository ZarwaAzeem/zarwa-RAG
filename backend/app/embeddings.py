"""Sentence-transformer embeddings."""
from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer

from . import config


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    return SentenceTransformer(config.EMBEDDING_MODEL)


def embed(texts: list[str]) -> np.ndarray:
    """L2-normalised float32 vectors, so inner product equals cosine similarity."""
    vectors = get_model().encode(
        texts, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False
    )
    return np.asarray(vectors, dtype="float32")
