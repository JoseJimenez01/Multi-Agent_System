from .base_agent import BaseAgent
from src.config import settings
from src.observability.langfuse_tracing import (
    flush_langfuse,
    get_langfuse_client,
    record_exception,
)

WEB_SEARCH_TOOL = {
    "type": "web_search_20250305",
    "name": "web_search",
    "max_uses": 3,
}

# El Orquestador ya decidió que esta consulta necesita la web: se fuerza el uso de la
# herramienta en el primer turno para que el modelo no responda solo con su conocimiento interno.
WEB_SEARCH_TOOL_CHOICE = {"type": "tool", "name": "web_search"}

NO_RESULTS_MESSAGE = (
    "No encontré información relevante en la búsqueda web para responder esta pregunta."
)


class WebResearchAgent(BaseAgent):

    def __init__(self):
        super().__init__()
        # Claude Haiku para búsquedas web
        self.model = settings.claude_model_fast
        self.context_used = False

        self.definition = {
            "agent_name": "WebSearch_Agent",
            "description": "Agente especializado en recuperar informacion desde internet cuando sea necesario.",
            "role": "researcher",
            "skills": [
                # Web navigation
                "web_search",
                "search_engine_query",
                # URL navigation
                "fetch_url",
                "browser_navigation",
                # Clean trash HTML
                "html_parser",
                "readability_extractor",
                # JavaScript rendering
                "playwright",
                "selenium",
                "headless_browser",
                # Content extraction
                "content_extraction"

            ],
            "allowed_tools": [
                "websearch_tool"
            ],
            "expected inputs": (
                "Una pregunta del usuario que requiere información externa o actual, no "
                "contenida en los apuntes del curso (por ejemplo, noticias, versiones de "
                "software, eventos recientes)."
            ),
            "expected outputs": (
                "Una respuesta basada en los resultados de la búsqueda web, seguida de una "
                "lista de fuentes (URL y título) consultadas. Si la búsqueda no arroja "
                "resultados útiles, debe indicarlo explícitamente en vez de inventar contenido."
            ),
            "restrictions": [
                "Debe dar referencias a las que poder consultar.",
                "No debe inventar fuentes.",
                "Debe usar busqueda web."
            ],
            "example of a call": (
                'Entrada: "¿Cuál es la versión más reciente de PyTorch?"\n'
                'Salida: "La versión más reciente de PyTorch es la 2.x, lanzada en ...\n\n'
                'Fuentes:\n- https://pytorch.org/blog/... (PyTorch Release Notes)"'
            ),
            "language": "Mismo idioma que usa el prompt del usuario."
        }

    def run(self, prompt: str, context: str | None = None) -> str:
        self.context_used = False
        system_prompt = self._build_system_prompt(context)
        langfuse = get_langfuse_client()
        trace_messages = self._trace_messages(prompt, context, self.definition)

        if langfuse is None:
            answer, _, searched = self._search_and_answer(system_prompt, prompt)
            self.context_used = searched
            return answer

        with langfuse.start_as_current_observation(
            as_type="agent",
            name=self.name,
            input={"messages": trace_messages},
            metadata={
                "agent": self.name,
                "model": self.model,
                "allowed_tools": self.definition.get("allowed_tools", []),
            },
        ):
            answer, citations, searched = self._search_and_answer(
                system_prompt, prompt, trace=True
            )
            self.context_used = searched

            langfuse.update_current_span(
                output={
                    "messages": trace_messages + [{"role": "assistant", "content": answer}],
                    "citations": citations,
                },
            )

        flush_langfuse()
        return answer

    def _search_and_answer(
        self, system_prompt: str, prompt: str, trace: bool = False
    ) -> tuple[str, list[dict], bool]:
        langfuse = get_langfuse_client() if trace else None

        if langfuse is None:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}],
                tools=[WEB_SEARCH_TOOL],
                tool_choice=WEB_SEARCH_TOOL_CHOICE,
                temperature=0.3,
            )
            return self._parse_response(response)

        with langfuse.start_as_current_observation(
            as_type="generation",
            name="anthropic-web-search",
            model=self.model,
            input={"system": system_prompt, "user_message": prompt},
            model_parameters={"temperature": 0.3, "max_tokens": 1024, "tools": [WEB_SEARCH_TOOL["type"]]},
        ) as generation:
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=1024,
                    system=system_prompt,
                    messages=[{"role": "user", "content": prompt}],
                    tools=[WEB_SEARCH_TOOL],
                    tool_choice=WEB_SEARCH_TOOL_CHOICE,
                    temperature=0.3,
                )
            except Exception as error:
                record_exception(generation, error)
                raise

            answer, citations, searched = self._parse_response(response)

            generation.update(
                output={"messages": [{"role": "assistant", "content": answer}]},
                usage_details={
                    "input": response.usage.input_tokens,
                    "output": response.usage.output_tokens,
                },
                metadata={"web_search_performed": searched, "citations": citations},
            )
            return answer, citations, searched

    @staticmethod
    def _parse_response(response) -> tuple[str, list[dict], bool]:
        text_parts: list[str] = []
        citations: list[dict] = []
        searched = False

        for block in response.content:
            block_type = getattr(block, "type", None)
            if block_type in ("server_tool_use", "web_search_tool_result"):
                searched = True
            elif block_type == "text":
                text_parts.append(block.text)
                for citation in getattr(block, "citations", None) or []:
                    entry = {
                        "url": getattr(citation, "url", None),
                        "title": getattr(citation, "title", None),
                    }
                    if entry not in citations:
                        citations.append(entry)

        answer = "".join(text_parts).strip()

        if not answer or not searched:
            return NO_RESULTS_MESSAGE, [], searched

        if citations:
            sources = "\n".join(
                f"- {c['url']} ({c['title']})" if c.get("title") else f"- {c['url']}"
                for c in citations
                if c.get("url")
            )
            if sources and "Fuentes:" not in answer:
                answer = f"{answer}\n\nFuentes:\n{sources}"

        return answer, citations, searched
