import asyncio
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from .base_agent import BaseAgent
from src.config import settings

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)


def _build_anthropic_tools(mcp_tools: list) -> list[dict]:
    required_overrides = {
        "search_transactions": ["fecha_desde", "fecha_hasta", "justificacion"],
        "create_fraud_case": ["justificacion"],
    }
    description_overrides = {
        "search_transactions": {
            "fecha_desde": ("Requerido. Formato YYYY-MM-DD. "
                            "El MCP Server rechaza búsquedas históricas sin rango de fechas."),
            "fecha_hasta": ("Requerido. Formato YYYY-MM-DD. "
                            "El MCP Server rechaza búsquedas históricas sin rango de fechas."),
            "justificacion": ("Requerido. Mínimo 10 caracteres. "
                              "Explica el motivo de la consulta."),
        },
        "create_fraud_case": {
            "justificacion": ("Requerido. Mínimo 10 caracteres. "
                              "Explica el motivo de la consulta."),
        },
    }

    tools = []
    for tool in mcp_tools:
        name = tool.name
        schema = dict(tool.inputSchema)

        if name in required_overrides:
            merged = list(schema.get("required", []))
            for p in required_overrides[name]:
                if p not in merged:
                    merged.append(p)
            schema["required"] = merged

        if name in description_overrides:
            props = schema.get("properties", {})
            for param_name, desc in description_overrides[name].items():
                if param_name in props:
                    props[param_name] = {**props[param_name], "description": desc}

        tools.append({
            "name": name,
            "description": tool.description or "",
            "input_schema": schema,
        })
    return tools


_MCP_TOOLS_CACHE: list | None = None


def _get_mcp_tools() -> list:
    global _MCP_TOOLS_CACHE
    if _MCP_TOOLS_CACHE is None:
        _MCP_TOOLS_CACHE = asyncio.run(_fetch_mcp_tools())
    return _MCP_TOOLS_CACHE


async def _fetch_mcp_tools() -> list:
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "src.mcp_server.server.server"],
        env={**os.environ, "PYTHONPATH": _PROJECT_ROOT},
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            return result.tools


_ANTHROPIC_TOOLS = _build_anthropic_tools(_get_mcp_tools())

MAX_TOOL_ROUNDS = 5


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
        return asyncio.run(self._run_tool_loop(system_prompt, messages))

    async def _run_tool_loop(self, system_prompt: str, messages: list[dict]) -> str:
        server_params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "src.mcp_server.server.server"],
            env={**os.environ, "PYTHONPATH": _PROJECT_ROOT},
        )
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                for _ in range(MAX_TOOL_ROUNDS):
                    response = self.client.messages.create(
                        model=self.model,
                        max_tokens=2048,
                        system=system_prompt,
                        messages=messages,
                        tools=_ANTHROPIC_TOOLS,
                        temperature=0.3,
                    )

                    tool_blocks = [b for b in response.content if b.type == "tool_use"]
                    if not tool_blocks:
                        text_parts = [b.text for b in response.content if hasattr(b, "text")]
                        return " ".join(text_parts) if text_parts else str(response.content[0])

                    messages.append({"role": "assistant", "content": response.content})
                    tool_results = await self._execute_mcp_tools_with_session(session, tool_blocks)
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
                text_parts = [b.text for b in final.content if hasattr(b, "text")]
                return " ".join(text_parts) if text_parts else str(final.content[0])

    async def _execute_mcp_tools_with_session(self, session, tool_blocks: list) -> list[dict]:
        results = []
        for block in tool_blocks:
            try:
                result = await session.call_tool(block.name, dict(block.input))
                if hasattr(result, 'content') and result.content:
                    parts = [item.text for item in result.content if hasattr(item, 'text')]
                    content = " ".join(parts) if parts else str(result)
                else:
                    content = str(result)
                results.append({"tool_use_id": block.id, "content": content})
            except Exception as e:
                results.append({"tool_use_id": block.id, "content": f"Error: {e}"})
        return results
