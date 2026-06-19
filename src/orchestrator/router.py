from contextlib import nullcontext



from src.config.settings import configure_langfuse_env



configure_langfuse_env()



from langfuse import propagate_attributes

from anthropic import Anthropic



from src.agents import RagAgent, WebResearchAgent, TransactionalAgent, SummarizerAgent

from src.agents.base_agent import BaseAgent

from src.database import VectorStore

from src.config import settings

from src.observability.langfuse_tracing import (
    flush_langfuse,
    get_langfuse_client,
    is_tracing_enabled,
    record_current_exception,
    record_exception,
    traced,
)


OUT_OF_SCOPE_MESSAGE = (
    "Esta pregunta no corresponde a ninguna de las capacidades del sistema "
    "(documentos del curso, búsqueda web, consultas transaccionales o resumen de conversación)."
)

OUT_OF_SCOPE = "fuera_de_alcance"




class Orchestrator:

    def __init__(self):

        self.vector_store = VectorStore()

        self.definition = {

            "agent_name": "Orchestrator",

            "description": "Clasificador de tareas para un sistema multi-agente.",

            "role": "router",

            "skills": ["task_classification", "agent_routing"],

            "task_types": {

                "rag": (
                    "Consultas sobre apuntes, notas de clase, materiales del curso, "
                    "documentos académicos o contenido educativo almacenado en la base de conocimiento."
                ),

                "web": (
                    "Consultas que requieren información externa o actual de internet, no "
                    "contenida en los apuntes del curso (noticias, versiones de software, eventos recientes)."
                ),

                "transactional": (
                    "Consultas sobre clientes, cuentas, transacciones o casos de fraude "
                    "ficticios de la base de datos transaccional."
                ),

                "summarizer": (
                    "Solicitudes de resumen sobre la conversación o el historial de la sesión actual."
                ),

                OUT_OF_SCOPE: (
                    "Cualquier consulta que no corresponda a apuntes del curso, búsqueda web, "
                    "datos transaccionales ni resumen de conversación (por ejemplo, conocimiento "
                    "general no relacionado con las capacidades del sistema)."
                ),

            },

            "allowed_tools": [],

            "expected inputs": "Consulta del usuario.",

            "expected outputs": 'Una sola palabra: "rag", "web", "transactional", "summarizer" o "fuera_de_alcance".',

            "restrictions": [

                "Tu única función es determinar el tipo de tarea de la consulta.",

                'Responde ÚNICAMENTE con una palabra: "rag", "web", "transactional", "summarizer" o "fuera_de_alcance".',

            ],

            "example of a call": "",

            "language": "Mismo idioma que usa el prompt del usuario.",

        }

        self.agent_map = {

            "rag": RagAgent(),

            "web": WebResearchAgent(),

            "transactional": TransactionalAgent(),

            "summarizer": SummarizerAgent(),

        }

        for task_type, agent in self.agent_map.items():
            agent.name = task_type



    def route(self, prompt: str, session_id: str, history: list[dict] | None = None) -> dict:

        trace_context = (

            propagate_attributes(

                session_id=session_id,

                trace_name="multi-agent-query",

                metadata={"app": "multi-agent-system"},

            )

            if is_tracing_enabled()

            else nullcontext()

        )

        try:

            with trace_context:

                result = self._route_traced(prompt, session_id, history)

        finally:

            flush_langfuse()

        return result



    @traced(as_type="chain", name="orchestrator-route", capture_input=False, capture_output=False)

    def _route_traced(self, prompt: str, session_id: str, history: list[dict] | None = None) -> dict:

        langfuse = get_langfuse_client()

        if langfuse is not None:

            langfuse.update_current_span(
                input={"prompt": prompt},
                metadata={"session_id": session_id},
            )



        try:

            task_type = self._classify_task(prompt)

            if task_type == OUT_OF_SCOPE:

                response = {
                    "result": OUT_OF_SCOPE_MESSAGE,
                    "agent": OUT_OF_SCOPE,
                    "context_used": False,
                }

                if langfuse is not None:

                    langfuse.update_current_span(
                        metadata={
                            "session_id": session_id,
                            "task_type": task_type,
                            "routed_agent": OUT_OF_SCOPE,
                        },
                        output={
                            "agent": response["agent"],
                            "context_used": response["context_used"],
                            "result_preview": response["result"][:500],
                        },
                    )

                return response

            agent = self._get_agent(task_type)

            if langfuse is not None:

                langfuse.update_current_span(
                    metadata={
                        "session_id": session_id,
                        "task_type": task_type,
                        "routed_agent": agent.name,
                    },
                )

            if isinstance(agent, SummarizerAgent):
                result = agent.run(prompt, context=SummarizerAgent.format_history(history))
            else:
                result = agent.run(prompt)

        except Exception as error:

            record_current_exception(error)

            raise

        context_used = getattr(agent, "context_used", False)

        response = {"result": result, "agent": agent.name, "context_used": context_used}



        if langfuse is not None:

            langfuse.update_current_span(

                output={
                    "agent": response["agent"],
                    "context_used": response["context_used"],
                    "result_preview": response["result"][:500],
                }

            )



        return response



    def _get_agent(self, task_type: str) -> BaseAgent:

        return self.agent_map[task_type]



    def _build_classifier_prompt(self) -> str:

        lines = [

            f"Eres {self.definition['agent_name']}.",

            self.definition["description"],

            "Tu única función es determinar si la consulta del usuario está relacionada con:",

        ]

        for task_type, description in self.definition["task_types"].items():

            lines.append(f'- "{task_type}": {description}')

        lines.append("")

        for restriction in self.definition["restrictions"]:

            lines.append(restriction)

        return "\n".join(lines)



    @traced(as_type="span", name="classify-task")

    def _classify_task(self, prompt: str) -> str:

        client = Anthropic(api_key=settings.anthropic_api_key)

        # El Orquestador es el agente más riguroso del sistema (Tabla I de la
        # especificación): usa el modelo más fuerte disponible también para clasificar.
        model = settings.claude_model_primary

        system_prompt = self._build_classifier_prompt()

        valid_task_types = self.definition["task_types"]

        langfuse = get_langfuse_client()

        if langfuse is None:

            response = client.messages.create(
                model=model,
                max_tokens=10,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )

            task_type = response.content[0].text.strip().lower()

            return task_type if task_type in valid_task_types else OUT_OF_SCOPE

        with langfuse.start_as_current_observation(
            as_type="generation",
            name="anthropic-classifier",
            model=model,
            input={"system": system_prompt, "user_message": prompt},
            model_parameters={"temperature": 0, "max_tokens": 10},
        ) as generation:

            try:

                response = client.messages.create(
                    model=model,
                    max_tokens=10,
                    system=system_prompt,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                )

            except Exception as error:

                record_exception(generation, error)

                raise

            task_type = response.content[0].text.strip().lower()

            generation.update(
                output=task_type,
                usage_details={
                    "input": response.usage.input_tokens,
                    "output": response.usage.output_tokens,
                },
            )

        resolved = task_type if task_type in valid_task_types else OUT_OF_SCOPE

        langfuse.update_current_span(output={"task_type": resolved})

        return resolved

