"""Script para inicializar/resetear la BD PostgreSQL en Docker.

Uso:
    python -m src.database.postgres.setup_db

Requiere el contenedor `mas-postgres` corriendo (puerto 5434 por defecto).
Lee DATABASE_URL desde .env o usa el default.
Ejecuta en orden:
  1. banco_schema.sql  (crea esquema, tablas, catálogos)
  2. banco_seed.sql    (inserta datos de prueba)
"""

import sys
from pathlib import Path

try:
    import psycopg2
except ImportError:
    print("ERROR: psycopg2 no instalado. Ejecuta: pip install psycopg2-binary")
    sys.exit(1)

_BASE = Path(__file__).resolve().parent
_SCHEMA = _BASE / "banco_schema.sql"
_SEED = _BASE / "banco_seed.sql"


def _read_sql(path: Path) -> str:
    if not path.exists():
        print(f"ERROR: No se encuentra {path}")
        sys.exit(1)
    return path.read_text(encoding="utf-8")


def main():
    try:
        from src.config import settings
        dsn = settings.database_url
    except ImportError:
        import os
        dsn = os.getenv("DATABASE_URL", "postgresql://postgres@localhost:5434/mas_db")

    print(f"Conectando a: {dsn}")
    conn = psycopg2.connect(dsn)
    conn.autocommit = True
    cur = conn.cursor()

    print("Ejecutando banco_schema.sql...")
    cur.execute(_read_sql(_SCHEMA))
    print("  OK")

    print("Ejecutando banco_seed.sql...")
    cur.execute(_read_sql(_SEED))
    print("  OK")

    cur.close()
    conn.close()
    print("Base de datos inicializada correctamente.")


if __name__ == "__main__":
    main()
