"""Comparación experimental entre las dos estrategias de segmentación RAG (III-C).

Corre el mismo set de preguntas (eval/questions.json) contra dos RagAgent,
uno por cada colección de Qdrant, y guarda los chunks recuperados (texto
completo + score) y la respuesta final de cada uno en
eval/chunking_comparison_results.json, más una tabla resumen de scores en
eval/chunking_comparison_summary.csv.

Este script NO decide cuál estrategia es mejor — solo genera los datos para
que la comparación/interpretación se haga aparte (informe).

Uso:
    python -m eval.compare_chunking
"""

import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.agents.RagAgent import RagAgent

QUESTIONS_PATH = Path(__file__).resolve().parent / "questions.json"
RESULTS_PATH = Path(__file__).resolve().parent / "chunking_comparison_results.json"
SUMMARY_CSV_PATH = Path(__file__).resolve().parent / "chunking_comparison_summary.csv"

COLLECTIONS = {
    "sentences": "course_notes_v1_sentences",
    "fixed_size": "course_notes_v2_fixed",
}


def run_strategy(agent: RagAgent, pregunta: str) -> dict:
    embedding = agent._get_embedding(pregunta)
    scored_points = agent._retrieve_chunks(pregunta, embedding)
    fragments = [agent._fragment_info(p) for p in scored_points]

    respuesta = agent.run(pregunta)

    return {
        "collection": agent.collection_name,
        "chunks_recuperados": fragments,
        "respuesta_agente": respuesta,
        "context_used": agent.context_used,
    }


def main():
    questions = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))

    print("Instanciando RagAgent por estrategia...")
    agents = {strategy: RagAgent(collection_name=collection) for strategy, collection in COLLECTIONS.items()}

    results = []
    summary_rows = []

    for q in questions:
        print(f"[{q['id']}] {q['pregunta']}")
        entry = {
            "id": q["id"],
            "pregunta": q["pregunta"],
            "respuesta_esperada": q["respuesta_esperada"],
            "documento_fuente": q["documento_fuente"],
            "semana": q["semana"],
            "estrategias": {},
        }

        best_scores = {}
        for strategy, agent in agents.items():
            print(f"    -> {strategy} ({agent.collection_name})")
            strategy_result = run_strategy(agent, q["pregunta"])
            entry["estrategias"][strategy] = strategy_result

            scores = [c["score"] for c in strategy_result["chunks_recuperados"] if c.get("score") is not None]
            best_scores[strategy] = max(scores) if scores else None

        results.append(entry)

        s_score = best_scores.get("sentences")
        f_score = best_scores.get("fixed_size")
        if s_score is None and f_score is None:
            mayor = "ninguno_recupero"
        elif s_score is None:
            mayor = "fixed_size"
        elif f_score is None:
            mayor = "sentences"
        elif s_score > f_score:
            mayor = "sentences"
        elif f_score > s_score:
            mayor = "fixed_size"
        else:
            mayor = "empate"

        summary_rows.append({
            "id": q["id"],
            "pregunta": q["pregunta"],
            "semana": q["semana"],
            "best_score_sentences": s_score,
            "best_score_fixed_size": f_score,
            "mayor_score": mayor,
        })

    RESULTS_PATH.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nResultados completos -> {RESULTS_PATH}")

    with open(SUMMARY_CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "id", "pregunta", "semana", "best_score_sentences", "best_score_fixed_size", "mayor_score",
        ])
        writer.writeheader()
        writer.writerows(summary_rows)
    print(f"Tabla resumen -> {SUMMARY_CSV_PATH}")

    return summary_rows


if __name__ == "__main__":
    main()
