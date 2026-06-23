# Multi-Agent System — Apuntes del curso de Inteligencia Artificial

Sistema multi-agente para responder preguntas sobre los apuntes del curso de
Inteligencia Artificial (RAG), complementado con búsqueda web, memoria
conversacional/histórica y consultas sobre una base de datos bancaria
ficticia. Proyecto académico (Tarea 04/05, Escuela de Ingeniería en
Computación, TEC).

## 1. Descripción general

El sistema recibe una pregunta del usuario a través de una interfaz web
(Streamlit) y la enruta, mediante un Orquestador que clasifica la consultaP
con un LLM, hacia uno de cuatro agentes especializados: un agente RAG que
responde con base en los apuntes del curso, un agente de búsqueda web para
preguntas que requieren información externa/actual, un agente Resumidor que
resume la sesión y consulta memoria histórica, y un agente Transaccional que
consulta una base de datos bancaria ficticia a través de un conjunto de
herramientas controladas inspiradas en el protocolo MCP. Las preguntas que no
corresponden a ninguna de estas capacidades se rechazan con un mensaje fijo,
sin invocar ningún modelo adicional.

El RAG se apoya en una base vectorial (Qdrant) poblada a partir de los PDFs
de los apuntes, con dos estrategias de segmentación implementadas y
comparadas experimentalmente. La memoria conversacional tiene dos niveles:
temporal (los últimos turnos de la sesión, pasados directamente a cada
llamada al LLM) e histórica persistente (sesiones y mensajes guardados en
Postgres, consultables entre sesiones). Toda la ejecución se traza en
Langfuse (entrada del usuario, agente usado, fragmentos recuperados,
llamadas al modelo, latencia, costo y errores).

Tecnologías principales: Python 3.13, Anthropic Claude (LLM), OpenAI
(embeddings), Qdrant (base vectorial), PostgreSQL (datos transaccionales y
memoria histórica), Langfuse self-hosted (observabilidad), Streamlit
(interfaz web), Docker Compose (infraestructura).

## 2. Arquitectura: agentes implementados

| Agente | Descripción |
| --- | --- |
| **Orquestador** | Clasifica la pregunta del usuario en una de 5 categorías (`rag`, `web`, `transactional`, `summarizer`, `fuera_de_alcance`) con Claude, usando los últimos turnos de la sesión solo para resolver referencias ambiguas (no para decidir el tema). Para `fuera_de_alcance` responde con un mensaje fijo sin invocar ningún otro LLM. |
| **RAG Agent** | Recupera fragmentos relevantes de los apuntes del curso desde Qdrant (con filtro opcional por semana) y genera una respuesta citando documento, semana y autor; indica explícitamente cuando no encuentra información en el contexto recuperado. |
| **Web Search Agent** | Responde preguntas que requieren información externa o actual usando la herramienta nativa de búsqueda web de Claude (forzada en el primer turno), citando las fuentes consultadas. |
| **Resumidor (Summarizer) Agent** | Resume la sesión actual o consulta memoria histórica persistente a través de 4 operaciones (`search_history`, `summarize_current_session`, `compare_with_previous`, `search_by_agent_and_date`); si no hay historial suficiente, lo dice en vez de inventar un resumen. |
| **Transaccional Agent** | Consulta una base de datos bancaria ficticia (clientes, cuentas, transacciones, casos de fraude) a través de 8 herramientas controladas (no ejecuta SQL libre), con reglas de seguridad aplicadas en código: números de cuenta enmascarados, límite duro de filas, rango de fechas y justificación obligatorios en consultas históricas. |

## 3. Requisitos previos

- **Docker Desktop** (o Docker Engine + Compose) — levanta Qdrant, Postgres y el stack completo de Langfuse self-hosted (7 contenedores). Recomendado al menos 8 GB de RAM libres.
- **Python 3.13** (versión usada en desarrollo; no se probó con versiones anteriores).
- **API key de Anthropic** (LLM principal de todos los agentes).
- **API key de OpenAI** (solo se usa para generar embeddings de los apuntes; no se usa como LLM).

## 4. Instalación y ejecución

### 4.1. Clonar el repositorio

```bash
git clone <url-del-repo>
cd Multi-Agent_System
```

### 4.2. Configurar variables de entorno

Copiar la plantilla y completar las API keys:

```bash
cp .env.example .env
```

Editar `.env` y completar como mínimo `ANTHROPIC_API_KEY` y `OPENAI_API_KEY`.
`LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY` se completan después del paso
4.3 (se generan desde la UI de Langfuse, no existen de antemano). Si se
dejan vacías, el sistema sigue funcionando sin trazas (`is_tracing_enabled()`
lo detecta y se salta el tracing).

