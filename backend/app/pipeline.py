"""Orchestrates acquisition -> embeddings -> FAISS, and keeps the index fresh."""
import logging
import re
import threading
from datetime import datetime, timezone

from . import acquisition, config
from .acquisition import Chunk
from .embeddings import embed
from .vector_store import VectorStore

log = logging.getLogger("rag.pipeline")

NAME_TOKENS = re.compile(
    r"\b(?:" + "|".join(map(re.escape, config.PERSON_NAME.split())) + r")(?:'s|’s)?\s*", re.I
)


class RagPipeline:
    def __init__(self) -> None:
        self._store: VectorStore | None = None
        self._build_lock = threading.Lock()
        self._stop = threading.Event()
        self._watcher: threading.Thread | None = None
        self.last_error: str | None = None

    # --- indexing -----------------------------------------------------------
    def rebuild(self) -> VectorStore:
        """Re-run the whole pipeline and atomically swap in the new index."""
        with self._build_lock:
            chunks, fingerprint, sources = acquisition.acquire()
            vectors = embed([chunk.embedding_text() for chunk in chunks])
            meta = {
                "fingerprint": fingerprint,
                "sources": sources,
                "embedding_model": config.EMBEDDING_MODEL,
                "indexed_at": datetime.now(timezone.utc).isoformat(),
            }
            store = VectorStore.build(vectors, chunks, meta)
            store.save(config.STORAGE_DIR)
            self._store = store
            self.last_error = None
            log.info("Indexed %d chunks from %s", len(chunks), ", ".join(sources))
            return store

    def start(self) -> None:
        """Load the persisted index if it still matches the sources, else build it."""
        try:
            current = acquisition.fingerprint(acquisition.source_files())
            saved = VectorStore.load(config.STORAGE_DIR)
            if (
                saved
                and saved.meta.get("fingerprint") == current
                and saved.meta.get("embedding_model") == config.EMBEDDING_MODEL
            ):
                self._store = saved
                log.info("Loaded persisted index (%d chunks)", len(saved.chunks))
            else:
                self.rebuild()
        except Exception as error:  # keep the API up; the watcher will retry
            self.last_error = str(error)
            log.exception("Initial indexing failed")
        self._watcher = threading.Thread(target=self._watch, name="rag-watcher", daemon=True)
        self._watcher.start()

    def stop(self) -> None:
        self._stop.set()

    def _watch(self) -> None:
        """Poll the source documents and re-index as soon as their content changes."""
        while not self._stop.wait(config.WATCH_INTERVAL_SECONDS):
            try:
                current = acquisition.fingerprint(acquisition.source_files())
                if self._store is None or current != self._store.meta["fingerprint"]:
                    log.info("Source documents changed - re-indexing")
                    self.rebuild()
            except Exception as error:  # e.g. file mid-write; retry on the next tick
                self.last_error = str(error)
                log.warning("Re-index attempt failed: %s", error)

    # --- querying -----------------------------------------------------------
    @property
    def ready(self) -> bool:
        return self._store is not None

    def search(self, query: str, top_k: int = config.TOP_K) -> list[tuple[Chunk, float]]:
        store = self._store
        if store is None:
            raise RuntimeError(self.last_error or "The knowledge base is still being built.")
        # Every chunk is about the same person, so their name only adds noise
        # (it pulls every question towards the contact block).
        cleaned = NAME_TOKENS.sub("", query).strip() or query
        return store.search(embed([cleaned])[0], top_k)

    def status(self) -> dict:
        store = self._store
        return {
            "ready": store is not None,
            "chunks": len(store.chunks) if store else 0,
            "sources": store.meta["sources"] if store else [],
            "indexed_at": store.meta["indexed_at"] if store else None,
            "fingerprint": store.meta["fingerprint"][:12] if store else None,
            "embedding_model": config.EMBEDDING_MODEL,
            "answer_mode": "llm" if config.LLM_ENABLED else "extractive",
            "error": self.last_error,
        }


pipeline = RagPipeline()
