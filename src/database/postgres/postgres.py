import psycopg2
import psycopg2.extras
from typing import List, Dict, Any


class PostgresDB:
    connection_string: str
    _conn = None

    def __init__(self, connection_string):
        self.connection_string = connection_string

    def connect(self):
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(self.connection_string)
        return self._conn

    def close(self):
        if self._conn and not self._conn.closed:
            self._conn.close()
            self._conn = None

    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        conn = self.connect()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params)
            if cur.description:
                return cur.fetchall()
            conn.commit()
            return []

    def execute_insert(self, query: str, params: tuple = None) -> int:
        conn = self.connect()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params)
            conn.commit()
            return cur.rowcount