También existe `docker/.env.example` — copiarlo a `docker/.env`. Son
secretos de infraestructura del stack de Langfuse (cifrado, claves de la DB
interna). **No cambiar `LANGFUSE_SECRET`/`LANGFUSE_SALT`/`LANGFUSE_ENCRYPTION_KEY`
después del primer arranque** o se pierde el acceso a las credenciales ya
registradas.

```bash
cp docker/.env.example docker/.env
```

### 4.3. Levantar la infraestructura Docker

```bash
docker compose -f docker/docker-compose.yml up -d
```

Esto levanta:

- **Qdrant** — base vectorial para los apuntes del curso.
- **Postgres (`mas-postgres`)** — una sola instancia con dos schemas separados: `banco` (datos transaccionales ficticios, poblados automáticamente la primera vez desde `src/database/postgres/banco_schema.sql`/`banco_seed.sql`) y `memory` (sesiones/mensajes históricos, se crea sola al instanciar el Orquestador).
- **Stack de Langfuse self-hosted** — Postgres propio, ClickHouse, Redis, MinIO, Zookeeper, el servicio web y el worker. Ver `documentacion/LANGFUSE.md` para el detalle de cada uno y cómo crear la cuenta/proyecto inicial.

Si el volumen de `mas-postgres` ya existía sin los datos de `banco` (por
ejemplo, tras un `docker compose down` sin borrar volúmenes seguido de un
cambio en el schema), repoblar manualmente:

```bash
python -m src.database.postgres.setup_db
```

### 4.4. Instalar dependencias de Python

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux/Mac

pip install -r requirements.txt
```

### 4.5. Ingestar los apuntes del curso a Qdrant

El `RagAgent` usado en producción (`router.py`, sin argumentos) apunta por
defecto a la colección `course_notes`. Es la que hace falta poblar para que
la app funcione:

```bash
python -m src.preprocess.ingest --strategy sentences --collection course_notes
```

Opcionalmente, para reproducir la comparación experimental entre las dos
estrategias de segmentación (ver sección 6), poblar también las colecciones
dedicadas a ese experimento:

```bash
python -m src.preprocess.ingest --strategy all
```

(esto crea `course_notes_v1_sentences` y `course_notes_v2_fixed`, separadas
de `course_notes`).

### 4.6. Levantar la aplicación

```bash
streamlit run src/app.py
```

La app queda disponible en `http://localhost:8501`.

## 5. Decisiones de diseño notables

- **El "MCP Server" es un módulo Python in-process, no un servidor separado.**
  `src/mcp/server/server.py` define 8 herramientas con el decorador
  `@mcp.tool()` de `FastMCP`, pero el archivo nunca llama a `mcp.run()`: no
  hay ningún proceso MCP escuchando por stdio/HTTP. `TransactionalAgent`
  importa y ejecuta esas funciones directamente como funciones Python.
  Decisión pragmática para el alcance de este proyecto — evita la
  complejidad de correr un proceso cliente/servidor MCP separado, sin perder
  el patrón de herramientas controladas (sin SQL libre) que pide la
  especificación. El comportamiento observable desde los agentes es el
  mismo; la diferencia es de transporte/proceso, no de funcionalidad.

- **Bug de overlap en la segmentación por oraciones, encontrado y corregido
  durante el desarrollo.** La función `segment_text()` (estrategia
  `sentences`) calculaba el overlap entre chunks tomando las últimas N
  *oraciones* de una lista, cuando el parámetro `CHUNK_OVERLAP=50` está
  pensado en *palabras*. Como casi ningún chunk de 500 palabras acumula 50
  oraciones, el código terminaba usando el chunk completo como overlap del
  siguiente, duplicando contenido masivamente. Se confirmó en 50 de 51
  documentos del corpus antes de corregirlo. El fix y la re-ingesta de la
  colección de producción ya están aplicados.

- **Las reglas de seguridad del MCP tienen enforcement real en código,
  no solo en el prompt.** `server.py` enmascara números de cuenta con SQL
  (`RIGHT(numero_cuenta::text, 4)`), aplica un límite duro de 50 filas
  independiente de lo que pida el agente, y rechaza con un error explícito
  las búsquedas históricas sin rango de fechas o sin una justificación de al
  menos 10 caracteres — todo evaluado en el handler de la herramienta, no
  delegado a que el LLM "decida" respetar una instrucción de texto.

