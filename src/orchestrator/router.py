from contextlib import nullcontext

from src.config.settings import configure_langfuse_env

configure_langfuse_env()

from langfuse import propagate_attributes
from anthropic import Anthropic

from src.agents import RagAgent
from src.agents.base_agent import BaseAgent
from src.database import VectorStore, DatabaseManager
from src.config import settings
from src.observability.langfuse_tracing import flush_langfuse, get_langfuse_client, is_tracing_enabled, traced


CLASSIFIER_SYSTEM_PROMPT = (
    "Eres un clasificador de tareas para un sistema multi-agente.\n"
    "Tu única función es determinar si la consulta del usuario está relacionada con:\n"
    '- "rag": consultas sobre apuntes, notas de clase, materiales del curso, '
    "documentos académicos, o cualquier contenido educativo almacenado en la base de conocimiento.\n"
    '- "general": cualquier otra consulta que no requiera buscar en los apuntes.\n\n'
    'Responde ÚNICAMENTE con una palabra: "rag" o "general".'
)


class Orchestrator:
    def __init__(self):
        self.vector_store = VectorStore()
        #self.db = DatabaseManager()
        self.agent_map = {
            "rag": RagAgent(),
            "general": BaseAgent(),
        }
        self.agent_map["rag"].name = "rag"
        self.agent_map["general"].name = "general"
        self.agent_map["general"].system_prompt = (
            "Eres un asistente IA versátil. Responde cualquier consulta "
            "de forma clara, precisa y en el mismo idioma de la pregunta."
        )

    def route(self, prompt: str, session_id: str) -> dict:
        trace_context = (
            propagate_attributes(
                session_id=session_id,
                trace_name="multi-agent-query",
                metadata={"app": "multi-agent-system"},
            )
            if is_tracing_enabled()
            else nullcontext()
        )
        with trace_context:
            result = self._route_traced(prompt, session_id)

        flush_langfuse()
        return result

    @traced(as_type="chain", name="orchestrator-route", capture_input=False, capture_output=False)
    def _route_traced(self, prompt: str, session_id: str) -> dict:
        langfuse = get_langfuse_client()
        if langfuse is not None:
            langfuse.update_current_span(input={"prompt": prompt})

        task_type = self._classify_task(prompt)
        agent = self._get_agent(task_type)

        # self.db.log_task(
        #     task_type, prompt, session_id, agent_used=agent.name, status="processing"
        # )

        try:
            result = agent.run(prompt)
            self.db.log_task(
                task_type, prompt, session_id, agent_used=agent.name,
                status="completed", result_text=result,
            )
            response = {"result": result, "agent": agent.name, "context_used": True}
        except Exception as e:
            self.db.log_task(
                task_type, prompt, session_id, agent_used=agent.name,
                status="failed", result_text=str(e),
            )
            raise

        if langfuse is not None:
            langfuse.update_current_span(
                output={
                    "agent": response["agent"],
                    "result_preview": response["result"][:500],
                }
            )

        return response

    def _get_agent(self, task_type: str) -> BaseAgent:
        return self.agent_map.get(task_type, self.agent_map["general"])

    @traced(as_type="span", name="classify-task")
    def _classify_task(self, prompt: str) -> str:
        client = Anthropic(api_key=settings.anthropic_api_key)
        response = client.messages.create(
            model=settings.claude_model_fast,
            max_tokens=10,
            system=CLASSIFIER_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        task_type = response.content[0].text.strip().lower()

        langfuse = get_langfuse_client()
        if langfuse is not None:
            langfuse.update_current_span(output={"task_type": task_type})

        return task_type if task_type in ("rag", "general") else "general"
