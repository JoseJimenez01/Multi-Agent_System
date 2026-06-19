from typing import Any
from mcp_server.server import FastMCP, Context
from src.config import settings
from src.database.postgres.postgres import PostgresDB
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mcp_server")

mcp = FastMCP(
    name="Multi-Agent_System_MCPServer",
    instructions="MCP server for querying the banking database (schema: banco)",
    host="127.0.0.1",
    port=8000,
)

db = PostgresDB(settings.database_url)


@mcp.tool()
def get_transaction_by_id(transaction_id: int) -> list[dict[str, Any]]:
    """Get a single transaction by its ID."""
    return db.execute_query("""
        SELECT t.id, t.fecha, t.hora, t.monto, t.descripcion, t.ip_origen, t.canal,
               ct.numero_cuenta, b.nombre AS banco,
               tt.nombre AS tipo_transaccion,
               et.nombre AS estado,
               m.codigo AS moneda,
               p.nombre AS pais
        FROM banco.transaccion t
        JOIN banco.cuenta ct ON ct.id = t.id_cuenta
        JOIN banco.banco b ON b.id = t.id_banco
        JOIN banco.tipo_transaccion tt ON tt.id = t.id_tipo_transaccion
        JOIN banco.estado_transaccion et ON et.id = t.id_estado_transaccion
        JOIN banco.moneda m ON m.id = t.id_moneda
        JOIN banco.pais p ON p.id = t.id_pais
        WHERE t.id = %s
    """, (transaction_id,))


