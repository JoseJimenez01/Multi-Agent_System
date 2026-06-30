"""Corre el conjunto de evaluación completo (IV de la especificación) contra el
Orquestador real (no agentes sueltos), por categoría, y registra agente usado,
contexto fundamentado, latencia, y un chequeo (heurístico) de si la respuesta
coincide con el criterio de éxito esperado.

Las preguntas 'transactional' (pending_mcp=true) se listan pero NO se corren
todavía, porque el agente Transaccional depende del MCP en desarrollo.

El chequeo de contenido para 'factual'/'comparacion' es un proxy heurístico
(coincidencia de palabras clave entre la respuesta y respuesta_esperada), NO
una verificación semántica real — está pensado para priorizar revisión manual,
no para reemplazarla. Para 'fuera_de_alcance' y 'web_search'/'transactional'
el chequeo es estructural (agente correcto, mensaje exacto, etc.) y sí es
confiable.

Uso:
    python -m eval.run_eval_set
"""

import csv
import json
import re
import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.orchestrator.router import Orchestrator, OUT_OF_SCOPE_MESSAGE, OUT_OF_SCOPE
from eval.llm_judge import judge_answer

QUESTIONS_PATH = Path(__file__).resolve().parent / "questions.json"
RESULTS_PATH = Path(__file__).resolve().parent / "eval_results.json"
SUMMARY_CSV_PATH = Path(__file__).resolve().parent / "eval_summary.csv"

_STOPWORDS = {
    "que", "el", "la", "los", "las", "de", "del", "en", "un", "una", "y", "o",
    "es", "con", "para", "por", "sobre", "esta", "esto", "como", "cual",
    "cuales", "mas", "se", "su", "sus", "lo", "segun", "los", "al", "a",
}


def _strip_accents(text: str) -> str:
    return text.lower().translate(str.maketrans("áéíóúñ", "aeioun"))


def _keywords(text: str, min_len: int = 4) -> set[str]:
    words = re.findall(r"[a-zA-ZáéíóúñÁÉÍÓÚÑ0-9]+", text)
    return {
        _strip_accents(w) for w in words
        if len(w) >= min_len and _strip_accents(w) not in _STOPWORDS
    }


def keyword_match_ratio(respuesta: str, esperada: str) -> float:
    """Proxy heurístico: % de palabras clave de la respuesta esperada que
    aparecen (como substring normalizado) en la respuesta del agente."""
    expected_kw = _keywords(esperada)
    if not expected_kw:
        return 0.0
    respuesta_norm = _strip_accents(respuesta)
    found = sum(1 for kw in expected_kw if kw in respuesta_norm)
    return round(found / len(expected_kw), 3)


def _combine_paso_final(paso_criterio: bool, llm_judge_veredicto: bool | None) -> bool:
    """Combina la heurística con el juez LLM: la heurística manda si aprobó;
    si falló, el juez puede rescatar un falso negativo; si el juez no aplica
    (None), se respeta la heurística tal cual."""
    if paso_criterio:
        return True
    if llm_judge_veredicto is None:
        return paso_criterio
    return bool(llm_judge_veredicto)


def run_single_turn(orchestrator: Orchestrator, prompt: str, session_id: str, history: list[dict] | None = None) -> dict:
    start = time.perf_counter()
    response = orchestrator.route(prompt, session_id, history=history)
    latency = round(time.perf_counter() - start, 3)
    return {
        "prompt": prompt,
        "agente_obtenido": response["agent"],
        "context_used": response["context_used"],
        "respuesta": response["result"],
        "latencia_seg": latency,
    }


def eval_factual_or_comparacion(orchestrator: Orchestrator, q: dict) -> dict:
    session_id = f"eval-{q['id']}-{uuid.uuid4().hex[:8]}"
    turn = run_single_turn(orchestrator, q["pregunta"], session_id)
    ratio = keyword_match_ratio(turn["respuesta"], q["respuesta_esperada"])
    routing_correcto = turn["agente_obtenido"] == q["agente_esperado"]
    paso_criterio = routing_correcto and ratio >= 0.5

    juicio = judge_answer(q["pregunta"], q["respuesta_esperada"], turn["respuesta"], modo="contenido")

    return {
        **q,
        **turn,
        "routing_correcto": routing_correcto,
        "keyword_match_ratio": ratio,
        "paso_criterio": paso_criterio,
        "llm_judge_veredicto": juicio["veredicto"],
        "llm_judge_justificacion": juicio["justificacion"],
        "paso_final": _combine_paso_final(paso_criterio, juicio["veredicto"]),
    }


