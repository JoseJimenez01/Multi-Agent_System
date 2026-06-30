"""LLM-as-a-judge: evalúa equivalencia semántica usando un modelo de OpenAI.

Complementa la heurística keyword_match_ratio: juzga si la respuesta del
agente es correcta por significado, no por coincidencia literal de palabras.
Útil para fórmulas matemáticas, respuestas dinámicas (transaccionales) y
criterios descriptivos en lenguaje natural.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from openai import OpenAI
from src.config import settings

_client = OpenAI(api_key=settings.openai_api_key)

_SYSTEM_PROMPT = """Eres un evaluador experto de respuestas de un sistema de \
IA educativo. Tu tarea es decidir si la respuesta del agente es CORRECTA \
respecto a una referencia.

Juzga por EQUIVALENCIA DE SIGNIFICADO y CUMPLIMIENTO DEL CRITERIO, no por \
coincidencia literal de palabras. En particular:
- Una fórmula en notación distinta (LaTeX vs texto plano) que representa lo \
mismo es CORRECTA.
- Detalle adicional correcto no invalida la respuesta.
- Diferencias de fraseo, orden o formato no importan.
Sé ESTRICTO cuando la respuesta del agente omite información esencial de la \
referencia, la contradice, o no cumple el comportamiento descrito en el criterio.

Responde ÚNICAMENTE con un objeto JSON válido, sin texto adicional ni \
markdown, con esta forma exacta:
{"veredicto": true/false, "justificacion": "1-2 frases explicando por qué"}"""


def judge_answer(pregunta: str, referencia: str, respuesta_real: str,
                 modo: str = "contenido") -> dict:
    """Juzga si respuesta_real es correcta respecto a la referencia.

    modo="contenido": la referencia es una respuesta_esperada (texto modelo).
    modo="rubrica":   la referencia es un criterio_de_exito (comportamiento).
    Devuelve {"veredicto": bool, "justificacion": str}. Ante error de API o
    parseo, devuelve veredicto=None y la justificación con el error, para no
    romper la corrida.
    """
    if modo == "rubrica":
        ref_label = "CRITERIO DE ÉXITO (comportamiento esperado)"
    else:
        ref_label = "RESPUESTA ESPERADA (referencia de contenido)"

    user_prompt = (
        f"PREGUNTA:\n{pregunta}\n\n"
        f"{ref_label}:\n{referencia}\n\n"
        f"RESPUESTA DEL AGENTE:\n{respuesta_real}\n\n"
        f"¿La respuesta del agente es correcta? Responde solo con el JSON."
    )

    try:
        resp = _client.chat.completions.create(
            model=settings.openai_judge_model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
            max_tokens=200,
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content
        data = json.loads(raw)
        return {
            "veredicto": bool(data.get("veredicto")),
            "justificacion": str(data.get("justificacion", "")),
        }
    except Exception as e:  # noqa: BLE001
        return {"veredicto": None, "justificacion": f"error del juez: {e}"}