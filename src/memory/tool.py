"""memory_tool: las 4 operaciones de memoria histórica que exige la especificación
(III-J), expuestas como tools de Anthropic para que el SummarizerAgent las invoque.

Los datos crudos los resuelve `src.memory.db`; este módulo solo arma la
respuesta que se le devuelve al LLM (incluyendo el caso de BD no disponible).
"""

import re

from . import db as memory_db

_DB_UNAVAILABLE = "memoria histórica no disponible en este momento (sin conexión a la base de datos)."

_STOPWORDS = {
    "que", "el", "la", "los", "las", "de", "del", "en", "un", "una", "y", "o",
    "es", "con", "para", "por", "sobre", "esta", "esto", "como", "que", "cual",
    "cuales", "mas", "se", "su", "sus", "lo", "ya", "hoy", "habiamos",
}


def _strip_accents(text: str) -> str:
    replacements = str.maketrans("áéíóúñ", "aeioun")
    return text.lower().translate(replacements)


def _keywords(text: str, min_len: int = 4, max_keywords: int = 5) -> list[str]:
    words = re.findall(r"[a-zA-ZáéíóúñÁÉÍÓÚÑ]+", text)
    seen: list[str] = []
    for word in words:
        normalized = _strip_accents(word)
        if len(normalized) >= min_len and normalized not in _STOPWORDS and normalized not in seen:
            seen.append(normalized)
        if len(seen) >= max_keywords:
            break
    return seen


def search_history(query: str, limit: int = 5) -> dict:
    """Busca en mensajes anteriores (de cualquier sesión) que contengan el texto indicado."""
    results = memory_db.search_messages(query, limit=limit)
    if results is None:
        return {"error": _DB_UNAVAILABLE}
    return {"query": query, "matches": results}


def summarize_current_session(session_id: str, fallback_history: list[dict] | None = None) -> dict:
    """Obtiene los mensajes de la sesión actual para que el agente los resuma."""
    messages = memory_db.get_session_messages(session_id)
    if messages is not None:
        return {"session_id": session_id, "message_count": len(messages), "messages": messages, "source": "db"}

    fallback = [
        {"role": m.get("role"), "content": m.get("content"), "agent_used": m.get("agent")}
        for m in (fallback_history or [])
    ]
    return {
        "session_id": session_id,
        "message_count": len(fallback),
        "messages": fallback,
        "source": "session_ram_fallback",
    }


def compare_with_previous(current_question: str, session_id: str, limit: int = 3) -> dict:
    """Busca preguntas similares de sesiones pasadas (excluye la sesión actual) para comparar."""
    keywords = _keywords(current_question) or [current_question]
    results: list[dict] = []
    seen_ids = set()
    db_failed = False

    for kw in keywords:
        matches = memory_db.search_messages(kw, limit=limit, exclude_session_id=session_id)
        if matches is None:
            db_failed = True
            continue
        for row in matches:
            if row.get("role") != "user" or row["id"] in seen_ids:
                continue
            seen_ids.add(row["id"])
            results.append(row)
        if len(results) >= limit:
            break

    if not results and db_failed:
        return {"error": _DB_UNAVAILABLE}

    return {"current_question": current_question, "previous_matches": results[:limit]}


def search_by_agent_and_date(agent_used: str, date: str) -> dict:
    """Busca interacciones de un agente específico en una fecha exacta (YYYY-MM-DD)."""
    results = memory_db.search_by_agent_and_date(agent_used, date)
    if results is None:
        return {"error": _DB_UNAVAILABLE}
    return {"agent_used": agent_used, "date": date, "matches": results}


MEMORY_TOOL_FUNCTIONS = {
    "search_history": search_history,
    "summarize_current_session": summarize_current_session,
    "compare_with_previous": compare_with_previous,
    "search_by_agent_and_date": search_by_agent_and_date,
}

MEMORY_TOOLS_SCHEMA = [
    {
        "name": "search_history",
        "description": (
            "Busca en mensajes anteriores (de cualquier sesión, pasada o actual) que "
            "contengan un texto o concepto. Úsala para preguntas tipo "
            "'¿qué pregunté antes sobre X?'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Texto o concepto a buscar."},
                "limit": {"type": "integer", "description": "Máximo de resultados (default 5)."},
            },
            "required": ["query"],
        },
    },
    {
        "name": "summarize_current_session",
        "description": (
            "Obtiene todos los mensajes de la sesión actual para poder resumirlos. "
            "Úsala para 'resume las preguntas de esta sesión'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "ID de la sesión actual."},
            },
            "required": ["session_id"],
        },
    },
    {
        "name": "compare_with_previous",
        "description": (
            "Busca preguntas similares hechas en sesiones pasadas (no la actual) para "
            "compararlas con la pregunta actual. Úsala para 'compara esta pregunta con una anterior'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "current_question": {"type": "string"},
                "session_id": {
                    "type": "string",
                    "description": "ID de la sesión actual (se excluye de la búsqueda).",
                },
                "limit": {"type": "integer"},
            },
            "required": ["current_question", "session_id"],
        },
    },
    {
        "name": "search_by_agent_and_date",
        "description": (
            "Busca interacciones atendidas por un agente específico en una fecha exacta. "
            "Úsala para '¿ya habíamos consultado transacciones sospechosas hoy?' "
            "(agent_used='transactional', date=hoy)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "agent_used": {
                    "type": "string",
                    "enum": ["rag", "web", "transactional", "summarizer"],
                },
                "date": {"type": "string", "description": "Fecha en formato YYYY-MM-DD."},
            },
            "required": ["agent_used", "date"],
        },
    },
]
