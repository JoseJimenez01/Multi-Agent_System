-- =============================================================
-- ESQUEMA DE BASE DE DATOS BANCARIA
-- Versión: 1.0
-- Descripción: BD para gestión de clientes, cuentas, transacciones
--              y detección de fraudes en un entorno bancario.
-- =============================================================

-- Limpiar esquema previo si existe
DROP SCHEMA IF EXISTS banco CASCADE;
CREATE SCHEMA banco;
SET search_path TO banco;


-- =============================================================
-- TABLAS DE CATÁLOGO / REFERENCIA
-- =============================================================

-- País de origen o de operación
CREATE TABLE pais (
    id          SERIAL          PRIMARY KEY,
    nombre      VARCHAR(64)     NOT NULL UNIQUE,
    codigo_iso  CHAR(2)         NOT NULL UNIQUE  -- ISO 3166-1 alpha-2
);

COMMENT ON TABLE  pais             IS 'Catálogo de países según ISO 3166-1.';
COMMENT ON COLUMN pais.codigo_iso  IS 'Código de dos letras del país (ej: CR, US, MX).';


-- Nacionalidad (separada de país para 3FN)
CREATE TABLE nacionalidad (
    id          SERIAL          PRIMARY KEY,
    id_pais     INT             NOT NULL REFERENCES pais(id),
    gentilicio  VARCHAR(64)     NOT NULL UNIQUE   -- ej: "Costarricense"
);

COMMENT ON TABLE nacionalidad IS 'Gentilicio asociado a un país (3FN: evita redundancia en persona).';


-- Nivel de riesgo del cliente (bajo, medio, alto)
CREATE TABLE nivel_riesgo (
    id          SERIAL          PRIMARY KEY,
    nombre      VARCHAR(32)     NOT NULL UNIQUE,  -- ej: BAJO, MEDIO, ALTO
    descripcion VARCHAR(128)    NOT NULL
);

COMMENT ON TABLE nivel_riesgo IS 'Clasificación de riesgo asignada a clientes para control de fraude.';


-- Tipo de cuenta (ahorro, corriente, etc.)
CREATE TABLE tipo_cuenta (
    id          SERIAL          PRIMARY KEY,
    nombre      VARCHAR(64)     NOT NULL UNIQUE,
    descripcion VARCHAR(128)    NOT NULL
);

COMMENT ON TABLE tipo_cuenta IS 'Catálogo de modalidades de cuenta bancaria.';


-- Tipo de transacción (depósito, retiro, transferencia, pago, etc.)
CREATE TABLE tipo_transaccion (
    id          SERIAL          PRIMARY KEY,
    nombre      VARCHAR(64)     NOT NULL UNIQUE,
    descripcion VARCHAR(128)    NOT NULL
);

COMMENT ON TABLE tipo_transaccion IS 'Catálogo de categorías de movimiento financiero.';


-- Moneda (USD, CRC, EUR, etc.)
CREATE TABLE moneda (
    id          SERIAL          PRIMARY KEY,
    codigo      CHAR(3)         NOT NULL UNIQUE,  -- ISO 4217
    nombre      VARCHAR(64)     NOT NULL UNIQUE
);

COMMENT ON TABLE  moneda        IS 'Catálogo de monedas según ISO 4217.';
COMMENT ON COLUMN moneda.codigo IS 'Código de tres letras (ej: USD, CRC, EUR).';


-- Estado de una transacción (APROBADA, RECHAZADA, PENDIENTE, REVERTIDA)
CREATE TABLE estado_transaccion (
    id          SERIAL          PRIMARY KEY,
    nombre      VARCHAR(32)     NOT NULL UNIQUE,
    descripcion VARCHAR(128)    NOT NULL
);

COMMENT ON TABLE estado_transaccion IS 'Estados posibles del ciclo de vida de una transacción.';


-- Reglas de detección de fraude / uso de herramientas
CREATE TABLE regla_fraude (
    id          SERIAL          PRIMARY KEY,
    nombre      VARCHAR(128)    NOT NULL UNIQUE,
    descripcion VARCHAR(512)    NOT NULL,
    activa      BOOLEAN         NOT NULL DEFAULT TRUE
);

COMMENT ON TABLE  regla_fraude        IS 'Reglas configurables para identificar comportamiento sospechoso.';
COMMENT ON COLUMN regla_fraude.activa IS 'Permite desactivar una regla sin eliminarla.';


-- =============================================================
-- ENTIDADES PRINCIPALES
-- =============================================================

-- Persona natural (información base, reutilizable)
CREATE TABLE persona (
    id              SERIAL          PRIMARY KEY,
    id_nacionalidad INT             NOT NULL REFERENCES nacionalidad(id),
    nombre          VARCHAR(128)    NOT NULL,
    apellido        VARCHAR(128)    NOT NULL,
    identificacion  VARCHAR(32)     NOT NULL UNIQUE,  -- cédula / pasaporte
    fecha_nac       DATE            NOT NULL,
    email           VARCHAR(128)    NOT NULL UNIQUE,
    telefono        VARCHAR(16)     NOT NULL
);

