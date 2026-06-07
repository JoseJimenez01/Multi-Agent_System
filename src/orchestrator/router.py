from src.agents import ResearchAgent, CodingAgent, AnalysisAgent
from src.agents.base_agent import BaseAgent
from src.database import VectorStore, DatabaseManager
from src.config import settings


class Orchestrator:
    def __init__(self):
        self.vector_store = VectorStore()
        self.db = DatabaseManager()
        self.agent_map = {
            "research": ResearchAgent(),
            "coding": CodingAgent(),
            "analysis": AnalysisAgent(),
            "general": BaseAgent(),
        }
        self.agent_map["general"].name = "general"
        self.agent_map["general"].system_prompt = (
            "Eres un asistente IA versátil. Responde cualquier consulta "
            "de forma clara, precisa y en el mismo idioma de la pregunta."
        )

    def route(self, prompt: str) -> dict:
        task_type = self._classify_task(prompt)
        collection_name = f"knowledge_{task_type}"
        self.vector_store.ensure_collection(collection_name)

        context = self._retrieve_context(prompt, collection_name)

        if context:
            result = self._execute_agent_with_context(task_type, prompt, context)
            agent_name = self.agent_map[task_type].name
            return {"result": result, "context_used": True, "agent": agent_name}

        result = self._execute_agent(task_type, prompt)

        self._store_in_vector_db(prompt, result, collection_name)
        agent_name = self.agent_map[task_type].name
        return {"result": result, "context_used": False, "agent": agent_name}

    def _classify_task(self, prompt: str) -> str:
        prompt_lower = prompt.lower()
        code_kw = ["codigo", "código", "function", "class", "implementar",
                    "programar", "debug", "bug", "script", "api", "endpoint",
                    "algoritmo", "python", "javascript", "typescript", "html",
                    "css", "docker", "git", "codew", "escribe un", "programa"]
        research_kw = ["investigar", "buscar", "research", "search", "qué es",
                       "quien es", "historia", "significa", "definición",
                       "definicion", "concepto", "explain", "what is",
                       "tell me about", "información", "investiga"]
        analysis_kw = ["analizar", "analiza", "analysis", "analyze", "reporte",
                       "report", "tendencia", "trend", "comparar", "compare",
                       "estadística", "statistics", "datos", "data", "métrica",
                       "metric", "analisis", "análisis"]

        scores = {
            "coding": sum(1 for kw in code_kw if kw in prompt_lower),
            "research": sum(1 for kw in research_kw if kw in prompt_lower),
            "analysis": sum(1 for kw in analysis_kw if kw in prompt_lower),
        }
        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else "general"

    def _retrieve_context(self, prompt: str, collection_name: str) -> str | None:
        try:
            embedding = self._get_embedding(prompt)
            results = self.vector_store.search(
                collection_name=collection_name,
                query_vector=embedding,
                limit=3,
                score_threshold=0.75,
            )
            if results:
                return "\n\n".join(r.payload.get("text", "") for r in results if r.payload)
        except Exception:
            pass
        return None

    def _execute_agent(self, task_type: str, prompt: str) -> str:
        agent = self.agent_map.get(task_type)
        if not agent:
            return f"No se encontró un agente para la tarea: {task_type}"

        task_id = self.db.log_task(task_type, prompt, agent_used=agent.name, status="processing")

        try:
            result = agent.run(prompt)
            self.db.log_task(
                task_type, prompt, agent_used=agent.name,
                status="completed", result_text=result,
            )
            return result
        except Exception as e:
            self.db.log_task(
                task_type, prompt, agent_used=agent.name,
                status="failed", result_text=str(e),
            )
            raise

    def _execute_agent_with_context(self, task_type: str, prompt: str, context: str) -> str:
        agent = self.agent_map.get(task_type)
        if not agent:
            return f"No se encontró un agente para la tarea: {task_type}"

        self.db.log_task(
            task_type, prompt, agent_used=agent.name,
            status="processing", result_text="Usando contexto de base vectorial",
        )
        result = agent.run(prompt, context=context)
        self.db.log_task(
            task_type, prompt, agent_used=agent.name,
            status="completed", result_text=result,
        )
        return result

    def _get_embedding(self, text: str) -> list[float]:
        from openai import OpenAI
        client = OpenAI(api_key=settings.openai_api_key)
        resp = client.embeddings.create(model=settings.embedding_model, input=text)
        return resp.data[0].embedding

    def _store_in_vector_db(self, prompt: str, result: str, collection_name: str):
        from qdrant_client import models
        import uuid

        embedding = self._get_embedding(prompt)
        point = models.PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={"question": prompt, "text": result},
        )
        self.vector_store.upsert(collection_name, [point])
