from .base_agent import BaseAgent
from src.config import settings


class SummarizerAgent(BaseAgent):

    def __init__(self):
        super().__init__()
        # Claude Haiku para tareas de resumen 
        self.model = settings.claude_model_fast

        self.definition = {
            "agent_name": "Summarizer_Agent",
            "description": "Agente especializado en resumir conversaciones, resultados de búsqueda, respuestas largas o historial de una sesión.",
            "role": "summarizer",
            "skills": [
                # Chunking
                "hierarchical_summarization",
                "map_reduce_summary",
                # Embeddings
                "semantic_search",
                "retrieve_context",

                "adaptive_summary_length"
            ],
            "allowed_tools": [
                "memory_tool"
            ],
            "expected inputs": "",
            "expected outputs": "",
            "restrictions": [
                "Debe dar referencias a las que poder consultar.",
                "No debe inventar fuentes.",
                "Debe usar busqueda web."
            ],
            "example of a call": "",
            "language": "Mismo idioma que usa el prompt del usuario."
        }