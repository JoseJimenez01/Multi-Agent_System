import inspect
from typing import Any, get_type_hints

from .base_agent import BaseAgent
from src.config import settings
from src.mcp.server.server import (
    get_transaction_by_id,
    get_transactions,
    search_transactions,
    get_customer_risk_summary,
    get_customers,
    get_recent_flagged_transactions,
    create_fraud_case,
    get_fraud_cases,
)

_TYPE_MAP = {
    int: "integer",
    str: "string",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
    type(None): "null",
}

_TOOL_FUNCTIONS = {
    "get_transaction_by_id": get_transaction_by_id,
    "get_transactions": get_transactions,
    "search_transactions": search_transactions,
    "get_customer_risk_summary": get_customer_risk_summary,
    "get_customers": get_customers,
    "get_recent_flagged_transactions": get_recent_flagged_transactions,
    "create_fraud_case": create_fraud_case,
    "get_fraud_cases": get_fraud_cases,
}


def _build_anthropic_tools() -> list[dict]:
    tools = []
    for name, fn in _TOOL_FUNCTIONS.items():
        sig = inspect.signature(fn)
        hints = get_type_hints(fn)
        properties = {}
        required = []
        doc = (fn.__doc__ or "").strip()

        for param_name, param in sig.parameters.items():
            if param_name == "ctx":
                continue
            param_type = hints.get(param_name, str)
            json_type = _TYPE_MAP.get(param_type, "string")

            prop = {"type": json_type}
            if param.default is inspect.Parameter.empty:
                required.append(param_name)

            properties[param_name] = prop

        tools.append({
            "name": name,
            "description": doc,
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        })
    return tools


_ANTHROPIC_TOOLS = _build_anthropic_tools()


class TransactionalAgent(BaseAgent):

    def __init__(self):
        super().__init__()
        self.model = settings.claude_model_fast
        self.definition = {
            "agent_name": "Transactional_Agent",
            "description": (
                "Agente especializado en consultar la base de datos bancaria "
                "(transacciones, clientes, fraudes) usando las herramientas del MCP Server."
            ),
            "role": "researcher",
            "skills": [
                "tool_selection", "parameter_extraction",
                "tool_invocation", "response_interpretation",
                "contextual_reasoning", "tool_error_handling",
                "response_formatting",
            ],
            "allowed_tools": [t["name"] for t in _ANTHROPIC_TOOLS],
            "expected inputs": (
                "Una pregunta del usuario sobre clientes, cuentas, transacciones o casos de "
                "fraude ficticios (por ejemplo, montos, fechas, estados o nivel de riesgo)."
            ),
            "expected outputs": (
                "Una respuesta en lenguaje natural basada únicamente en los datos devueltos por "
                "las herramientas del MCP Server, indicando qué consulta se realizó y, cuando "
                "corresponda, los últimos cuatro dígitos de la cuenta (nunca el número completo)."
            ),
            "restrictions": [
                "No debe crear queries SQL.",
                "No debe consultar bases de datos en internet.",
                "No debe usar busqueda web.",
                "No debe hacer consultas a la base de datos vetorial.",
                "No debe consultar APIS externas.",
                "Debe usar las herramientas proporcionadas por el MCP Server interno.",
                "Toda llamada al MCP debe incluir una justificación.",
                "No se deben mostrar números de cuenta completos. Solo se permiten los últimos cuatro dígitos.",
                "No se deben permitir consultas masivas sin filtros.",
                "No se deben modificar transacciones existentes.",
                "Las consultas con información sensible deben ser anonimizadas o rechazadas.",
                "Las búsquedas históricas deben limitarse por rango de fechas.",
                "El agente debe explicar qué datos utilizó para llegar a una conclusión.",
            ],
            "example of a call": (
                'Entrada: "¿Hay transacciones sospechosas en los últimos 7 días?"\n'
                'Salida: "Se encontraron 2 transacciones marcadas como sospechosas entre el '
                '10 y el 17 de junio de 2026 (consulta: get_recent_flagged_transactions(days=7)): '
                'una por monto inusualmente alto en la cuenta terminada en 4821 y otra por '
                'actividad de madrugada en la cuenta terminada en 9034."'
            ),
            "language": "Mismo idioma que usa el prompt del usuario.",
        }

    def run(self, prompt: str, context: str | None = None, history: list[dict] | None = None) -> str:
        system_prompt = self._build_system_prompt(context)
        messages = self._build_messages(history, prompt)

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=system_prompt,
            messages=messages,
            tools=_ANTHROPIC_TOOLS,
            temperature=0.3,
        )

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                fn = _TOOL_FUNCTIONS.get(block.name)
                if fn is None:
                    tool_results.append({"tool_use_id": block.id, "content": f"Unknown tool: {block.name}"})
                    continue
                try:
                    result = fn(**dict(block.input))
                    tool_results.append({"tool_use_id": block.id, "content": str(result)})
                except Exception as e:
                    tool_results.append({"tool_use_id": block.id, "content": f"Error: {e}"})

        if not tool_results:
            return response.content[0].text

        messages.append({"role": "assistant", "content": response.content})
        messages.append({
            "role": "user",
            "content": [{"type": "tool_result", **tr} for tr in tool_results],
        })

        final = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=system_prompt,
            messages=messages,
            temperature=0.3,
        )
        return final.content[0].text
