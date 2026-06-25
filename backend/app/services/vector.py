from abc import ABC, abstractmethod
from typing import Any
import chromadb
from app.core.config import settings

class VectorStoreService(ABC):
    """Abstract Base Class for Vector DB interactions (ChromaDB, etc.)."""

    @abstractmethod
    async def add_documents(
        self, collection_name: str, documents: list[str], ids: list[str], metadatas: list[dict[str, Any]] | None = None
    ) -> None:
        """Adds documents to the specified collection."""
        pass

    @abstractmethod
    async def query(
        self, collection_name: str, query_texts: list[str], n_results: int = 5, where: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Queries the vector database for matching documents."""
        pass


class ChromaVectorStoreService(VectorStoreService):
    """Concrete implementation of VectorStoreService using ChromaDB."""

    def __init__(self) -> None:
        # Chroma HTTP client or Persistent Client based on environment config
        self.client = chromadb.HttpClient(
            host=settings.CHROMADB_HOST,
            port=settings.CHROMADB_PORT
        )

    async def add_documents(
        self, collection_name: str, documents: list[str], ids: list[str], metadatas: list[dict[str, Any]] | None = None
    ) -> None:
        """Adds documents to Chroma DB collection."""
        collection = self.client.get_or_create_collection(name=collection_name)
        collection.add(
            documents=documents,
            ids=ids,
            metadatas=metadatas
        )

    async def query(
        self, collection_name: str, query_texts: list[str], n_results: int = 5, where: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Queries Chroma DB collection."""
        collection = self.client.get_or_create_collection(name=collection_name)
        results = collection.query(
            query_texts=query_texts,
            n_results=n_results,
            where=where
        )
        return dict(results)