@mcp.tool()
def get_transactions(limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
    """Get all transactions with pagination."""
    return db.execute_query("""
        SELECT t.id, t.fecha, t.hora, t.monto, t.descripcion, t.ip_origen, t.canal,
               ct.numero_cuenta, b.nombre AS banco,
               tt.nombre AS tipo_transaccion,
               et.nombre AS estado,
               m.codigo AS moneda,
               p.nombre AS pais
        FROM banco.transaccion t
        JOIN banco.cuenta ct ON ct.id = t.id_cuenta
        JOIN banco.banco b ON b.id = t.id_banco
        JOIN banco.tipo_transaccion tt ON tt.id = t.id_tipo_transaccion
        JOIN banco.estado_transaccion et ON et.id = t.id_estado_transaccion
        JOIN banco.moneda m ON m.id = t.id_moneda
        JOIN banco.pais p ON p.id = t.id_pais
        ORDER BY t.fecha DESC, t.hora DESC
        LIMIT %s OFFSET %s
    """, (limit, offset))


@mcp.tool()
def search_transactions(
    ctx: Context = None,
    cliente_id: int = None,
    numero_cuenta: str = None,
    tipo: str = None,
    estado: str = None,
    fecha_desde: str = None,
    fecha_hasta: str = None,
    monto_min: float = None,
    monto_max: float = None,
    pais: str = None,
    canal: str = None,
    limit: int = 50
) -> list[dict[str, Any]]:
    """Search transactions with optional filters. All filter parameters are optional."""
    conditions = []
    params = []

    if cliente_id is not None:
        conditions.append("ct.id_cliente = %s")
        params.append(cliente_id)
    if numero_cuenta is not None:
        conditions.append("ct.numero_cuenta = %s")
        params.append(numero_cuenta)
    if tipo is not None:
        conditions.append("tt.nombre = %s")
        params.append(tipo)
    if estado is not None:
        conditions.append("et.nombre = %s")
        params.append(estado)
    if fecha_desde is not None:
        conditions.append("t.fecha >= %s")
        params.append(fecha_desde)
    if fecha_hasta is not None:
        conditions.append("t.fecha <= %s")
        params.append(fecha_hasta)
    if monto_min is not None:
        conditions.append("t.monto >= %s")
        params.append(monto_min)
    if monto_max is not None:
        conditions.append("t.monto <= %s")
        params.append(monto_max)
    if pais is not None:
        conditions.append("p.nombre = %s")
        params.append(pais)
    if canal is not None:
        conditions.append("t.canal = %s")
        params.append(canal)

    where_clause = " AND ".join(conditions) if conditions else "TRUE"

    query = f"""
        SELECT t.id, t.fecha, t.hora, t.monto, t.descripcion, t.ip_origen, t.canal,
               ct.numero_cuenta, b.nombre AS banco,
               tt.nombre AS tipo_transaccion,
               et.nombre AS estado,
               m.codigo AS moneda,
               p.nombre AS pais
        FROM banco.transaccion t
        JOIN banco.cuenta ct ON ct.id = t.id_cuenta
        JOIN banco.banco b ON b.id = t.id_banco
        JOIN banco.tipo_transaccion tt ON tt.id = t.id_tipo_transaccion
        JOIN banco.estado_transaccion et ON et.id = t.id_estado_transaccion
        JOIN banco.moneda m ON m.id = t.id_moneda
        JOIN banco.pais p ON p.id = t.id_pais
        WHERE {where_clause}
        ORDER BY t.fecha DESC, t.hora DESC
        LIMIT %s
    """
    params.append(limit)

    if ctx:
        ctx.info(f"Searching transactions with {len(conditions)} filter(s)")
    return db.execute_query(query, tuple(params))


@mcp.tool()
def get_customer_risk_summary(customer_id: int) -> list[dict[str, Any]]:
    """Get risk summary for a customer including profile, accounts, and flagged cases."""
    return db.execute_query("""
        SELECT p.id, p.nombre, p.apellido, p.identificacion, p.email, p.telefono,
               nr.nombre AS nivel_riesgo, nr.descripcion AS riesgo_descripcion,
               c.fecha_alta, c.activo,
               COUNT(DISTINCT ct.id) AS total_cuentas,
               COALESCE(SUM(ct.saldo), 0) AS saldo_total,
               COUNT(DISTINCT cr.id) AS casos_abiertos
        FROM banco.cliente c
        JOIN banco.persona p ON p.id = c.id_persona
        JOIN banco.nivel_riesgo nr ON nr.id = c.id_nivel_riesgo
        LEFT JOIN banco.cuenta ct ON ct.id_cliente = c.id
        LEFT JOIN banco.caso_revision cr ON cr.id_transaccion IN (
            SELECT t.id FROM banco.transaccion t WHERE t.id_cuenta IN (
                SELECT ct2.id FROM banco.cuenta ct2 WHERE ct2.id_cliente = c.id
            )
        ) AND cr.estado = 'ABIERTO'
        WHERE c.id = %s
        GROUP BY p.id, p.nombre, p.apellido, p.identificacion, p.email, p.telefono,
                 nr.nombre, nr.descripcion, c.fecha_alta, c.activo
    """, (customer_id,))


@mcp.tool()
def get_customers(limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
    """Get all customers with pagination."""
    return db.execute_query("""
        SELECT c.id AS cliente_id, p.nombre, p.apellido, p.identificacion, p.email,
               p.telefono, nr.nombre AS nivel_riesgo, c.fecha_alta, c.activo
        FROM banco.cliente c
        JOIN banco.persona p ON p.id = c.id_persona
        JOIN banco.nivel_riesgo nr ON nr.id = c.id_nivel_riesgo
        ORDER BY c.id
        LIMIT %s OFFSET %s
    """, (limit, offset))


@mcp.tool()
def get_recent_flagged_transactions(days: int = 7) -> list[dict[str, Any]]:
    """Get transactions that have been flagged in fraud cases within the last N days."""
    return db.execute_query("""
        SELECT t.id AS transaction_id, t.fecha, t.hora, t.monto, t.descripcion, t.canal,
               ct.numero_cuenta, p.nombre AS cliente_nombre, p.apellido AS cliente_apellido,
               cr.id AS caso_id, cr.fecha_apertura, cr.estado AS caso_estado,
               rf.nombre AS regla_disparada
        FROM banco.caso_revision cr
        JOIN banco.transaccion t ON t.id = cr.id_transaccion
        JOIN banco.cuenta ct ON ct.id = t.id_cuenta
        JOIN banco.cliente c ON c.id = ct.id_cliente
        JOIN banco.persona p ON p.id = c.id_persona
        JOIN banco.regla_fraude rf ON rf.id = cr.id_regla_fraude
        WHERE cr.fecha_apertura >= CURRENT_DATE - %s::interval
        ORDER BY cr.fecha_apertura DESC
    """, (f"{days} days",))


@mcp.tool()
def create_fraud_case(
    transaction_id: int,
    reason: str,
    severity: str = "ALTA",
    ctx: Context = None
) -> list[dict[str, Any]]:
    """Create a new fraud case for a transaction. severity: ALTA, MEDIA, or BAJA."""
    if severity.upper() not in ("ALTA", "MEDIA", "BAJA"):
        return [{"error": "severity must be ALTA, MEDIA, or BAJA"}]

    db.execute_query(
        "INSERT INTO banco.regla_fraude (nombre, descripcion) VALUES (%s, %s) ON CONFLICT (nombre) DO NOTHING",
        (f"MANUAL_{transaction_id}", reason)
    )
    db.execute_query(
        "INSERT INTO banco.caso_revision (id_transaccion, id_regla_fraude, resolucion, estado) "
        "VALUES (%s, (SELECT id FROM banco.regla_fraude WHERE nombre = %s), %s, 'ABIERTO')",
        (transaction_id, f"MANUAL_{transaction_id}", f"Severidad: {severity.upper()}. Motivo: {reason}")
    )
    if ctx:
        ctx.info(f"Fraud case created for transaction {transaction_id}")
    return [{"message": f"Fraud case created for transaction {transaction_id}", "severity": severity.upper(), "reason": reason}]


@mcp.tool()
def get_fraud_cases(limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
    """Get all fraud cases with pagination."""
    return db.execute_query("""
        SELECT cr.id, cr.fecha_apertura, cr.fecha_cierre, cr.estado, cr.resolucion,
               cr.analista, t.id AS transaction_id, t.monto, t.fecha AS fecha_transaccion,
               rf.nombre AS regla_disparada, rf.descripcion AS regla_descripcion
        FROM banco.caso_revision cr
        JOIN banco.regla_fraude rf ON rf.id = cr.id_regla_fraude
        JOIN banco.transaccion t ON t.id = cr.id_transaccion
        ORDER BY cr.fecha_apertura DESC
        LIMIT %s OFFSET %s
    """, (limit, offset))
