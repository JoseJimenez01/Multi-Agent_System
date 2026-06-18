from .base_agent import BaseAgent
from src.config import settings

NO_HISTORY_MESSAGE = (
    "No hay suficiente historial en esta sesión para generar un resumen. "
    "Hacé al menos una pregunta primero y luego pedime el resumen."
)


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
            "expected inputs": (
                "Una solicitud de resumen sobre el historial de la sesión actual "
                "(por ejemplo, 'resume las preguntas que he hecho hoy')."
            ),
            "expected outputs": (
                "Un resumen en lenguaje natural de los turnos previos de la sesión, "
                "preservando las conclusiones clave e indicando qué rango de mensajes resumió. "
                "Si no hay historial suficiente, debe indicarlo en vez de inventar un resumen."
            ),
            "restrictions": [
                "No debe inventar contenido que no esté presente en la conversación original.",
                "Debe preservar las conclusiones y datos clave de los mensajes resumidos.",
                "Debe indicar qué rango de mensajes de la sesión resumió.",
            ],
            "example of a call": (
                'Entrada: "Resume las preguntas realizadas en esta sesión."\n'
                'Salida: "En esta sesión (3 mensajes previos) preguntaste sobre descenso de '
                'gradiente y el agente RAG respondió citando los apuntes de la Semana 6..."'
            ),
            "language": "Mismo idioma que usa el prompt del usuario."
        }

    @staticmethod
    def format_history(history: list[dict] | None) -> str | None:
        """Da formato al historial de st.session_state.messages como texto para el LLM.

        Punto de extensión: hoy recibe el historial de la sesión en memoria (Streamlit);
        cuando exista memoria histórica persistente, este método debe poder recibir el
        mismo tipo de lista obtenida desde la base de datos para sesiones pasadas.
        """
        if not history or len(history) < 2:
            return None

        lines = []
        for msg in history:
            if msg.get("role") == "user":
                speaker = "Usuario"
            else:
                speaker = f"Asistente ({msg.get('agent', 'desconocido')})"
            lines.append(f"{speaker}: {msg.get('content', '')}")

        return "\n".join(lines)

    def run(self, prompt: str, context: str | None = None) -> str:
        if not context:
            return NO_HISTORY_MESSAGE

        return super().run(prompt, context=context)
