"""
Azure AI Search service for hybrid vector + keyword search on code chunks.
"""

import uuid
import numpy as np
from typing import Optional

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger("search")


class SearchDocument:
    """Document to be indexed in Azure AI Search."""
    def __init__(self, doc_id: str, repo_id: str, file_path: str, language: str, framework: str,
                 code_text: str, element_type: str, content_vector: list[float],
                 chunk_index: int = 0, total_chunks: int = 1, metadata: str = ""):
        self.doc_id = doc_id
        self.repo_id = repo_id
        self.file_path = file_path
        self.language = language
        self.framework = framework
        self.code_text = code_text
        self.element_type = element_type
        self.content_vector = content_vector
        self.chunk_index = chunk_index
        self.total_chunks = total_chunks
        self.metadata = metadata

    def to_dict(self) -> dict:
        return {
            "id": self.doc_id, "repo_id": self.repo_id, "file_path": self.file_path,
            "language": self.language, "framework": self.framework,
            "code_text": self.code_text, "element_type": self.element_type,
            "content_vector": self.content_vector,
            "chunk_index": self.chunk_index, "total_chunks": self.total_chunks,
            "metadata": self.metadata,
        }


class SearchService:
    """Azure AI Search service with hybrid search capabilities."""

    def __init__(self):
        self.settings = get_settings()
        self._search_client = None
        self._index_client = None

    def _get_index_client(self):
        if self._index_client is None:
            from azure.core.credentials import AzureKeyCredential
            from azure.search.documents.indexes import SearchIndexClient
            self._index_client = SearchIndexClient(
                endpoint=self.settings.AZURE_SEARCH_ENDPOINT,
                credential=AzureKeyCredential(self.settings.AZURE_SEARCH_API_KEY),
            )
        return self._index_client

    def _get_search_client(self):
        if self._search_client is None:
            from azure.core.credentials import AzureKeyCredential
            from azure.search.documents import SearchClient
            self._search_client = SearchClient(
                endpoint=self.settings.AZURE_SEARCH_ENDPOINT,
                index_name=self.settings.AZURE_SEARCH_INDEX_NAME,
                credential=AzureKeyCredential(self.settings.AZURE_SEARCH_API_KEY),
            )
        return self._search_client

    async def create_or_update_index(self):
        from azure.search.documents.indexes.models import (
            SearchIndex, SearchField, SearchFieldDataType, SearchableField, SimpleField,
            VectorSearch, HnswAlgorithmConfiguration, VectorSearchProfile,
            SemanticConfiguration, SemanticPrioritizedFields, SemanticField, SemanticSearch,
        )
        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True, filterable=True),
            SimpleField(name="repo_id", type=SearchFieldDataType.String, filterable=True),
            SearchableField(name="file_path", type=SearchFieldDataType.String, filterable=True),
            SearchableField(name="language", type=SearchFieldDataType.String, filterable=True),
            SearchableField(name="framework", type=SearchFieldDataType.String, filterable=True),
            SearchableField(name="code_text", type=SearchFieldDataType.String),
            SearchableField(name="element_type", type=SearchFieldDataType.String, filterable=True),
            SearchField(
                name="content_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=self.settings.EMBEDDING_DIMENSIONS,
                vector_search_profile_name="code-vector-profile",
            ),
            SimpleField(name="chunk_index", type=SearchFieldDataType.Int32),
            SimpleField(name="total_chunks", type=SearchFieldDataType.Int32),
            SimpleField(name="metadata", type=SearchFieldDataType.String),
        ]
        vector_search = VectorSearch(
            algorithms=[HnswAlgorithmConfiguration(name="code-hnsw-config")],
            profiles=[VectorSearchProfile(name="code-vector-profile", algorithm_configuration_name="code-hnsw-config")],
        )
        semantic_config = SemanticConfiguration(
            name="code-semantic-config",
            prioritized_fields=SemanticPrioritizedFields(
                content_fields=[SemanticField(field_name="code_text")],
                title_field=SemanticField(field_name="file_path"),
                keywords_fields=[SemanticField(field_name="element_type")],
            ),
        )
        index = SearchIndex(
            name=self.settings.AZURE_SEARCH_INDEX_NAME, fields=fields,
            vector_search=vector_search,
            semantic_search=SemanticSearch(configurations=[semantic_config]),
        )
        self._get_index_client().create_or_update_index(index)
        logger.info(f"Search index '{self.settings.AZURE_SEARCH_INDEX_NAME}' created/updated")

    async def index_documents(self, documents: list[SearchDocument]):
        client = self._get_search_client()
        batch = [doc.to_dict() for doc in documents]
        for i in range(0, len(batch), 1000):
            chunk = batch[i:i+1000]
            result = client.upload_documents(documents=chunk)
            succeeded = sum(1 for r in result if r.succeeded)
            logger.info(f"Indexed {succeeded}/{len(chunk)} documents")

    async def hybrid_search(self, query_text: str, query_vector: list[float], repo_id: str = None,
                            top: int = 10, filter_expr: Optional[str] = None) -> list[dict]:
        from azure.search.documents.models import VectorizedQuery
        vector_query = VectorizedQuery(vector=query_vector, k_nearest_neighbors=50, fields="content_vector")
        client = self._get_search_client()
        
        # Base filter for repo_id
        if repo_id:
            repo_filter = f"repo_id eq '{repo_id}'"
            final_filter = f"({repo_filter}) and ({filter_expr})" if filter_expr else repo_filter
        else:
            final_filter = filter_expr
            
        results = client.search(
            search_text=query_text, vector_queries=[vector_query],
            query_type="semantic", semantic_configuration_name="code-semantic-config",
            top=top, filter=final_filter,
            select=["id", "repo_id", "file_path", "language", "framework", "code_text", "element_type"],
        )
        return [{"id": r["id"], "file_path": r["file_path"], "code_text": r["code_text"],
                 "language": r.get("language", ""), "framework": r.get("framework", ""),
                 "element_type": r.get("element_type", ""), "score": r.get("@search.score", 0),
                 } for r in results]