def eval_seguimiento(orchestrator: Orchestrator, q: dict) -> dict:
    session_id = f"eval-{q['id']}-{uuid.uuid4().hex[:8]}"

    turno_1 = run_single_turn(orchestrator, q["pregunta_inicial"], session_id)

    history = [
        {"role": "user", "content": q["pregunta_inicial"]},
        {"role": "assistant", "agent": turno_1["agente_obtenido"], "content": turno_1["respuesta"]},
    ]
    turno_2 = run_single_turn(orchestrator, q["pregunta_seguimiento"], session_id, history=history)

    return {
        **q,
        "turno_1": turno_1,
        "turno_2": turno_2,
        "routing_correcto": turno_1["agente_obtenido"] == q["agente_esperado"] and turno_2["agente_obtenido"] == q["agente_esperado"],
    }


def eval_fuera_de_alcance(orchestrator: Orchestrator, q: dict) -> dict:
    session_id = f"eval-{q['id']}-{uuid.uuid4().hex[:8]}"
    turn = run_single_turn(orchestrator, q["pregunta"], session_id)

    clasificacion_correcta = turn["agente_obtenido"] == OUT_OF_SCOPE
    mensaje_exacto = turn["respuesta"] == OUT_OF_SCOPE_MESSAGE
    paso_criterio = clasificacion_correcta and mensaje_exacto

    return {
        **q,
        **turn,
        "routing_correcto": clasificacion_correcta,
        "mensaje_fijo_exacto": mensaje_exacto,
        "paso_criterio": paso_criterio,
        "llm_judge_veredicto": None,
        "llm_judge_justificacion": None,
        "paso_final": paso_criterio,
    }


def eval_web_search(orchestrator: Orchestrator, q: dict) -> dict:
    session_id = f"eval-{q['id']}-{uuid.uuid4().hex[:8]}"
    turn = run_single_turn(orchestrator, q["pregunta"], session_id)
    routing_correcto = turn["agente_obtenido"] == q["agente_esperado"]
    busco_y_cito_fuente = turn["context_used"] and ("http" in turn["respuesta"] or "Fuentes:" in turn["respuesta"])
    paso_criterio = routing_correcto and busco_y_cito_fuente

    return {
        **q,
        **turn,
        "routing_correcto": routing_correcto,
        "busco_y_cito_fuente": busco_y_cito_fuente,
        "paso_criterio": paso_criterio,
        "llm_judge_veredicto": None,
        "llm_judge_justificacion": None,
        "paso_final": paso_criterio,
    }


def eval_transactional(orchestrator: Orchestrator, q: dict) -> dict:
    session_id = f"eval-{q['id']}-{uuid.uuid4().hex[:8]}"
    turn = run_single_turn(orchestrator, q["pregunta"], session_id)
    ratio = keyword_match_ratio(turn["respuesta"], q.get("criterio_de_exito", ""))
    routing_correcto = turn["agente_obtenido"] == q["agente_esperado"]
    paso_criterio = routing_correcto and ratio >= 0.5

    juicio = judge_answer(q["pregunta"], q.get("criterio_de_exito", ""), turn["respuesta"], modo="rubrica")

    q_sin_pending = {k: v for k, v in q.items() if k != "pending_mcp"}
    return {
        **q_sin_pending,
        **turn,
        "routing_correcto": routing_correcto,
        "keyword_match_ratio": ratio,
        "paso_criterio": paso_criterio,
        "llm_judge_veredicto": juicio["veredicto"],
        "llm_judge_justificacion": juicio["justificacion"],
        "paso_final": _combine_paso_final(paso_criterio, juicio["veredicto"]),
    }


def run_pending_only():
    """Corre SOLO las preguntas que en eval_results.json quedaron con
    'estado': 'pending_mcp', sin volver a correr (ni sobreescribir) las demás."""
    questions = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))
    questions_by_id = {q["id"]: q for q in questions}

    if not RESULTS_PATH.exists():
        print(f"No existe {RESULTS_PATH} todavía. Corré el set completo primero (python -m eval.run_eval_set).")
        return None

    existing_results = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    pending_ids = [r["id"] for r in existing_results if r.get("estado") == "pending_mcp"]

    if not pending_ids:
        print("No hay preguntas con estado 'pending_mcp' en eval_results.json. Nada que correr.")
        return existing_results

    print(f"Preguntas pending_mcp encontradas: {pending_ids}")
    print("Instanciando Orchestrator...")
    orchestrator = Orchestrator()

    new_results_by_id = {}
    for qid in pending_ids:
        q = questions_by_id.get(qid)
        if q is None:
            print(f"  [{qid}] no está en questions.json, se omite")
            continue
        print(f"[{qid}] ({q['categoria']}) ...")
        if q["categoria"] == "transactional":
            new_results_by_id[qid] = eval_transactional(orchestrator, q)
        else:
            print(f"  categoria inesperada para pending_mcp: {q['categoria']}, se omite")

    # Reemplaza únicamente las entradas recién corridas; conserva las demás tal cual.
    merged = [new_results_by_id.get(r["id"], r) for r in existing_results]

    RESULTS_PATH.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nResultados actualizados (solo pending_mcp corridas) -> {RESULTS_PATH}")

    write_summary(merged, questions)
    return merged


