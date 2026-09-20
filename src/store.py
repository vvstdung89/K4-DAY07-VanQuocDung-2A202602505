from __future__ import annotations

from typing import Any, Callable

from .chunking import compute_similarity
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    In-memory only: the ChromaDB branch is intentionally not used (no test needs
    it, it is not in requirements.txt, and the starter set _use_chroma = True
    before any client existed).
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

    def _make_record(self, doc: Document) -> dict[str, Any]:
        # Copy metadata: khong giu tham chieu toi dict cua nguoi goi.
        metadata = dict(doc.metadata or {})
        # delete_document() phu thuoc vao khoa nay. Voi chunk "file#3" thi
        # doc_id phai tro ve file goc, nen chi set khi caller chua khai bao.
        metadata.setdefault("doc_id", doc.id)

        record = {
            "index": self._next_index,
            "id": doc.id,
            "content": doc.content,
            "metadata": metadata,
            "embedding": self._embedding_fn(doc.content),
        }
        self._next_index += 1
        return record

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        if not records or top_k <= 0:
            return []

        query_embedding = self._embedding_fn(query)
        scored = [
            {
                "id": record["id"],
                "content": record["content"],
                "metadata": record["metadata"],
                "score": compute_similarity(query_embedding, record["embedding"]),
            }
            for record in records
        ]
        scored.sort(key=lambda result: result["score"], reverse=True)
        return scored[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """Embed each document's content and store it."""
        for doc in docs:
            self._store.append(self._make_record(doc))

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Find the top_k most similar chunks to query."""
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        Loc TRUOC roi moi search: neu lay top-k truoc roi bo cai khong khop thi
        co the con 0 ket qua du store van con tai lieu hop le.
        """
        if not metadata_filter:
            candidates = self._store
        else:
            candidates = [
                record
                for record in self._store
                if all(record["metadata"].get(key) == value for key, value in metadata_filter.items())
            ]
        return self._search_records(query, candidates, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """Remove all chunks belonging to a document."""
        remaining = [record for record in self._store if record["metadata"].get("doc_id") != doc_id]
        if len(remaining) == len(self._store):
            return False
        self._store = remaining
        return True
