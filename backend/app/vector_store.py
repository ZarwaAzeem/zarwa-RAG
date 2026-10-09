"""FAISS vector database with on-disk persistence."""
import json
from pathlib import Path

import faiss
import numpy as np

from .acquisition import Chunk

INDEX_FILE = "index.faiss"
META_FILE = "chunks.json"


class VectorStore:
    def __init__(self, index: faiss.Index, chunks: list[Chunk], meta: dict):
        self.index = index
        self.chunks = chunks
        self.meta = meta

    @classmethod
    def build(cls, vectors: np.ndarray, chunks: list[Chunk], meta: dict) -> "VectorStore":
        index = faiss.IndexFlatIP(vectors.shape[1])
        index.add(vectors)
        return cls(index, chunks, meta)

    def search(self, query_vector: np.ndarray, top_k: int) -> list[tuple[Chunk, float]]:
        scores, ids = self.index.search(query_vector.reshape(1, -1), min(top_k, len(self.chunks)))
        return [
            (self.chunks[i], float(score)) for score, i in zip(scores[0], ids[0]) if i != -1
        ]

    def save(self, directory: Path) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(directory / INDEX_FILE))
        payload = {"meta": self.meta, "chunks": [chunk.to_dict() for chunk in self.chunks]}
        (directory / META_FILE).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, directory: Path) -> "VectorStore | None":
        index_path, meta_path = directory / INDEX_FILE, directory / META_FILE
        if not (index_path.is_file() and meta_path.is_file()):
            return None
        payload = json.loads(meta_path.read_text(encoding="utf-8"))
        chunks = [Chunk(**chunk) for chunk in payload["chunks"]]
        return cls(faiss.read_index(str(index_path)), chunks, payload["meta"])
