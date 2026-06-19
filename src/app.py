import sys
import uuid
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from src.orchestrator import Orchestrator

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


orchestrator = init_orchestrator()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "conversations" not in st.session_state:
    st.session_state.conversations = []

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

left, right = st.columns([1, 2.5], gap="medium")

with left:
    st.markdown("##### Conversaciones")
    st.markdown("---")
    if not st.session_state.conversations:
        st.caption("Aún no hay conversaciones")
    else:
        for i, conv in enumerate(reversed(st.session_state.conversations), 1):
            preview = conv["first_msg"][:50] + ("..." if len(conv["first_msg"]) > 50 else "")
            st.markdown(f"**{preview}**  \n{conv['count']} mensajes  \n:gray[{conv['time']}]")
            st.markdown("---")

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

        conversation_entry = {
            "first_msg": st.session_state.messages[0]["content"],
            "count": len(st.session_state.messages) // 2,
            "time": datetime.now(ZoneInfo("America/Mexico_City")).strftime("%H:%M"),
        }
        existing = next(
            (c for c in st.session_state.conversations if c["session_id"] == st.session_state.session_id),
            None,
        )
        if existing is None:
            conversation_entry["session_id"] = st.session_state.session_id
            st.session_state.conversations.append(conversation_entry)
        else:
            existing.update(conversation_entry)

        st.rerun()