def main():
    questions = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))

    pending = [q for q in questions if q.get("pending_mcp")]
    runnable = [q for q in questions if not q.get("pending_mcp")]

    print(f"Total preguntas: {len(questions)} | Pendientes (MCP no disponible): {len(pending)} | A correr: {len(runnable)}")

    print("Instanciando Orchestrator...")
    orchestrator = Orchestrator()

    results = []
    for q in runnable:
        print(f"[{q['id']}] ({q['categoria']}) ...")
        if q["categoria"] in ("factual", "comparacion"):
            results.append(eval_factual_or_comparacion(orchestrator, q))
        elif q["categoria"] == "seguimiento_conversacional":
            results.append(eval_seguimiento(orchestrator, q))
        elif q["categoria"] == "fuera_de_alcance":
            results.append(eval_fuera_de_alcance(orchestrator, q))
        elif q["categoria"] == "web_search":
            results.append(eval_web_search(orchestrator, q))
        elif q["categoria"] == "transactional":
            results.append(eval_transactional(orchestrator, q))
        else:
            print(f"  categoria desconocida: {q['categoria']}, se omite")

    for q in pending:
        results.append({**q, "estado": "pending_mcp", "nota": "No corrida: el agente Transaccional depende del MCP Server en desarrollo."})

    RESULTS_PATH.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nResultados completos -> {RESULTS_PATH}")

    write_summary(results, questions)
    return results


def write_summary(results: list[dict], questions: list[dict]):
    from collections import defaultdict

    by_cat = defaultdict(lambda: {"total": 0, "paso_heuristica": 0, "paso_final": 0, "agentes": defaultdict(int)})

    for r in results:
        cat = r["categoria"]
        by_cat[cat]["total"] += 1

        if r.get("estado") == "pending_mcp":
            by_cat[cat]["agentes"]["pending_mcp"] += 1
            continue

        if cat == "seguimiento_conversacional":
            # No tiene paso_criterio/paso_final propios (no se invoca al juez): el
            # routing es el único criterio, así que ambas tasas coinciden.
            paso_heuristica = r.get("routing_correcto", False)
            paso_final = paso_heuristica
            agente = r["turno_1"]["agente_obtenido"] + " -> " + r["turno_2"]["agente_obtenido"]
        else:
            paso_heuristica = r.get("paso_criterio", False)
            paso_final = r.get("paso_final", paso_heuristica)
            agente = r.get("agente_obtenido")

        if paso_heuristica:
            by_cat[cat]["paso_heuristica"] += 1
        if paso_final:
            by_cat[cat]["paso_final"] += 1
        by_cat[cat]["agentes"][agente] += 1

    with open(SUMMARY_CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "categoria", "total_preguntas",
            "aprobadas_heuristica", "aprobadas_final",
            "tasa_heuristica", "tasa_final",
            "agentes_usados",
        ])
        for cat, data in by_cat.items():
            total = data["total"]
            tasa_heuristica = round(data["paso_heuristica"] / total, 3) if total else 0.0
            tasa_final = round(data["paso_final"] / total, 3) if total else 0.0
            agentes_str = "; ".join(f"{a}={n}" for a, n in data["agentes"].items())
            writer.writerow([
                cat, total,
                data["paso_heuristica"], data["paso_final"],
                tasa_heuristica, tasa_final,
                agentes_str,
            ])

    print(f"Tabla resumen -> {SUMMARY_CSV_PATH}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Corre el set de evaluación del sistema multi-agente.")
    parser.add_argument(
        "--only-pending",
        action="store_true",
        help="Corre únicamente las preguntas con estado 'pending_mcp' en eval_results.json "
             "(ej. transaccionales, una vez que el MCP ya está disponible), sin re-correr "
             "ni sobreescribir el resto de los resultados existentes.",
    )
    args = parser.parse_args()

    if args.only_pending:
        run_pending_only()
    else:
        main()
