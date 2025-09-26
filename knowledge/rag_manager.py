"""
RAG Knowledge Manager for Quantum Computing API Translation
Intelligent retrieval system simulating human programmer document search
"""

import json
import os
import pickle
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from sentence_transformers import SentenceTransformer
from loguru import logger


@dataclass
class APIDocEntry:
    """Single API documentation entry"""
    api_name: str
    library: str
    signature: str
    description: str
    parameters: Dict[str, str]
    returns: str
    example: str
    usage_context: str
    related_apis: List[str]
    common_pitfalls: str
    embedding: Optional[np.ndarray] = None


@dataclass
class SearchResult:
    """Search result entry"""
    api_doc: APIDocEntry
    similarity_score: float
    match_type: str  # "semantic", "keyword", "context"


class EmbeddingCache:
    """Embedding result cache system"""

    def __init__(self, cache_dir: str):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "embeddings_cache.pkl"
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        self._load_cache()

    def _load_cache(self):
        """Load cache"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'rb') as f:
                    self.cache = pickle.load(f)
                logger.info(f"Loaded embedding cache with {len(self.cache)} entries")
            else:
                self.cache = {}
                logger.info("Created new embedding cache")

            if self.metadata_file.exists():
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
            else:
                self.metadata = {"version": "1.0", "model": None, "created": None}
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}, creating new cache")
            self.cache = {}
            self.metadata = {"version": "1.0", "model": None, "created": None}

    def _save_cache(self):
        """Save cache"""
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.cache, f)
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2)
            logger.debug(f"Saved embedding cache with {len(self.cache)} entries")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")

    def _get_cache_key(self, text: str) -> str:
        """Generate cache key"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def get(self, text: str) -> Optional[np.ndarray]:
        """Get cached embedding"""
        key = self._get_cache_key(text)
        return self.cache.get(key)

    def set(self, text: str, embedding: np.ndarray):
        """Set cached embedding"""
        key = self._get_cache_key(text)
        self.cache[key] = embedding

        # Save every 10 new entries
        if len(self.cache) % 10 == 0:
            self._save_cache()

    def save(self):
        """Manually save cache"""
        self._save_cache()


