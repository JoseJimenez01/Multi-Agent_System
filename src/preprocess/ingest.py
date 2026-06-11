import json
from pathlib import Path

from openai import OpenAI
from loguru import logger

from src.config import settings
from src.database.vector_store import VectorStore
from src.preprocess.processor import process_all_documents
from qdrant_client import models


COLLECTION_NAME = "course_notes"


def get_embedding(client: OpenAI, text: str, model: str = settings.embedding_model) -> list[float]:
    text = text.replace("\n", " ")
    response = client.embeddings.create(input=[text], model=model)
    return response.data[0].embedding


def ingest_documents(notes_dir: str | Path | None = None):
    logger.info("Starting document ingestion pipeline")

    documents = process_all_documents(Path(notes_dir) if notes_dir else None)
    if not documents:
        logger.warning("No documents to ingest")
        return

    logger.info(f"Initializing OpenAI client (model: {settings.embedding_model})")
    openai_client = OpenAI(api_key=settings.openai_api_key)

    logger.info(f"Initializing Qdrant vector store (collection: {COLLECTION_NAME})")
    vector_store = VectorStore()
    vector_store.ensure_collection(COLLECTION_NAME)

    points = []
    for i, doc in enumerate(documents):
        logger.info(f"Embedding chunk {i + 1}/{len(documents)}: {doc['id']}")
        vector = get_embedding(openai_client, doc["text"])

        point = models.PointStruct(
            id=i,
            vector=vector,
            payload={
                "text": doc["text"],
                "token_estimate": doc["token_estimate"],
                "metadata": doc["metadata"],
            },
        )
        points.append(point)

        if len(points) >= 100:
            vector_store.upsert(COLLECTION_NAME, points)
            logger.info(f"Upserted batch of {len(points)} points")
            points = []

    if points:
        vector_store.upsert(COLLECTION_NAME, points)
        logger.info(f"Upserted final batch of {len(points)} points")

    logger.info(f"Ingestion complete. Total points: {len(documents)}")


def export_documents_json(output_path: str = "documents_export.json"):
    documents = process_all_documents()
    export = []
    for doc in documents:
        export.append({
            "id": doc["id"],
            "text": doc["text"],
            "token_estimate": doc["token_estimate"],
            "metadata": doc["metadata"],
        })

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(export, f, indent=2, ensure_ascii=False)

    logger.info(f"Exported {len(export)} documents to {output_path}")
    return output_path


if __name__ == "__main__":
    ingest_documents()
