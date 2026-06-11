from src.config.settings import configure_langfuse_env

configure_langfuse_env()

from anthropic import Anthropic

from src.config import settings
from src.observability.langfuse_tracing import flush_langfuse, get_langfuse_client, traced


class BaseAgent:
    name: str = "base"
    description: str = "Base agent"

    def __init__(self):
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.claude_model_primary
        self.definition = {
            "agent_name": "General_Agent",
            "description": (
                "Asistente IA versátil. Responde cualquier consulta "
                "de forma clara, precisa y en el mismo idioma de la pregunta."
            ),
            "role": "assistant",
            "skills": ["general_qa", "reasoning", "multilingual_response"],
            "allowed_tools": [],
            "expected inputs": "",
            "expected outputs": "",
            "restrictions": [],
            "example of a call": "",
            "language": "Mismo idioma que usa el prompt del usuario.",
        }

    @staticmethod
    def definition_to_system_prompt(definition: dict) -> str:
        lines = []

        if agent_name := definition.get("agent_name"):
            lines.append(f"Eres {agent_name}.")
        if desc := definition.get("description"):
            lines.append(desc)
        if role := definition.get("role"):
            lines.append(f"Tu rol es: {role}.")

        if skills := definition.get("skills"):
            lines.append("Habilidades:")
            lines.extend(f"- {skill}" for skill in skills)

        if tools := definition.get("allowed_tools"):
            lines.append("Herramientas permitidas:")
            lines.extend(f"- {tool}" for tool in tools)

        if restrictions := definition.get("restrictions"):
            lines.append("Restricciones:")
            lines.extend(f"- {restriction}" for restriction in restrictions)

        if language := definition.get("language"):
            lines.append(f"Idioma: {language}")

        return "\n".join(lines)

    @traced(as_type="agent", capture_input=False, capture_output=False)
    def run(self, prompt: str, context: str | None = None) -> str:
        system_prompt = self._build_system_prompt(context)
        langfuse = get_langfuse_client()

        if langfuse is not None:
            langfuse.update_current_span(
                name=self.name,
                input={"prompt": prompt, "has_context": context is not None},
                metadata={"agent": self.name, "model": self.model},
            )

        if langfuse is None:
            result_text, _ = self._call_llm(system_prompt, prompt)
            return result_text

        with langfuse.start_as_current_observation(
            as_type="generation",
            name="anthropic-completion",
            model=self.model,
            input={"user_message": prompt},
            model_parameters={"temperature": 0.3, "max_tokens": 2048},
        ) as generation:
            result_text, usage = self._call_llm(system_prompt, prompt)
            generation.update(
                output=result_text,
                usage_details={
                    "input": usage.input_tokens,
                    "output": usage.output_tokens,
                },
            )
            langfuse.update_current_span(output={"response": result_text})

        flush_langfuse()
        return result_text

    def _call_llm(self, system_prompt: str, prompt: str) -> tuple[str, object]:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        return response.content[0].text, response.usage

    def _build_system_prompt(self, context: str | None = None) -> str:
        prompt = self.definition_to_system_prompt(self.definition)
        if context:
            return f"{prompt}\n\nContexto recuperado:\n{context}"
        return prompt
