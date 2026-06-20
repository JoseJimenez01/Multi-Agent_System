from .base_agent import BaseAgent
from src.config import settings
from src.memory import MEMORY_TOOL_FUNCTIONS, MEMORY_TOOLS_SCHEMA
from src.memory import db as memory_db
from src.observability.langfuse_tracing import get_langfuse_client, record_exception

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
            "description": (
                "Agente especializado en resumir conversaciones y consultar la memoria "
                "histórica del sistema (sesión actual y sesiones pasadas) usando memory_tool."
            ),
            "role": "summarizer",
            "skills": [
                # Chunking
                "hierarchical_summarization",
                "map_reduce_summary",
                # Memoria histórica
                "search_history",
                "compare_with_previous",
                "search_by_agent_and_date",

                "adaptive_summary_length"
            ],
            "allowed_tools": list(MEMORY_TOOL_FUNCTIONS.keys()),
            "expected inputs": (
                "Una solicitud sobre el historial de la conversación: resumir la sesión actual, "
                "recordar una pregunta anterior, comparar con una pregunta pasada, o verificar si "
                "ya se consultó algo en una fecha/agente específico."
            ),
            "expected outputs": (
                "Un resumen o respuesta en lenguaje natural basado en los datos devueltos por "
                "memory_tool, indicando qué rango de mensajes o sesiones consultó. "
                "Si no hay historial suficiente, debe indicarlo en vez de inventar un resumen."
            ),
            "restrictions": [
                "No debe inventar contenido que no esté presente en la conversación original.",
                "Debe preservar las conclusiones y datos clave de los mensajes resumidos.",
                "Debe indicar qué rango de mensajes de la sesión resumió.",
                "Debe usar memory_tool para consultar historial; no debe responder de memoria propia.",
            ],
            "example of a call": (
                'Entrada: "Resume las preguntas realizadas en esta sesión."\n'
                'Salida: "En esta sesión (3 mensajes previos) preguntaste sobre descenso de '
                'gradiente y el agente RAG respondió citando los apuntes de la Semana 6..."'
            ),
            "language": "Mismo idioma que usa el prompt del usuario."
        }

    def run(
        self,
        prompt: str,
        context: str | None = None,
        history: list[dict] | None = None,
        session_id: str | None = None,
    ) -> str:
        system_prompt = self._build_system_prompt(context)
        if session_id:
            system_prompt += (
                f"\n\nID de la sesión actual: {session_id}. Usa este valor como "
                "session_id al llamar a summarize_current_session o compare_with_previous."
            )
        messages = self._build_messages(history, prompt)
        langfuse = get_langfuse_client()

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=system_prompt,
            messages=messages,
            tools=MEMORY_TOOLS_SCHEMA,
            temperature=0.3,
        )

        tool_results = []
        summarize_message_count = None
        summarized_session_id = None

        for block in response.content:
            if getattr(block, "type", None) != "tool_use":
                continue

            fn = MEMORY_TOOL_FUNCTIONS.get(block.name)
            tool_input = dict(block.input)
            if block.name in ("summarize_current_session", "compare_with_previous"):
                tool_input.setdefault("session_id", session_id)
            if block.name == "summarize_current_session":
                tool_input.setdefault("fallback_history", history)

            result = self._call_memory_tool(block.name, fn, tool_input, langfuse)

            if block.name == "summarize_current_session" and isinstance(result, dict):
                summarized_session_id = tool_input.get("session_id")
                summarize_message_count = result.get("message_count", 0)

            tool_results.append({"tool_use_id": block.id, "content": str(result)})

        if summarize_message_count is not None and summarize_message_count < 2:
            return NO_HISTORY_MESSAGE

        if not tool_results:
            text = "".join(getattr(b, "text", "") for b in response.content if getattr(b, "type", None) == "text")
            return text or NO_HISTORY_MESSAGE

        messages.append({"role": "assistant", "content": response.content})
        messages.append({
            "role": "user",
            "content": [{"type": "tool_result", **tr} for tr in tool_results],
        })

        final = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=system_prompt,
            messages=messages,
            temperature=0.3,
        )
        final_text = final.content[0].text

        if summarized_session_id:
            memory_db.save_session_summary(summarized_session_id, final_text)

        return final_text

    @staticmethod
    def _call_memory_tool(name: str, fn, tool_input: dict, langfuse) -> object:
        if fn is None:
            return {"error": f"Unknown tool: {name}"}

        if langfuse is None:
            try:
                return fn(**tool_input)
            except Exception as error:
                return {"error": str(error)}

        with langfuse.start_as_current_observation(
            as_type="tool",
            name=f"memory_tool.{name}",
            input=tool_input,
        ) as tool_span:
            try:
                result = fn(**tool_input)
            except Exception as error:
                record_exception(tool_span, error)
                return {"error": str(error)}
            tool_span.update(output=result)
            return result
