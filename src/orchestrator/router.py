from contextlib import nullcontext



from src.config.settings import configure_langfuse_env



configure_langfuse_env()



from langfuse import propagate_attributes

from anthropic import Anthropic



from src.agents import RagAgent

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

                "general": "Cualquier otra consulta que no requiera buscar en los apuntes.",

            },

            "allowed_tools": [],

            "expected inputs": "Consulta del usuario.",

            "expected outputs": 'Una sola palabra: "rag" o "general".',

            "restrictions": [

                "Tu única función es determinar el tipo de tarea de la consulta.",

                'Responde ÚNICAMENTE con una palabra: "rag" o "general".',

            ],

            "example of a call": "",

            "language": "Mismo idioma que usa el prompt del usuario.",

        }

        self.agent_map = {

            "rag": RagAgent(),

            "general": BaseAgent(),

        }

        self.agent_map["rag"].name = "rag"

        self.agent_map["general"].name = "general"



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

        try:

            with trace_context:

                result = self._route_traced(prompt, session_id)

        finally:

            flush_langfuse()

        return result



    @traced(as_type="chain", name="orchestrator-route", capture_input=False, capture_output=False)

    def _route_traced(self, prompt: str, session_id: str) -> dict:

        langfuse = get_langfuse_client()

        if langfuse is not None:

            langfuse.update_current_span(
                input={"prompt": prompt},
                metadata={"session_id": session_id},
            )



        try:

            task_type = self._classify_task(prompt)

            agent = self._get_agent(task_type)

            if langfuse is not None:

                langfuse.update_current_span(
                    metadata={
                        "session_id": session_id,
                        "task_type": task_type,
                        "routed_agent": agent.name,
                    },
                )

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

        return self.agent_map.get(task_type, self.agent_map["general"])



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

        model = settings.claude_model_fast

        system_prompt = self._build_classifier_prompt()

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

            return task_type if task_type in self.definition["task_types"] else "general"

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

        resolved = task_type if task_type in self.definition["task_types"] else "general"

        langfuse.update_current_span(output={"task_type": resolved})

        return resolved

