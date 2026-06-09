from .base_agent import BaseAgent
from src.config import settings


class WebResearchAgent(BaseAgent):

    def __init__(self):
        super().__init__()
        # Claude Haiku para búsquedas web
        self.model = settings.claude_model_fast

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
            "expected inputs": "",
            "expected outputs": "",
            "restrictions": [
                "Debe dar referencias a las que poder consultar.",
                "No debe inventar fuentes.",
                "Debe usar busqueda web."
            ],
            "example of a call": "",
            "language": "Mismo idioma que usa el prompt del usuario."
        }