COMMENT ON TABLE  persona               IS 'Datos personales de individuos; base para clientes.';
COMMENT ON COLUMN persona.identificacion IS 'Número de documento único (cédula, pasaporte, etc.).';


-- Cliente bancario (extiende persona con datos de relación bancaria)
CREATE TABLE cliente (
    id              SERIAL          PRIMARY KEY,
    id_persona      INT             NOT NULL UNIQUE REFERENCES persona(id),
    id_nivel_riesgo INT             NOT NULL REFERENCES nivel_riesgo(id),
    fecha_alta      DATE            NOT NULL DEFAULT CURRENT_DATE,
    activo          BOOLEAN         NOT NULL DEFAULT TRUE
);

COMMENT ON TABLE  cliente            IS 'Cliente registrado en el sistema bancario.';
COMMENT ON COLUMN cliente.id_persona IS 'Relación 1-1 con persona natural.';


-- Banco (institución financiera)
CREATE TABLE banco (
    id      SERIAL          PRIMARY KEY,
    nombre  VARCHAR(128)    NOT NULL UNIQUE,
    codigo  VARCHAR(16)     NOT NULL UNIQUE   -- código SWIFT u otro identificador
);

COMMENT ON TABLE banco IS 'Instituciones bancarias participantes en el sistema.';


-- Banco operando en un país determinado
CREATE TABLE banco_pais (
    id      SERIAL  PRIMARY KEY,
    id_banco INT    NOT NULL REFERENCES banco(id),
    id_pais  INT    NOT NULL REFERENCES pais(id),
    UNIQUE (id_banco, id_pais)                -- un banco no se duplica por país
);

COMMENT ON TABLE banco_pais IS 'Relación N:M entre bancos y países donde operan.';


-- Cuenta bancaria de un cliente
CREATE TABLE cuenta (
    id              SERIAL          PRIMARY KEY,
    id_cliente      INT             NOT NULL REFERENCES cliente(id),
    id_banco        INT             NOT NULL REFERENCES banco(id),
    id_tipo_cuenta  INT             NOT NULL REFERENCES tipo_cuenta(id),
    id_moneda       INT             NOT NULL REFERENCES moneda(id),
    numero_cuenta   VARCHAR(32)     NOT NULL UNIQUE,
    saldo           NUMERIC(18, 2)  NOT NULL DEFAULT 0.00,
    fecha_apertura  DATE            NOT NULL DEFAULT CURRENT_DATE,
    activa          BOOLEAN         NOT NULL DEFAULT TRUE
);

COMMENT ON TABLE  cuenta              IS 'Cuenta financiera asociada a un cliente en un banco.';
COMMENT ON COLUMN cuenta.saldo        IS 'Saldo actual; se actualiza tras cada transacción aprobada.';
COMMENT ON COLUMN cuenta.numero_cuenta IS 'Número único de cuenta (IBAN u otro formato).';


-- =============================================================
-- TRANSACCIONES
-- =============================================================

-- Transacción financiera
CREATE TABLE transaccion (
    id                      SERIAL          PRIMARY KEY,
    id_cuenta               INT             NOT NULL REFERENCES cuenta(id),
    id_banco                INT             NOT NULL REFERENCES banco(id),
    id_tipo_transaccion     INT             NOT NULL REFERENCES tipo_transaccion(id),
    id_estado_transaccion   INT             NOT NULL REFERENCES estado_transaccion(id),
    id_moneda               INT             NOT NULL REFERENCES moneda(id),
    id_pais                 INT             NOT NULL REFERENCES pais(id),  -- país donde ocurrió
    fecha                   DATE            NOT NULL DEFAULT CURRENT_DATE,
    hora                    TIME            NOT NULL DEFAULT CURRENT_TIME,
    monto                   NUMERIC(18, 2)  NOT NULL,
    descripcion             VARCHAR(256)    NOT NULL,
    ip_origen               VARCHAR(64)     NOT NULL,   -- trazabilidad digital
    canal                   VARCHAR(32)     NOT NULL    -- WEB, APP, ATM, SUCURSAL
);

COMMENT ON TABLE  transaccion          IS 'Registro de cada movimiento financiero realizado.';
COMMENT ON COLUMN transaccion.id_pais  IS 'País donde se originó la transacción (clave para detección geográfica).';
COMMENT ON COLUMN transaccion.canal    IS 'Canal usado: WEB, APP, ATM, SUCURSAL.';
COMMENT ON COLUMN transaccion.ip_origen IS 'IP del dispositivo origen para trazabilidad.';