class RAGManager:
    """RAG knowledge base manager - simulating human programmer document search"""

    def __init__(self, knowledge_base_dir: str = None, cache_dir: str = None):
        if knowledge_base_dir is None:
            knowledge_base_dir = Path(__file__).parent / "knowledge_base"
        if cache_dir is None:
            cache_dir = Path(__file__).parent / "embeddings"

        self.knowledge_base_dir = Path(knowledge_base_dir)
        self.api_docs: List[APIDocEntry] = []
        self.embedding_model = None
        self.embedding_cache = EmbeddingCache(cache_dir)

        logger.info(f"Initialized RAG Manager with knowledge base: {self.knowledge_base_dir}")

    def _init_embedding_model(self):
        """Lazy initialize embedding model"""
        if self.embedding_model is None:
            try:
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Loaded sentence transformer model")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                self.embedding_model = None

    def load_knowledge_base(self) -> None:
        """Load all API documents into memory"""
        logger.info("Loading knowledge base...")
        self.api_docs.clear()

        # Traverse all JSON files
        for json_file in self.knowledge_base_dir.rglob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Support single API or API array
                if isinstance(data, list):
                    apis = data
                else:
                    apis = [data]

                for api_data in apis:
                    api_doc = APIDocEntry(
                        api_name=api_data.get("api_name", ""),
                        library=api_data.get("library", ""),
                        signature=api_data.get("signature", ""),
                        description=api_data.get("description", ""),
                        parameters=api_data.get("parameters", {}),
                        returns=api_data.get("returns", ""),
                        example=api_data.get("example", ""),
                        usage_context=api_data.get("usage_context", ""),
                        related_apis=api_data.get("related_apis", []),
                        common_pitfalls=api_data.get("common_pitfalls", "")
                    )
                    self.api_docs.append(api_doc)

            except Exception as e:
                logger.error(f"Failed to load {json_file}: {e}")

        logger.info(f"Loaded {len(self.api_docs)} API documents")

        # Precompute embeddings
        if self.api_docs:
            self._precompute_embeddings()

    def _precompute_embeddings(self):
        """Precompute embeddings for all API documents"""
        self._init_embedding_model()
        if self.embedding_model is None:
            logger.warning("No embedding model available, skipping embedding computation")
            return

        logger.info("Computing embeddings for API documents...")
        new_embeddings = 0

        for api_doc in self.api_docs:
            # Combine text for embedding
            combined_text = f"{api_doc.api_name} {api_doc.description} {api_doc.usage_context}"

            # Check cache
            cached_embedding = self.embedding_cache.get(combined_text)
            if cached_embedding is not None:
                api_doc.embedding = cached_embedding
            else:
                # Compute new embedding
                try:
                    embedding = self.embedding_model.encode(combined_text)
                    api_doc.embedding = embedding
                    self.embedding_cache.set(combined_text, embedding)
                    new_embeddings += 1
                except Exception as e:
                    logger.error(f"Failed to compute embedding for {api_doc.api_name}: {e}")

        # Save cache
        self.embedding_cache.save()
        logger.info(f"Computed {new_embeddings} new embeddings, using {len(self.api_docs) - new_embeddings} cached")

    def search_apis(self, query: str, top_k: int = 5, min_similarity: float = 0.3) -> List[SearchResult]:
        """
        Intelligent API search - simulating human programmer search process

        Args:
            query: Search query (feature description or keywords)
            top_k: Number of results to return
            min_similarity: Minimum similarity threshold
        """
        if not self.api_docs:
            logger.warning("No API docs loaded, call load_knowledge_base() first")
            return []

        results = []

        # 1. Semantic Search
        semantic_results = self._semantic_search(query, top_k * 2)
        results.extend(semantic_results)

        # 2. Keyword Matching
        keyword_results = self._keyword_search(query, top_k)
        results.extend(keyword_results)

        # 3. Context Matching
        context_results = self._context_search(query, top_k)
        results.extend(context_results)

        # Deduplicate and sort
        seen_apis = set()
        unique_results = []
        for result in results:
            if result.api_doc.api_name not in seen_apis and result.similarity_score >= min_similarity:
                seen_apis.add(result.api_doc.api_name)
                unique_results.append(result)

        # Sort by similarity and return top_k
        unique_results.sort(key=lambda x: x.similarity_score, reverse=True)
        return unique_results[:top_k]

    def _semantic_search(self, query: str, top_k: int) -> List[SearchResult]:
        """Semantic search"""
        self._init_embedding_model()
        if self.embedding_model is None:
            return []

        try:
            # Compute query embedding
            query_embedding = self.embedding_model.encode(query)

            results = []
            for api_doc in self.api_docs:
                if api_doc.embedding is not None:
                    # Compute cosine similarity
                    similarity = np.dot(query_embedding, api_doc.embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(api_doc.embedding)
                    )

                    results.append(SearchResult(
                        api_doc=api_doc,
                        similarity_score=float(similarity),
                        match_type="semantic"
                    ))

            results.sort(key=lambda x: x.similarity_score, reverse=True)
            return results[:top_k]

        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []

    def _keyword_search(self, query: str, top_k: int) -> List[SearchResult]:
        """Keyword search"""
        query_lower = query.lower()
        query_words = set(query_lower.split())

        results = []
        for api_doc in self.api_docs:
            # Search target text
            search_text = f"{api_doc.api_name} {api_doc.description} {api_doc.signature}".lower()

            # Calculate keyword match score
            matches = 0
            for word in query_words:
                if word in search_text:
                    matches += 1
                    # Higher weight for API name matches
                    if word in api_doc.api_name.lower():
                        matches += 1

            if matches > 0:
                score = matches / len(query_words)
                results.append(SearchResult(
                    api_doc=api_doc,
                    similarity_score=score,
                    match_type="keyword"
                ))

        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results[:top_k]

    def _context_search(self, query: str, top_k: int) -> List[SearchResult]:
        """Context search - based on usage scenario matching"""
        query_lower = query.lower()

        results = []
        for api_doc in self.api_docs:
            context_text = api_doc.usage_context.lower()

            # Check context matching
            if query_lower in context_text or any(word in context_text for word in query_lower.split()):
                # Simple text matching score
                score = len(set(query_lower.split()) & set(context_text.split())) / len(query_lower.split())

                results.append(SearchResult(
                    api_doc=api_doc,
                    similarity_score=score,
                    match_type="context"
                ))

        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results[:top_k]

    def get_api_by_name(self, api_name: str) -> Optional[APIDocEntry]:
        """Exact API lookup by name"""
        for api_doc in self.api_docs:
            if api_doc.api_name == api_name:
                return api_doc
        return None

    def get_apis_by_library(self, library: str) -> List[APIDocEntry]:
        """Get all APIs from specified library"""
        return [api_doc for api_doc in self.api_docs if api_doc.library == library]

    def get_related_apis(self, api_name: str) -> List[APIDocEntry]:
        """Get related APIs"""
        api_doc = self.get_api_by_name(api_name)
        if not api_doc:
            return []

        related = []
        for related_name in api_doc.related_apis:
            related_api = self.get_api_by_name(related_name)
            if related_api:
                related.append(related_api)

        return related

    def search_by_description_and_keywords(self, description: str) -> List[APIDocEntry]:
        """Interface for DocumentationSearchAgent"""
        results = self.search_apis(description, top_k=10, min_similarity=0.2)
        return [result.api_doc for result in results]

    def get_statistics(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        stats = {
            "total_apis": len(self.api_docs),
            "libraries": {},
            "embedding_model_loaded": self.embedding_model is not None,
            "cache_size": len(self.embedding_cache.cache)
        }

        for api_doc in self.api_docs:
            library = api_doc.library
            if library not in stats["libraries"]:
                stats["libraries"][library] = 0
            stats["libraries"][library] += 1

        return stats