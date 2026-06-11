from qdrant_client import QdrantClient, models
from qdrant_client.models import Distance, VectorParams

from src.config import settings


class VectorStore:
    def __init__(self, url: str | None = None):
        self.client = QdrantClient(url or settings.qdrant_url)
        self.dimension = settings.embedding_dimension

    def ensure_collection(self, collection_name: str, distance: Distance = Distance.COSINE):
        collections = self.client.get_collections().collections
        if not any(c.name == collection_name for c in collections):
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=self.dimension,
                    distance=distance,
                ),
            )

    def upsert(self, collection_name: str, points: list[models.PointStruct]):
        self.client.upsert(collection_name=collection_name, points=points)

    def search(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int = 5,
        score_threshold: float | None = 0.75,
    ) -> list[models.ScoredPoint]:
        return self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold,
        )

    def delete_collection(self, collection_name: str):
        self.client.delete_collection(collection_name=collection_name)
