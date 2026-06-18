from .base_agent import BaseAgent
from src.config import settings

class TransactionalAgent(BaseAgent):

    def __init__(self):
        super().__init__()
        # Claude Haiku para tareas transaccionales
        self.model = settings.claude_model_fast

        self.definition = {
            "agent_name": "Transactional_Agent",
            "description": "Agente especializado en recuperar informacion consultar la base de datos ficticia mediante el MCP Server.",
            "role": "researcher",
            "skills": [
                # wich tool
                "tool_selection",
                # Parameter extraction
                "parameter_extraction",
                # Tool calling
                "tool_invocation",
                # Result interpretation
                "response_interpretation",
                # Reasoning
                "contextual_reasoning",
                # Error handling
                "tool_error_handling",
                # Formatting
                "response_formatting"
            ],
            "allowed_tools": [
                "mcp_transaction_tool"
            ],
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
                "Debe usar las herramientas proporcionadas por el MCP Server interno."
            ],
            "example of a call": (
                'Entrada: "¿Hay transacciones sospechosas en los últimos 7 días?"\n'
                'Salida: "Se encontraron 2 transacciones marcadas como sospechosas entre el '
                '10 y el 17 de junio de 2026 (consulta: get_recent_flagged_transactions(days=7)): '
                'una por monto inusualmente alto en la cuenta terminada en 4821 y otra por '
                'actividad de madrugada en la cuenta terminada en 9034."'
            ),
            "language": "Mismo idioma que usa el prompt del usuario."
        }