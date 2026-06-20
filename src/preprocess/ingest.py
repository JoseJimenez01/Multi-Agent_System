import argparse
import json
from pathlib import Path

from openai import OpenAI
from loguru import logger

from src.config import settings
from src.database.vector_store import VectorStore
from src.preprocess.processor import process_all_documents
from qdrant_client import models


DEFAULT_COLLECTION = "course_notes"

# Colecciones dedicadas a la comparación experimental de estrategias de
# segmentación (III-C de la especificación): mismo contenido, mismo
# chunk_size/overlap, distinto criterio de corte.
STRATEGY_COLLECTIONS = {
    "sentences": "course_notes_v1_sentences",
    "fixed_size": "course_notes_v2_fixed",
}


def get_embedding(client: OpenAI, text: str, model: str = settings.embedding_model) -> list[float]:
    text = text.replace("\n", " ")
    response = client.embeddings.create(input=[text], model=model)
    return response.data[0].embedding


def ingest_documents(
    notes_dir: str | Path | None = None,
    strategy: str = "sentences",
    collection_name: str | None = None,
) -> str:
    collection_name = collection_name or STRATEGY_COLLECTIONS.get(strategy, DEFAULT_COLLECTION)
    logger.info(f"Starting document ingestion pipeline (strategy={strategy}, collection={collection_name})")

    documents = process_all_documents(Path(notes_dir) if notes_dir else None, strategy=strategy)
    if not documents:
        logger.warning("No documents to ingest")
        return collection_name

    logger.info(f"Initializing OpenAI client (model: {settings.embedding_model})")
    openai_client = OpenAI(api_key=settings.openai_api_key)

    logger.info(f"Initializing Qdrant vector store (collection: {collection_name})")
    vector_store = VectorStore()
    vector_store.ensure_collection(collection_name)

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
            vector_store.upsert(collection_name, points)
            logger.info(f"Upserted batch of {len(points)} points")
            points = []

    if points:
        vector_store.upsert(collection_name, points)
        logger.info(f"Upserted final batch of {len(points)} points")

    logger.info(f"Ingestion complete ({collection_name}). Total points: {len(documents)}")
    return collection_name


def ingest_all_strategies(notes_dir: str | Path | None = None) -> dict[str, str]:
    """Corre la ingesta completa para las dos estrategias de segmentación,
    cada una hacia su propia colección, para poder compararlas después."""
    results = {}
    for strategy, collection_name in STRATEGY_COLLECTIONS.items():
        results[strategy] = ingest_documents(notes_dir=notes_dir, strategy=strategy, collection_name=collection_name)
    return results


def export_documents_json(output_path: str = "documents_export.json", strategy: str = "sentences"):
    documents = process_all_documents(strategy=strategy)
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
    parser = argparse.ArgumentParser(description="Ingesta de apuntes del curso a Qdrant.")
    parser.add_argument(
        "--strategy",
        choices=["sentences", "fixed_size", "all"],
        default="sentences",
        help="Estrategia de segmentación a usar ('all' corre ambas, una por colección).",
    )
    parser.add_argument(
        "--collection",
        default=None,
        help="Nombre de colección destino (default: derivado de la estrategia).",
    )
    parser.add_argument("--notes-dir", default=None, help="Carpeta de PDFs a ingerir (default: src/notes/).")
    args = parser.parse_args()

    if args.strategy == "all":
        ingest_all_strategies(notes_dir=args.notes_dir)
    else:
        ingest_documents(notes_dir=args.notes_dir, strategy=args.strategy, collection_name=args.collection)
