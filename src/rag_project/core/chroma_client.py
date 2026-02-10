"""
ChromaDB client management — singleton pattern with proper lifecycle.
"""

from __future__ import annotations

from typing import Optional

import chromadb
from chromadb.utils import embedding_functions

from ..config import settings
from ..logging_config import get_logger

logger = get_logger("chroma")


class ChromaManager:
    """Manages ChromaDB client and collection access."""

    def __init__(self, db_path: Optional[str] = None, api_key: Optional[str] = None):
        self._db_path = db_path or str(settings.chroma_db_path)
        self._api_key = api_key or settings.openai_api_key
        self._client: Optional[chromadb.ClientAPI] = None
        self._embedder = None

    @property
    def client(self) -> chromadb.ClientAPI:
        if self._client is None:
            logger.info("Initializing ChromaDB client at %s", self._db_path)
            self._client = chromadb.PersistentClient(path=self._db_path)
        return self._client

    @property
    def embedder(self):
        if self._embedder is None:
            self._embedder = embedding_functions.OpenAIEmbeddingFunction(
                api_key=self._api_key,
                model_name=settings.embedding_model,
            )
        return self._embedder

    def get_collection(self, name: str):
        """Get a collection with the configured embedding function."""
        return self.client.get_collection(name, embedding_function=self.embedder)

    def get_or_create_collection(self, name: str):
        """Get or create a collection."""
        return self.client.get_or_create_collection(name, embedding_function=self.embedder)

    def delete_collection(self, name: str) -> bool:
        """Delete a collection if it exists. Returns True if deleted."""
        try:
            self.client.delete_collection(name=name)
            logger.info("Deleted collection: %s", name)
            return True
        except (ValueError, Exception):
            return False

    def list_collections(self) -> list:
        """List all collection names."""
        return [c.name for c in self.client.list_collections()]

    def get_auth_collection(self):
        return self.get_collection(settings.coll_auth)

    def get_draft_collection(self):
        return self.get_collection(settings.coll_draft)


# Singleton instance
_manager: Optional[ChromaManager] = None


def get_chroma_manager() -> ChromaManager:
    """Get the singleton ChromaManager instance."""
    global _manager
    if _manager is None:
        _manager = ChromaManager()
    return _manager
