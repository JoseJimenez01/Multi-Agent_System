from .base_agent import BaseAgent


class ResearchAgent(BaseAgent):
    name = "research"
    description = "Investigación y búsqueda de información"
    system_prompt = """Eres un agente experto en investigación. Tu tarea es:
1. Buscar información precisa y relevante
2. Sintetizar datos de múltiples fuentes
3. Presentar hallazgos de forma estructurada
4. Citar fuentes cuando sea posible

Responde en el mismo idioma de la consulta del usuario."""