-- =============================================================
-- FRAUDE Y REVISIÓN
-- =============================================================    

-- Caso de revisión o fraude vinculado a una transacción
CREATE TABLE caso_revision (
    id              SERIAL          PRIMARY KEY,
    id_transaccion  INT             NOT NULL REFERENCES transaccion(id),
    id_regla_fraude INT             NOT NULL REFERENCES regla_fraude(id),
    fecha_apertura  TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_cierre    TIMESTAMP,                          -- NULL si aún abierto
    estado          VARCHAR(32)     NOT NULL DEFAULT 'ABIERTO',  -- ABIERTO, CERRADO, ESCALADO
    resolucion      VARCHAR(512)    NOT NULL DEFAULT 'Pendiente de análisis.',
    analista        VARCHAR(128)    NOT NULL DEFAULT 'SISTEMA'
);

COMMENT ON TABLE  caso_revision              IS 'Caso de investigación por posible fraude o anomalía.';
COMMENT ON COLUMN caso_revision.fecha_cierre IS 'NULL mientras el caso esté activo.';
COMMENT ON COLUMN caso_revision.analista     IS 'Analista asignado o "SISTEMA" si fue generado automáticamente.';
COMMENT ON COLUMN caso_revision.estado       IS 'Estados: ABIERTO, CERRADO, ESCALADO.';


-- =============================================================
-- ÍNDICES PARA RENDIMIENTO
-- =============================================================

-- Búsquedas frecuentes por cliente y fecha en transacciones
CREATE INDEX idx_transaccion_cuenta     ON transaccion(id_cuenta);
CREATE INDEX idx_transaccion_fecha      ON transaccion(fecha);
CREATE INDEX idx_transaccion_hora       ON transaccion(hora);
CREATE INDEX idx_transaccion_estado     ON transaccion(id_estado_transaccion);
CREATE INDEX idx_transaccion_pais       ON transaccion(id_pais);
CREATE INDEX idx_caso_revision_estado   ON caso_revision(estado);
CREATE INDEX idx_cuenta_cliente         ON cuenta(id_cliente);


-- =============================================================
-- DATOS SEMILLA (catálogos mínimos)
-- =============================================================

INSERT INTO nivel_riesgo (nombre, descripcion) VALUES
    ('BAJO',  'Cliente con historial limpio y actividad predecible.'),
    ('MEDIO', 'Cliente con algunas transacciones inusuales o información incompleta.'),
    ('ALTO',  'Cliente con alertas previas o actividad de alto riesgo.');

INSERT INTO estado_transaccion (nombre, descripcion) VALUES
    ('APROBADA',  'Transacción procesada exitosamente.'),
    ('RECHAZADA', 'Transacción denegada por fondos insuficientes u otro motivo.'),
    ('PENDIENTE', 'Transacción en proceso de verificación.'),
    ('REVERTIDA', 'Transacción aprobada que fue anulada posteriormente.');

INSERT INTO tipo_cuenta (nombre, descripcion) VALUES
    ('AHORRO',    'Cuenta de ahorro con tasa de interés.'),
    ('CORRIENTE', 'Cuenta corriente de uso diario.'),
    ('PLAZO_FIJO','Depósito a plazo fijo con rendimiento acordado.');

INSERT INTO tipo_transaccion (nombre, descripcion) VALUES
    ('DEPOSITO',       'Ingreso de fondos a la cuenta.'),
    ('RETIRO',         'Extracción de fondos de la cuenta.'),
    ('TRANSFERENCIA',  'Movimiento de fondos entre cuentas.'),
    ('PAGO',           'Pago de servicios o comercios.'),
    ('COMPRA',         'Cargo por compra con tarjeta o medio digital.');

INSERT INTO regla_fraude (nombre, descripcion) VALUES
    ('MONTO_INUSUAL',
     'Transacción cuyo monto supera significativamente el promedio histórico del cliente.'),
    ('ALTA_FRECUENCIA',
     'Más de N transacciones en una ventana de tiempo corta (ej: 10 en 1 hora).'),
    ('MULTI_PAIS_DIA',
     'Transacciones en países distintos dentro del mismo día calendario.'),
    ('HORARIO_MADRUGADA',
     'Transacción realizada entre las 00:00 y las 05:00 horas.'),
    ('FALLO_SEGUIDO_APROBACION',
     'Una o más transacciones rechazadas inmediatamente antes de una aprobada.'),
    ('ACTIVIDAD_FUERA_PERFIL',
     'Comportamiento que no coincide con el nivel de riesgo ni el perfil habitual del cliente.');

INSERT INTO moneda (codigo, nombre) VALUES
    ('USD', 'Dólar estadounidense'),
    ('CRC', 'Colón costarricense'),
    ('EUR', 'Euro'),
    ('MXN', 'Peso mexicano');

-- =============================================================
-- FIN DEL ESQUEMA
-- =============================================================