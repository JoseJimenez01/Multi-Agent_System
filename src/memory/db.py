"""Capa de persistencia para la memoria conversacional e histórica (III-J).

Usa el mismo Postgres que ya despliega el MCP Server (`settings.database_url`),
pero en el schema `memory` para no colisionar con el schema `banco`.

Toda función pública atrapa sus propios errores de conexión/consulta: si la
BD no está disponible, registra el error y devuelve un valor de respaldo
(`None` para indicar "no se pudo leer" vs. `[]`/`False` para "no hay datos"),
de modo que el resto del sistema pueda seguir funcionando solo con la
memoria de sesión en RAM.
"""

import logging
from pathlib import Path
from typing import Any

from psycopg2.extras import Json

from src.config import settings
from src.database.postgres.postgres import PostgresDB

logger = logging.getLogger("memory_db")

_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "database" / "postgres" / "memory_schema.sql"

_db = PostgresDB(settings.database_url)


def init_schema() -> bool:
    """Crea el schema/tablas de memoria si no existen. Seguro de re-correr."""
    try:
        _db.execute_query(_SCHEMA_PATH.read_text(encoding="utf-8"))
        return True
    except Exception as exc:
        logger.error("No se pudo inicializar el schema de memoria: %s", exc)
        return False


def ensure_session(session_id: str) -> bool:
    try:
        _db.execute_query(
            """
            INSERT INTO memory.sessions (session_id)
            VALUES (%s)
            ON CONFLICT (session_id) DO UPDATE SET updated_at = now()
            """,
            (session_id,),
        )
        return True
    except Exception as exc:
        logger.error("ensure_session(%s) fallo: %s", session_id, exc)
        return False


def save_message(
    session_id: str,
    role: str,
    content: str,
    agent_used: str | None = None,
    metadata: dict | None = None,
) -> bool:
    try:
        ensure_session(session_id)
        _db.execute_query(
            """
            INSERT INTO memory.messages (session_id, role, content, agent_used, metadata)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (session_id, role, content, agent_used, Json(metadata) if metadata is not None else None),
        )
        return True
    except Exception as exc:
        logger.error("save_message(%s) fallo: %s", session_id, exc)
        return False


def get_session_messages(session_id: str) -> list[dict] | None:
    """Devuelve los mensajes de una sesión. None si la BD no está disponible."""
    try:
        return _db.execute_query(
            """
            SELECT id, session_id, timestamp, role, content, agent_used, metadata
            FROM memory.messages
            WHERE session_id = %s
            ORDER BY timestamp ASC, id ASC
            """,
            (session_id,),
        )
    except Exception as exc:
        logger.error("get_session_messages(%s) fallo: %s", session_id, exc)
        return None


def search_messages(
    query_text: str,
    limit: int = 10,
    exclude_session_id: str | None = None,
) -> list[dict] | None:
    """Busca mensajes por coincidencia de texto. None si la BD no está disponible."""
    try:
        params: list[Any] = [f"%{query_text}%"]
        exclude_clause = ""
        if exclude_session_id:
            exclude_clause = "AND session_id != %s"
            params.append(exclude_session_id)
        params.append(limit)

        return _db.execute_query(
            f"""
            SELECT id, session_id, timestamp, role, content, agent_used
            FROM memory.messages
            WHERE content ILIKE %s {exclude_clause}
            ORDER BY timestamp DESC
            LIMIT %s
            """,
            tuple(params),
        )
    except Exception as exc:
        logger.error("search_messages(%r) fallo: %s", query_text, exc)
        return None


def search_by_agent_and_date(agent_used: str, date_str: str) -> list[dict] | None:
    """Busca mensajes de un agente en una fecha (YYYY-MM-DD). None si falla la BD."""
    try:
        return _db.execute_query(
            """
            SELECT id, session_id, timestamp, role, content, agent_used
            FROM memory.messages
            WHERE agent_used = %s AND timestamp::date = %s::date
            ORDER BY timestamp DESC
            """,
            (agent_used, date_str),
        )
    except Exception as exc:
        logger.error("search_by_agent_and_date(%s, %s) fallo: %s", agent_used, date_str, exc)
        return None


def save_session_summary(session_id: str, summary_text: str) -> bool:
    try:
        ensure_session(session_id)
        _db.execute_query(
            "UPDATE memory.sessions SET summary = %s, updated_at = now() WHERE session_id = %s",
            (summary_text, session_id),
        )
        return True
    except Exception as exc:
        logger.error("save_session_summary(%s) fallo: %s", session_id, exc)
        return False


def get_recent_sessions(n: int = 5) -> list[dict] | None:
    try:
        return _db.execute_query(
            """
            SELECT session_id, created_at, updated_at, summary
            FROM memory.sessions
            ORDER BY updated_at DESC
            LIMIT %s
            """,
            (n,),
        )
    except Exception as exc:
        logger.error("get_recent_sessions fallo: %s", exc)
        return None


def get_recent_sessions_with_preview(limit: int = 10) -> list[dict] | None:
    """Sesiones recientes con su primer mensaje y conteo total, para listarlas en la UI."""
    try:
        return _db.execute_query(
            """
            SELECT
                s.session_id,
                s.updated_at,
                s.summary,
                fm.content AS first_message,
                COUNT(m.id) AS message_count
            FROM memory.sessions s
            LEFT JOIN memory.messages m ON m.session_id = s.session_id
            LEFT JOIN LATERAL (
                SELECT content FROM memory.messages
                WHERE session_id = s.session_id AND role = 'user'
                ORDER BY timestamp ASC
                LIMIT 1
            ) fm ON true
            GROUP BY s.session_id, s.updated_at, s.summary, fm.content
            ORDER BY s.updated_at DESC
            LIMIT %s
            """,
            (limit,),
        )
    except Exception as exc:
        logger.error("get_recent_sessions_with_preview fallo: %s", exc)
        return None


if __name__ == "__main__":
    print("Inicializando schema de memoria en:", settings.database_url)
    print("OK" if init_schema() else "FALLÓ — revisá la conexión a Postgres.")
