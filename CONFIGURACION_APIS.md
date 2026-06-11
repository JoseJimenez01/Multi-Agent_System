# Configuración de APIS

**Última actualización:** Junio 2026

---

## Arquitectura

El sistema utiliza dos proveedores de IA con roles diferenciados:

| Proveedor | Uso | Modelo |
|-----------|-----|--------|
| **Anthropic** | LLM principal (orquestador y agentes) | Claude Sonnet 4.6 / Haiku 4.5 |
| **OpenAI** | Embeddings para búsqueda semántica | text-embedding-3-small |

### Asignación de modelos por componente

| Componente | Modelo | Justificación |
|-----------|--------|---------------|
| Orquestador (`router.py`) | Claude Sonnet 4.6 | Clasificación de tareas y decisiones complejas |
| RAG Agent | Claude Haiku 4.5 | Búsqueda en documentos, bajo costo |
| Summarizer Agent | Claude Haiku 4.5 | Resúmenes rápidos, bajo costo |
| Web Research Agent | Claude Haiku 4.5 | Búsquedas web, bajo costo |
| Transactional Agent | Claude Haiku 4.5 | Consultas de base de datos, bajo costo |
| Embeddings | text-embedding-3-small | Vectorización para búsqueda semántica |

---

## Instalación

### 1. Obtener API Keys

**Anthropic** — https://console.anthropic.com  
Crear una clave en la sección *API Keys*. Formato: `sk-ant-...`

**OpenAI** — https://platform.openai.com/account/api-keys  
Crear una nueva clave secreta. Formato: `sk-...`

### 2. Configurar variables de entorno

Crear el archivo `.env` en la raíz del proyecto:

```bash
# Anthropic Claude (LLM principal) — REQUERIDO
ANTHROPIC_API_KEY=sk-ant-...

# OpenAI (solo embeddings) — REQUERIDO
OPENAI_API_KEY=sk-...

# PostgreSQL
DATABASE_URL=postgresql://mas_user:mas_pass@localhost:5432/mas_db

# Qdrant (base vectorial)
QDRANT_URL=http://localhost:6333
QDRANT_GRPC_PORT=6334

# Langfuse (observabilidad) — OPCIONAL
# Ver guía completa: LANGFUSE.md
LANGFUSE_HOST=http://localhost:3000
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Verificar configuración

```bash
python test_apis.py
```

---

## Archivos modificados

```
src/
├── config/settings.py           # Claves y modelos de Anthropic
├── agents/
│   ├── base_agent.py            # Cliente cambiado: OpenAI → Anthropic
│   ├── RagAgent.py              # Modelo: Claude Haiku 4.5
│   ├── SummarizerAgent.py       # Modelo: Claude Haiku 4.5
│   ├── TransactionalAgent.py    # Modelo: Claude Haiku 4.5
│   └── WebResearchAgent.py      # Modelo: Claude Haiku 4.5
└── orchestrator/router.py       # Sin cambios (embeddings con OpenAI)

requirements.txt                 # Agregado: anthropic>=0.25.0
```

---

## Estimación de costos

Precios aproximados (Junio 2026) asumiendo 1 000 consultas/día:

| Modelo | Input | Output | Uso estimado |
|--------|-------|--------|--------------|
| Claude Haiku 4.5 | $0.25 / 1M tokens | $1.25 / 1M tokens | ~$0.50–1.00/mes |
| Claude Sonnet 4.6 | — | — | ~$0.50–1.00/mes |
| text-embedding-3-small | $0.02 / 1M tokens | — | ~$0.50/mes |
| **Total estimado** | | | **~$1.50–2.50/mes** |

---

## Solución de problemas

**`ModuleNotFoundError: No module named 'anthropic'`**  
Ejecutar `pip install -r requirements.txt`.

**`Invalid API Key`**  
Verificar que la clave en `.env` no tenga espacios y sea válida (`sk-ant-...`).

**Error de conexión a Qdrant o PostgreSQL**  
Asegurarse de que Docker esté activo: `docker-compose up -d`.

**Respuestas lentas**  
Verificar que los agentes específicos usen `claude_model_fast` (Haiku) y no el modelo del orquestador.

---

## Referencias

- [Configuración Langfuse (guía completa)](./LANGFUSE.md)
- [Documentación Anthropic](https://docs.anthropic.com)
- [Precios Anthropic](https://www.anthropic.com/pricing)
- [Documentación OpenAI](https://platform.openai.com/docs/api-reference)
- [Precios OpenAI](https://openai.com/pricing)
