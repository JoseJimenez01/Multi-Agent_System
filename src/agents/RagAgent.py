from .base_agent import BaseAgent
from src.config import settings


class RagAgent(BaseAgent):
        
    def __init__(self):
        super().__init__()
        # Claude Haiku para tareas de RAG
        self.model = settings.claude_model_fast
        
        self.definition = {
            "agent_name": "Rag_Agent",
            "description": "Agente especializado en recuperar informacion desde los apuntes del curso.",
            "role": "researcher",
            "skills": [
                "search_notes",
                "answer_from_notes",
                # Metadata
                "named_entity_recognition",
                "keyword_extraction",
                # Citation/Reference
                "source_reference",
                "citation_tracking"
            ],
            "allowed_tools": [
                "rag_tool"
            ],
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