- **El clasificador del Orquestador ve los últimos turnos de la sesión,
  pero no decide la categoría en base a ellos.** Inicialmente
  `_classify_task()` solo recibía la pregunta actual, lo que rompía
  preguntas de seguimiento con referencias implícitas ("¿y cuál es la
  derivada de esa función?"). Se corrigió pasándole los últimos 2 pares de
  turnos, con una instrucción explícita de usarlos solo para resolver
  pronombres/referencias, no para decidir el tema — evita que toda la
  conversación posterior a una pregunta de RAG quede "pegada" a esa
  categoría.

- **Limitación conocida:** `TransactionalAgent.run()` solo soporta una ronda
  de tool-calling. Tareas que requieren llamadas encadenadas (por ejemplo,
  buscar la transacción de mayor monto y *después* crear un caso de fraude
  sobre esa transacción específica) pueden quedar incompletas: el agente
  describe en texto el siguiente paso pero no tiene herramientas
  disponibles en el segundo turno para ejecutarlo. Documentado, no
  corregido todavía.

## 6. Evaluación experimental

`eval/questions.json` contiene 35 preguntas en 6 categorías: 10 factuales,
5 de comparación, 5 de seguimiento conversacional (pares pregunta
inicial/seguimiento), 5 fuera de alcance, 5 de búsqueda web y 5
transaccionales.

Correr el set completo contra el Orquestador real:

```bash
python -m eval.run_eval_set
```

Correr únicamente las preguntas que hayan quedado pendientes en una corrida
anterior (sin re-correr ni sobreescribir el resto):

```bash
python -m eval.run_eval_set --only-pending
```

Resultados en `eval/eval_results.json` (detalle por pregunta: agente usado,
latencia, si usó contexto fundamentado, coincidencia con el criterio de
éxito) y `eval/eval_summary.csv` (resumen por categoría). El chequeo de
contenido para preguntas factuales/comparación es un proxy heurístico de
coincidencia de palabras clave, no una verificación semántica — pensado
para priorizar revisión manual.

`eval/compare_chunking.py` corre las 10 preguntas factuales contra las dos
colecciones de chunking (`course_notes_v1_sentences` vs
`course_notes_v2_fixed`) y guarda los chunks recuperados, scores y
respuestas de cada una en `eval/chunking_comparison_results.json`, sin
concluir cuál estrategia es mejor.

## 7. Estructura del proyecto

```text
.
├── docker/
│   ├── docker-compose.yml        # Qdrant, Postgres (banco + memory), stack de Langfuse
│   ├── .env.example               # secretos de infraestructura (Langfuse, Qdrant)
│   ├── postgres/                  # (vacío; schema/seed reales viven en src/database/postgres/)
│   └── clickhouse/                # configuración de ClickHouse para Langfuse
├── eval/
│   ├── questions.json             # 35 preguntas de evaluación, 6 categorías
│   ├── run_eval_set.py            # corre el set contra el Orquestador real
│   ├── compare_chunking.py        # comparación experimental de las 2 estrategias de chunking
│   ├── eval_results.json          # resultados detallados de la última corrida
│   ├── eval_summary.csv           # resumen por categoría
│   └── chunking_comparison_*.json/.csv  # resultados de la comparación de chunking
├── src/
│   ├── agents/
│   │   ├── base_agent.py          # clase base: system prompt, tracing, historial multi-turno
│   │   ├── RagAgent.py
│   │   ├── WebResearchAgent.py
│   │   ├── SummarizerAgent.py
│   │   └── TransactionalAgent.py
│   ├── orchestrator/
│   │   └── router.py              # clasificador y enrutamiento del Orquestador
│   ├── mcp/server/
│   │   └── server.py              # 8 herramientas sobre la base de datos bancaria ficticia
│   ├── memory/
│   │   ├── db.py                  # persistencia de sesiones/mensajes en Postgres
│   │   └── tool.py                # memory_tool: 4 operaciones de memoria histórica
│   ├── database/
│   │   ├── vector_store.py        # cliente Qdrant
│   │   └── postgres/              # schema/seed de banco y memoria, cliente Postgres
│   ├── preprocess/
│   │   ├── processor.py           # extracción, limpieza y 2 estrategias de segmentación
│   │   └── ingest.py              # pipeline de embeddings y carga a Qdrant
│   ├── observability/
│   │   └── langfuse_tracing.py    # helpers de tracing condicional (no rompe sin Langfuse)
│   ├── config/settings.py         # configuración centralizada (lee .env)
│   ├── models/                    # (vacío, sin uso actual)
│   ├── notes/                     # PDFs de los apuntes del curso (corpus del RAG)
│   └── app.py                     # interfaz web (Streamlit)
├── tests/
│   └── verify_apis.py             # script de verificación de configuración/API keys
├── documentacion/
│   ├── LANGFUSE.md                # guía detallada de configuración de Langfuse
│   └── CONFIGURACION_APIS.md      # detalle de API keys y asignación de modelos
├── backups/                       # backups puntuales de colecciones Qdrant
├── .env.example                   # plantilla de variables de entorno de la aplicación
├── requirements.txt
└── README.md
```
