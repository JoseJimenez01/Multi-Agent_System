#!/usr/bin/env python3
"""
Script de prueba para verificar la configuración de APIs
Uso: python verify_apis.py
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Agregar raíz al path
sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from src.config import settings
    print("✓ Configuración cargada correctamente")
except Exception as e:
    print(f"✗ Error al cargar configuración: {e}")
    sys.exit(1)


def check_api_keys() -> Tuple[bool, List[str]]:
    """Verifica que las API keys estén configuradas"""
    issues = []
    all_ok = True
    
    print("\n" + "="*60)
    print("🔑 VERIFICACIÓN DE API KEYS")
    print("="*60)
    
    # Anthropic API Key
    if settings.anthropic_api_key:
        print("✓ ANTHROPIC_API_KEY: Configurada")
        if not settings.anthropic_api_key.startswith("sk-ant-"):
            print("  ⚠️  ADVERTENCIA: No parece ser una clave de Anthropic válida")
            issues.append("Anthropic API Key podría ser inválida")
    else:
        print("✗ ANTHROPIC_API_KEY: NO CONFIGURADA")
        issues.append("ANTHROPIC_API_KEY no está en el archivo .env")
        all_ok = False
    
    # OpenAI API Key
    if settings.openai_api_key:
        print("✓ OPENAI_API_KEY: Configurada")
        if not settings.openai_api_key.startswith("sk-"):
            print("  ⚠️  ADVERTENCIA: No parece ser una clave de OpenAI válida")
            issues.append("OpenAI API Key podría ser inválida")
    else:
        print("✗ OPENAI_API_KEY: NO CONFIGURADA")
        issues.append("OPENAI_API_KEY no está en el archivo .env")
        all_ok = False
    
    return all_ok, issues


def check_models() -> None:
    """Verifica que los modelos estén configurados"""
    print("\n" + "="*60)
    print("VERIFICACIÓN DE MODELOS")
    print("="*60)
    
    print(f"Modelo Principal (Orquestador): {settings.claude_model_primary}")
    print(f"  → {settings.claude_model_primary}")
    
    print(f"\nModelo Rápido (Agentes): {settings.claude_model_fast}")
    print(f"  → {settings.claude_model_fast}")
    
    print(f"\nModelo de Embeddings: {settings.embedding_model}")
    print(f"  → {settings.embedding_model} ({settings.embedding_dimension} dimensiones)")


def check_agents() -> None:
    """Verifica que los agentes se carguen correctamente"""
    print("\n" + "="*60)
    print("VERIFICACIÓN DE AGENTES")
    print("="*60)
    
    try:
        from src.agents.base_agent import BaseAgent
        from src.agents import RagAgent, SummarizerAgent, WebResearchAgent, TransactionalAgent
        
        agents: Dict[str, object] = {
            "BaseAgent": BaseAgent(),
            "RagAgent": RagAgent(),
            "SummarizerAgent": SummarizerAgent(),
            "WebResearchAgent": WebResearchAgent(),
            "TransactionalAgent": TransactionalAgent(),
        }
        
        for name, agent in agents.items():
            model = agent.model
            print(f"✓ {name:20s} → {model}")
        
        print("\nTodos los agentes se cargaron correctamente")
        
    except Exception as e:
        print(f"Error al cargar agentes: {e}")
        return False
    
    return True


def check_database_config() -> None:
    """Verifica la configuración de bases de datos"""
    print("\n" + "="*60)
    print("VERIFICACIÓN DE BASES DE DATOS")
    print("="*60)
    
    print(f"PostgreSQL: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'localhost'}")
    print(f"  → {settings.database_url[:50]}...")
    
    print(f"\nQdrant:")
    print(f"  → URL: {settings.qdrant_url}")
    print(f"  → gRPC Port: {settings.qdrant_grpc_port}")


def test_anthropic_connection() -> bool:
    """Intenta conectar con Anthropic"""
    print("\n" + "="*60)
    print("PRUEBA DE CONEXIÓN ANTHROPIC")
    print("="*60)
    
    if not settings.anthropic_api_key:
        print("Saltando: ANTHROPIC_API_KEY no configurada")
        return False
    
    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=settings.anthropic_api_key)
        
        # Hacer una llamada simple
        print("Enviando petición de prueba a Claude...")
        response = client.messages.create(
            model=settings.claude_model_primary,
            max_tokens=100,
            messages=[{"role": "user", "content": "Responde solo con 'OK'"}]
        )
        
        print(f"Conexión exitosa con Anthropic")
        print(f"  Respuesta: {response.content[0].text[:50]}...")
        return True
        
    except Exception as e:
        print(f"Error de conexión: {e}")
        return False


def test_openai_connection() -> bool:
    """Intenta conectar con OpenAI para embeddings"""
    print("\n" + "="*60)
    print("PRUEBA DE CONEXIÓN OPENAI (Embeddings)")
    print("="*60)
    
    if not settings.openai_api_key:
        print("Saltando: OPENAI_API_KEY no configurada")
        return False
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.openai_api_key)
        
        # Crear un embedding simple
        print("Enviando petición de embedding a OpenAI...")
        response = client.embeddings.create(
            model=settings.embedding_model,
            input="prueba"
        )
        
        print(f"Conexión exitosa con OpenAI")
        print(f"  Dimensiones del embedding: {len(response.data[0].embedding)}")
        return True
        
    except Exception as e:
        print(f"Error de conexión: {e}")
        return False


def main() -> None:
    """Función principal"""
    print("""
╔════════════════════════════════════════════════════════════╗
║     VERIFICADOR DE CONFIGURACIÓN DE APIs                  ║
║     Sistema Multi-Agente de Inteligencia Artificial        ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    # Verificaciones
    api_keys_ok, issues = check_api_keys()
    check_models()
    check_database_config()
    agents_ok = check_agents()
    
    # Pruebas de conexión (solo si las APIs están configuradas)
    anthropic_ok = test_anthropic_connection()
    openai_ok = test_openai_connection()
    
    # Resumen final
    print("\n" + "="*60)
    print("RESUMEN")
    print("="*60)
    
    summary = {
        "API Keys": "✓" if api_keys_ok else "✗",
        "Modelos": "✓",
        "Agentes": "✓" if agents_ok else "✗",
        "Conexión Anthropic": "✓" if anthropic_ok else "⏭️" if not settings.anthropic_api_key else "✗",
        "Conexión OpenAI": "✓" if openai_ok else "⏭️" if not settings.openai_api_key else "✗",
    }
    
    for check, result in summary.items():
        print(f"{check:.<40} {result}")
    
    if issues:
        print("\nPROBLEMAS ENCONTRADOS:")
        for issue in issues:
            print(f"  • {issue}")
    
    # Estado final
    if api_keys_ok and agents_ok:
        print("\nConfiguración completada exitosamente")
        print("Puedes proceder a ejecutar la aplicación.")
        return
    else:
        print("\nHay problemas en la configuración")
        print("Por favor, sigue los pasos en CONFIGURACION_APIs.md")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nVerificación cancelada por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\nError inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
