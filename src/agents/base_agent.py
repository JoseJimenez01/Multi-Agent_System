from anthropic import Anthropic
from langfuse import Langfuse

from src.config import settings


class BaseAgent:
    name: str = "base"
    description: str = "Base agent"
    system_prompt: str = "You are a helpful AI assistant."

    def __init__(self):
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.claude_model_primary  # Claude Sonnet por defecto para orquestador
        self.langfuse = (
            Langfuse(
                public_key=settings.langfuse_public_key,
                secret_key=settings.langfuse_secret_key,
                host=settings.langfuse_host,
            )
            if settings.langfuse_public_key and settings.langfuse_secret_key
            else None
        )

    def run(self, prompt: str, context: str | None = None) -> str:
        system_prompt = self._build_system_prompt(context)

        trace = self.langfuse.trace(name=self.name) if self.langfuse else None
        generation = trace.generation(name="run", model=self.model) if trace else None

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )

        result_text = response.content[0].text

        if generation:
            generation.end(output=result_text)

        return result_text

    def _build_system_prompt(self, context: str | None = None) -> str:
        if context:
            return f"{self.system_prompt}\n\nContexto recuperado:\n{context}"
        return self.system_prompt
