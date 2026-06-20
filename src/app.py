import sys
import uuid
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from src.orchestrator import Orchestrator
from src.memory import db as memory_db

st.set_page_config(page_title="Multi-Agent System", layout="wide")

HIDE_STREAMLIT = """
<style>
    .stAppDeployButton, #MainMenu, footer, header {display: none !important;}
    div[data-testid="stToolbar"] {display: none;}
    .viewerBadge_container__1QSob, .stActionButton {display: none !important;}
</style>
"""
st.markdown(HIDE_STREAMLIT, unsafe_allow_html=True)


def greeting():
    hour = datetime.now(ZoneInfo("America/Mexico_City")).hour
    if 6 <= hour < 12:
        return "Buenos días"
    if 12 <= hour < 18:
        return "Buenas tardes"
    return "Buenas noches"


@st.cache_resource
def init_orchestrator():
    return Orchestrator()


def _messages_from_db(session_id: str) -> list[dict]:
    """Mapea filas de memory.messages al shape que usa la UI. [] si no hay BD/datos."""
    db_messages = memory_db.get_session_messages(session_id)
    return [
        {
            "role": m["role"],
            "content": m["content"],
            "agent": m.get("agent_used"),
            "context_used": bool((m.get("metadata") or {}).get("context_used")),
        }
        for m in (db_messages or [])
    ]


def _switch_session(session_id: str) -> None:
    st.session_state.session_id = session_id
    st.query_params["session_id"] = session_id
    st.session_state.messages = _messages_from_db(session_id)


orchestrator = init_orchestrator()

if "session_id" not in st.session_state:
    # F5 reconecta el WebSocket y Streamlit arranca st.session_state desde cero,
    # pero la URL (vía st.query_params) sí sobrevive al refresh. La usamos como
    # ancla: si ya trae un session_id, es un refresh de una sesión existente y
    # recuperamos su historial de memory.messages; si no, es una pestaña nueva.
    query_session_id = st.query_params.get("session_id")

    if query_session_id:
        st.session_state.session_id = query_session_id
        st.session_state.messages = _messages_from_db(query_session_id)
    else:
        st.session_state.session_id = str(uuid.uuid4())
        st.query_params["session_id"] = st.session_state.session_id
        st.session_state.messages = []

left, right = st.columns([1, 2.5], gap="medium")

with left:
    st.markdown("##### Conversaciones")

    if st.button("+ Nueva conversación", use_container_width=True):
        _switch_session(str(uuid.uuid4()))
        st.rerun()

    st.markdown("---")

    past_sessions = memory_db.get_recent_sessions_with_preview(15)

    if past_sessions is None:
        st.caption("Memoria histórica no disponible (sin conexión a la base de datos).")
    elif not past_sessions:
        st.caption("Aún no hay conversaciones guardadas.")
    else:
        for s in past_sessions:
            first_message = s.get("first_message") or "(sin mensajes)"
            preview = first_message[:45] + ("..." if len(first_message) > 45 else "")
            turns = (s.get("message_count") or 0) // 2
            is_active = s["session_id"] == st.session_state.session_id

            label = f"{'➤ ' if is_active else ''}{preview} · {turns} mensajes"
            if st.button(label, key=f"conv_{s['session_id']}", use_container_width=True, disabled=is_active):
                _switch_session(s["session_id"])
                st.rerun()

with right:
    st.markdown(f"## {greeting()}")
    st.markdown("---")

    chat = st.container(height=400)
    with chat:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg.get("agent"):
                    st.caption(f"Agente: {msg['agent']}")
                if msg.get("context_used"):
                    st.caption(":blue[Usó contexto de base vectorial]")

    prompt = st.chat_input("Escribe tu mensaje...")

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat:
            with st.chat_message("user"):
                st.markdown(prompt)

        with chat:
            with st.chat_message("assistant"):
                with st.status("Pensando...", expanded=False) as status:
                    status.write("Clasificando tarea con IA...")
                    history = st.session_state.messages[:-1]
                    response = orchestrator.route(prompt, st.session_state.session_id, history=history)
                    status.write("Respuesta lista")

                st.markdown(response["result"])
                st.caption(f"Agente: {response['agent']}")
                if response["context_used"]:
                    st.caption(":blue[Usó contexto de base vectorial]")

        st.session_state.messages.append({
            "role": "assistant",
            "content": response["result"],
            "agent": response["agent"],
            "context_used": response["context_used"],
        })

        st.rerun()
