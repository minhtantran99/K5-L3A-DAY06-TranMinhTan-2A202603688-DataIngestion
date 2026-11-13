"""Persistent Qdrant local backend: cosine search and metadata filters."""
from dataclasses import asdict
from uuid import NAMESPACE_URL, uuid5
from qdrant_client import QdrantClient, models

class QdrantStore:
    def __init__(self, path, dimensions):
        self.client = QdrantClient(path=str(path))
        self.dimensions = dimensions

    @staticmethod
    def collection(strategy):
        if strategy not in {"A", "B", "C"}:
            raise ValueError("Unknown strategy")
        return f"day06_{strategy}"

    def replace(self, strategy, chunks, vectors):
        if len(chunks) != len(vectors) or any(len(v) != self.dimensions for v in vectors):
            raise ValueError("Invalid vector count/dimensions")
        name = self.collection(strategy)
        # Clear points through Qdrant API: deleting/recreating a collection can
        # leave SQLite files locked on Windows. Full refresh is not atomic.
        if self.client.collection_exists(name):
            config = self.client.get_collection(name).config.params.vectors
            if config.size != self.dimensions or config.distance != models.Distance.COSINE:
                raise ValueError("Existing collection has incompatible vector configuration")
            self.client.delete(name, points_selector=models.FilterSelector(filter=models.Filter()), wait=True)
            if self.count(strategy) != 0:
                raise ValueError("Failed to clear previous snapshot")
        else:
            self.client.create_collection(name, vectors_config=models.VectorParams(
                size=self.dimensions, distance=models.Distance.COSINE))
        self.upsert(strategy, chunks, vectors)

    def upsert(self, strategy, chunks, vectors):
        if len(chunks) != len(vectors) or any(len(v) != self.dimensions for v in vectors):
            raise ValueError("Invalid vectors")
        points = [models.PointStruct(id=str(uuid5(NAMESPACE_URL, c.chunk_id)), vector=v,
                  payload={**asdict(c), **c.metadata}) for c, v in zip(chunks, vectors)]
        for start in range(0, len(points), 64):
            self.client.upsert(self.collection(strategy), points[start:start + 64], wait=True)

    def count(self, strategy):
        return self.client.count(self.collection(strategy), exact=True).count

    def search(self, strategy, query_vector, top_k=3, filters=None):
        if filters and set(filters) - {"content_group", "language", "document_id"}:
            raise ValueError("Unsupported filter key")
        conditions = [models.FieldCondition(key=k, match=models.MatchValue(value=v))
                      for k, v in (filters or {}).items()]
        result = self.client.query_points(
            self.collection(strategy), query=query_vector, limit=top_k,
            query_filter=models.Filter(must=conditions) if conditions else None,
            with_payload=True)  # Local mode always uses exact search.
        return [{**p.payload, "score": p.score} for p in result.points]

    def close(self):
        self.client.close()
