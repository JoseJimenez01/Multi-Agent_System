import re

from qdrant_client.models import FieldCondition, Filter, MatchValue, ScoredPoint

from .base_agent import BaseAgent
from src.config import settings
from src.database import VectorStore
from src.preprocess.processor import extract_semana_from_query
from openai import OpenAI


COLLECTION_NAME = "course_notes"
SCORE_THRESHOLD = 0.35
FILTERED_SCORE_THRESHOLD = 0.20
SEARCH_LIMIT = 5


class RagAgent(BaseAgent):

    def __init__(self):
        super().__init__()
        self.model = settings.claude_model_fast
        self.openai_client = OpenAI(api_key=settings.openai_api_key)
        self.vector_store = VectorStore()
        self.vector_store.ensure_collection(COLLECTION_NAME)
        self.context_used = False

        self.definition = {
            "agent_name": "Rag_Agent",
            "description": (
                "Agente especializado en recuperar informacion desde los apuntes del curso."
            ),
            "role": "researcher",
            "skills": [
                "search_notes",
                "answer_from_notes",
                "named_entity_recognition",
                "keyword_extraction",
                "source_reference",
                "citation_tracking",
            ],
            "allowed_tools": ["rag_tool"],
            "expected inputs": "",
            "expected outputs": "",
            "restrictions": [
                "Usa EXCLUSIVAMENTE el contexto proporcionado para responder.",
                "Si el contexto no contiene la información necesaria, indícalo claramente "
                "y sugiere reformular la consulta.",
                "Cita siempre el documento, semana y autor indicados en cada fragmento.",
                "No debe inventar fuentes.",
                "No debe usar busqueda web.",
            ],
            "example of a call": "",
            "language": "Mismo idioma que usa el prompt del usuario.",
        }

    def _get_embedding(self, text: str) -> list[float]:
        resp = self.openai_client.embeddings.create(
            model=settings.embedding_model,
            input=text,
        )
        return resp.data[0].embedding

    @staticmethod
    def _build_semana_filter(semana: str) -> Filter:
        return Filter(
            must=[
                FieldCondition(
                    key="metadata.semana",
                    match=MatchValue(value=semana),
                )
            ]
        )

    @staticmethod
    def _format_chunk(result: ScoredPoint) -> str:
        payload = result.payload or {}
        metadata = payload.get("metadata") or {}
        header_parts = []

        if metadata.get("file_name"):
            header_parts.append(f"Documento: {metadata['file_name']}")
        if metadata.get("semana"):
            header_parts.append(metadata["semana"])
        if metadata.get("seccion"):
            header_parts.append(metadata["seccion"])
        if metadata.get("autor"):
            header_parts.append(f"Autor: {metadata['autor']}")
        if metadata.get("profesor"):
            header_parts.append(f"Profesor: {metadata['profesor']}")

        header = " | ".join(header_parts) if header_parts else "Fuente: apuntes del curso"
        text = payload.get("text", "")
        return f"[{header}]\n{text}"

    def _retrieve_chunks(self, prompt: str, query_embedding: list[float]) -> list[str]:
        semana = extract_semana_from_query(prompt)
        query_filter = self._build_semana_filter(semana) if semana else None
        threshold = FILTERED_SCORE_THRESHOLD if semana else SCORE_THRESHOLD

        results = self.vector_store.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_embedding,
            limit=SEARCH_LIMIT,
            score_threshold=threshold,
            query_filter=query_filter,
        )

        chunks: list[str] = []
        seen_texts: set[str] = set()
        for result in results or []:
            if not result.payload:
                continue
            text = result.payload.get("text", "")
            if not text or text in seen_texts:
                continue
            seen_texts.add(text)
            chunks.append(self._format_chunk(result))

        return chunks

    def run(self, prompt: str, context: str | None = None) -> str:
        self.context_used = False
        query_embedding = self._get_embedding(prompt)
        chunks = self._retrieve_chunks(prompt, query_embedding)

        context_text = "\n\n---\n\n".join(chunks) if chunks else None
        self.context_used = context_text is not None

        return super().run(prompt, context=context_text)
