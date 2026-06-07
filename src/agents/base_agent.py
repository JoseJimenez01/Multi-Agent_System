from openai import OpenAI
from langfuse import Langfuse

from src.config import settings


class BaseAgent:
    name: str = "base"
    description: str = "Base agent"
    system_prompt: str = "You are a helpful AI assistant."

    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
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
        messages = [{"role": "system", "content": self._build_system_prompt(context)}]
        messages.append({"role": "user", "content": prompt})

        trace = self.langfuse.trace(name=self.name) if self.langfuse else None
        generation = trace.generation(name="run", model=self.model) if trace else None

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3,
        )

        if generation:
            generation.end(output=response.choices[0].message.content)

        return response.choices[0].message.content

    def _build_system_prompt(self, context: str | None = None) -> str:
        if context:
            return f"{self.system_prompt}\n\nContexto recuperado:\n{context}"
        return self.system_prompt