class MockSearchService(SearchService):
    """In-memory search service for local development."""

    def __init__(self):
        super().__init__()
        self._documents: list[SearchDocument] = []

    async def create_or_update_index(self):
        logger.info("[MOCK] Index created (in-memory)")

    async def index_documents(self, documents: list[SearchDocument]):
        self._documents.extend(documents)
        logger.info(f"[MOCK] Indexed {len(documents)} documents (total: {len(self._documents)})")

    async def hybrid_search(self, query_text: str, query_vector: list[float], repo_id: str = None,
                            top: int = 10, filter_expr: Optional[str] = None) -> list[dict]:
        if not self._documents:
            return []
        query_vec = np.array(query_vector)
        scored = []
        for doc in self._documents:
            if repo_id and getattr(doc, 'repo_id', None) != repo_id:
                continue
            doc_vec = np.array(doc.content_vector)
            cos_sim = np.dot(query_vec, doc_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(doc_vec) + 1e-8)
            query_words = set(query_text.lower().split())
            doc_words = set(doc.code_text.lower().split())
            keyword_overlap = len(query_words & doc_words) / max(len(query_words), 1)
            scored.append((doc, 0.7 * cos_sim + 0.3 * keyword_overlap))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [{"id": d.doc_id, "file_path": d.file_path, "code_text": d.code_text,
                 "language": d.language, "framework": d.framework,
                 "element_type": d.element_type, "score": float(s),
                 } for d, s in scored[:top]]

    async def delete_all_documents(self):
        self._documents.clear()


def get_search_service() -> SearchService:
    settings = get_settings()
    if settings.MOCK_MODE:
        return MockSearchService()
    return SearchService()
