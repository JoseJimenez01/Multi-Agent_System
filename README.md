# Multi-Agent_System
RAG, A2A, MCP, and Memory are implemented.

### Dependencies

Create a virtual environment using:

python -m venv .venv

Activate the environment (the CLI geta a visual change):

Windows:
.venv\Scripts\activate

Linux/MAC:
source .venv/bin/activate

Then install requirements with:

pip install -r requirements.txt

Then, when we wanted to work again with the project:

activate .venv

and continue working, the project are going to use the libraries in it.

Activate containers:

# Levantar contenedores
docker compose -f docker/docker-compose.yml up -d

# Parar sin borrar volúmenes
docker compose -f docker/docker-compose.yml down

# Solo detener
docker compose -f docker/docker-compose.yml stop

# Ver logs
docker compose -f docker/docker-compose.yml logs -f

To run the app:

streamlit run src/app.py --server.openBrowser true
streamlit run src/app.py


To export the data
python -c "from src.preprocess.ingest import export_documents_json; export_documents_json('output.json')"


Create Transactions database manually:
```python -m src.database.postgres.setup_db```

If dont want of this way, Docker create and load it when activate the container.