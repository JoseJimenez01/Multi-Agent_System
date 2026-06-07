from .base_agent import BaseAgent

class TransactionalAgent(BaseAgent):

    def __init__(self):
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
            "expected inputs": "",
            "expected outputs": "",
            "restrictions": [
                "No debe crear queries SQL.",
                "No debe consultar bases de datos en internet.",
                "Debe usar las herramientas proporcionadas por el MCP Server interno."
            ],
            "example of a call": "",
            "language": "Mismo idioma que usa el prompt del usuario."
        }