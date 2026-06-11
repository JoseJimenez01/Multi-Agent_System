from .base_agent import BaseAgent
from src.config import settings
from src.database import VectorStore
from openai import OpenAI
from qdrant_client.models import Distance


class RagAgent(BaseAgent):

    def __init__(self):
        super().__init__()
        self.model = settings.claude_model_fast
        self.openai_client = OpenAI(api_key=settings.openai_api_key)
        self.vector_store = VectorStore()
        self.vector_store.ensure_collection("rag_notes", distance=Distance.EUCLID)

        # quitar este y usar los self.definition
        self.system_prompt = (
            "Eres un asistente experto en recuperar información de apuntes académicos. "
            "Usa EXCLUSIVAMENTE el contexto proporcionado para responder. "
            "Si el contexto no contiene la información necesaria, indícalo claramente "
            "y sugiere reformular la consulta. Cita las fuentes cuando sea posible. "
            "Responde en el mismo idioma del usuario."
        )

        self.definition = {
            "agent_name": "Rag_Agent",
            "description": "Agente especializado en recuperar informacion desde los apuntes del curso.",
            "role": "researcher",
            "skills": [
                "search_notes",
                "answer_from_notes",
                "named_entity_recognition",
                "keyword_extraction",
                "source_reference",
                "citation_tracking"
            ],
            "allowed_tools": ["rag_tool"],
            "expected inputs": "",
            "expected outputs": "",
            "restrictions": [
                "Debe citar documentos y autores.",
                "No debe inventar fuentes.",
                "No debe usar busqueda web."
            ],
            "example of a call": "",
            "language": "Mismo idioma que usa el prompt del usuario."
        }

    def _get_embedding(self, text: str) -> list[float]:
        resp = self.openai_client.embeddings.create(
            model=settings.embedding_model,
            input=text
        )
        return resp.data[0].embedding

    def run(self, prompt: str, context: str | None = None) -> str:
        query_embedding = self._get_embedding(prompt)

        rag_results = self.vector_store.search(
            collection_name="rag_notes",
            query_vector=query_embedding,
            limit=3,
            score_threshold=None,
        )

        course_results = self.vector_store.search(
            collection_name="course_notes",
            query_vector=query_embedding,
            limit=3,
            score_threshold=0.5,
        )

        all_results = (rag_results or []) + (course_results or [])
        context_text = None
        if all_results:
            context_text = "\n\n---\n\n".join(
                r.payload.get("text", "") for r in all_results if r.payload
            )

        return super().run(prompt, context=context_text)