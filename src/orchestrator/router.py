from contextlib import nullcontext

from src.config.settings import configure_langfuse_env

configure_langfuse_env()

from langfuse import propagate_attributes

from src.agents import RagAgent, WebResearchAgent, SummarizerAgent, TransactionalAgent
from src.agents.base_agent import BaseAgent
from src.database import VectorStore, DatabaseManager
from src.config import settings
from src.observability.langfuse_tracing import flush_langfuse, get_langfuse_client, is_tracing_enabled, traced


class Orchestrator:
    def __init__(self):
        self.vector_store = VectorStore()
        self.db = DatabaseManager()
        self.agent_map = {
            "coding": RagAgent(),
            "research": WebResearchAgent(),
            "analysis": SummarizerAgent(),
            "transactional": TransactionalAgent(),
            "general": BaseAgent(),
        }
        self.agent_map["coding"].name = "rag"
        self.agent_map["research"].name = "web_research"
        self.agent_map["analysis"].name = "summarizer"
        self.agent_map["transactional"].name = "transactional"
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

        task_context = (
            propagate_attributes(tags=[f"task:{task_type}"], metadata={"task_type": task_type})
            if is_tracing_enabled()
            else nullcontext()
        )
        with task_context:
            collection_name = f"knowledge_{task_type}"
            self.vector_store.ensure_collection(collection_name)

            context = self._retrieve_context(prompt, collection_name)

            if context:
                result = self._execute_agent_with_context(task_type, prompt, context, session_id)
                agent_name = self._get_agent(task_type).name
                response = {"result": result, "context_used": True, "agent": agent_name}
            else:
                result = self._execute_agent(task_type, prompt, session_id)
                self._store_in_vector_db(prompt, result, collection_name)
                agent_name = self._get_agent(task_type).name
                response = {"result": result, "context_used": False, "agent": agent_name}

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

    @traced(as_type="span", name="classify-task")
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
        task_type = best if scores[best] > 0 else "general"

        langfuse = get_langfuse_client()
        if langfuse is not None:
            langfuse.update_current_span(output={"task_type": task_type, "scores": scores})

        return task_type

    @traced(as_type="retriever", name="retrieve-context", capture_input=False)
    def _retrieve_context(self, prompt: str, collection_name: str) -> str | None:
        langfuse = get_langfuse_client()
        if langfuse is not None:
            langfuse.update_current_span(
                input={"prompt": prompt, "collection": collection_name},
            )

        try:
            embedding = self._get_embedding(prompt)
            results = self.vector_store.search(
                collection_name=collection_name,
                query_vector=embedding,
                limit=3,
                score_threshold=0.75,
            )
            if results:
                context = "\n\n".join(r.payload.get("text", "") for r in results if r.payload)
                if langfuse is not None:
                    langfuse.update_current_span(
                        output={"chunks_found": len(results), "has_context": True},
                    )
                return context
        except Exception as exc:
            if langfuse is not None:
                langfuse.update_current_span(
                    level="WARNING",
                    status_message=str(exc),
                    output={"has_context": False},
                )
        return None

    def _execute_agent(self, task_type: str, prompt: str, session_id: str) -> str:
        agent = self._get_agent(task_type)

        self.db.log_task(
            task_type, prompt, session_id, agent_used=agent.name, status="processing"
        )

        try:
            result = agent.run(prompt)
            self.db.log_task(
                task_type, prompt, session_id, agent_used=agent.name,
                status="completed", result_text=result,
            )
            return result
        except Exception as e:
            self.db.log_task(
                task_type, prompt, session_id, agent_used=agent.name,
                status="failed", result_text=str(e),
            )
            raise

    def _execute_agent_with_context(
        self, task_type: str, prompt: str, context: str, session_id: str
    ) -> str:
        agent = self._get_agent(task_type)

        self.db.log_task(
            task_type, prompt, session_id, agent_used=agent.name,
            status="processing", result_text="Usando contexto de base vectorial",
        )
        result = agent.run(prompt, context=context)
        self.db.log_task(
            task_type, prompt, session_id, agent_used=agent.name,
            status="completed", result_text=result,
        )
        return result

    @traced(as_type="embedding", name="openai-embedding", capture_input=False, capture_output=False)
    def _get_embedding(self, text: str) -> list[float]:
        from openai import OpenAI

        langfuse = get_langfuse_client()
        if langfuse is not None:
            langfuse.update_current_span(
                input={"text_preview": text[:200]},
                metadata={"model": settings.embedding_model},
            )

        client = OpenAI(api_key=settings.openai_api_key)
        resp = client.embeddings.create(model=settings.embedding_model, input=text)

        if langfuse is not None:
            usage = resp.usage
            langfuse.update_current_span(
                output={
                    "dimensions": len(resp.data[0].embedding),
                    "prompt_tokens": usage.prompt_tokens,
                    "total_tokens": usage.total_tokens,
                },
                metadata={"model": settings.embedding_model},
            )

        return resp.data[0].embedding

    @traced(as_type="span", name="store-vector", capture_input=False)
    def _store_in_vector_db(self, prompt: str, result: str, collection_name: str):
        from qdrant_client import models
        import uuid

        langfuse = get_langfuse_client()
        if langfuse is not None:
            langfuse.update_current_span(
                input={"collection": collection_name, "prompt_preview": prompt[:200]},
            )

        embedding = self._get_embedding(prompt)
        point = models.PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={"question": prompt, "text": result},
        )
        self.vector_store.upsert(collection_name, [point])

        if langfuse is not None:
            langfuse.update_current_span(output={"stored": True, "collection": collection_name})
