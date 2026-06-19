-- =============================================================
-- SCRIPT DE DATOS SEMILLA — BASE DE DATOS BANCARIA
-- Descripción : Poblar la BD con datos realistas que incluyen
--               transacciones normales y patrones sospechosos.
-- Dependencia : Ejecutar banco_schema.sql primero.
-- =============================================================

SET search_path TO banco;

-- ─────────────────────────────────────────────────────────────
-- 1. PAÍSES  (16 países de Latinoamérica, Europa y Norteamérica)
-- ─────────────────────────────────────────────────────────────
INSERT INTO pais (nombre, codigo_iso) VALUES
    ('Costa Rica',          'CR'),
    ('Estados Unidos',      'US'),
    ('México',              'MX'),
    ('Colombia',            'CO'),
    ('Panamá',              'PA'),
    ('España',              'ES'),
    ('Alemania',            'DE'),
    ('Francia',             'FR'),
    ('Brasil',              'BR'),
    ('Argentina',           'AR'),
    ('Chile',               'CL'),
    ('Perú',                'PE'),
    ('Ecuador',             'EC'),
    ('Guatemala',           'GT'),
    ('Honduras',            'HN'),
    ('El Salvador',         'SV');


-- ─────────────────────────────────────────────────────────────
-- 2. NACIONALIDADES  (una por país)
-- ─────────────────────────────────────────────────────────────
INSERT INTO nacionalidad (id_pais, gentilicio) VALUES
    (1,  'Costarricense'),
    (2,  'Estadounidense'),
    (3,  'Mexicana'),
    (4,  'Colombiana'),
    (5,  'Panameña'),
    (6,  'Española'),
    (7,  'Alemana'),
    (8,  'Francesa'),
    (9,  'Brasileña'),
    (10, 'Argentina'),
    (11, 'Chilena'),
    (12, 'Peruana'),
    (13, 'Ecuatoriana'),
    (14, 'Guatemalteca'),
    (15, 'Hondureña'),
    (16, 'Salvadoreña');


-- ─────────────────────────────────────────────────────────────
-- 3. MONEDAS ADICIONALES
-- ─────────────────────────────────────────────────────────────
-- USD, CRC, EUR, MXN ya insertados en el schema.
INSERT INTO moneda (codigo, nombre) VALUES
    ('COP', 'Peso colombiano'),
    ('PAB', 'Balboa panameño'),
    ('GTQ', 'Quetzal guatemalteco'),
    ('BRL', 'Real brasileño'),
    ('ARS', 'Peso argentino'),
    ('CLP', 'Peso chileno'),
    ('PEN', 'Sol peruano');


-- ─────────────────────────────────────────────────────────────
-- 4. BANCOS  (12 instituciones ficticias pero verosímiles)
-- ─────────────────────────────────────────────────────────────
INSERT INTO banco (nombre, codigo) VALUES
    ('Banco Nacional de Costa Rica',    'BNCRCR'),
    ('Banco de América Central',        'BACCR'),
    ('Promerica Financial Group',       'PROMFI'),
    ('Scotiabank Latinoamérica',        'SCOBLA'),
    ('HSBC Latinoamérica',              'HSBCLA'),
    ('Banco Davivienda',                'DAVIVI'),
    ('Banco de Bogotá',                 'BOGOTA'),
    ('BBVA México',                     'BBVAMX'),
    ('Santander España',                'SANTES'),
    ('Deutsche Bank Europa',            'DEUTEU'),
    ('BNP Paribas',                     'BNPPFR'),
    ('Itaú Unibanco',                   'ITAUBU');


-- ─────────────────────────────────────────────────────────────
-- 5. BANCO × PAÍS  (presencia geográfica realista)
-- ─────────────────────────────────────────────────────────────
INSERT INTO banco_pais (id_banco, id_pais) VALUES
    -- BNCR: solo Costa Rica
    (1, 1),
    -- BAC: Centroamérica y Panamá
    (2, 1),(2, 5),(2, 14),(2, 15),(2, 16),
    -- Promerica: Centroamérica y Panamá
    (3, 1),(3, 5),(3, 14),(3, 15),(3, 16),(3, 3),
    -- Scotiabank: varios países
    (4, 1),(4, 2),(4, 3),(4, 4),(4, 11),(4, 12),
    -- HSBC: presencia global
    (5, 2),(5, 3),(5, 6),(5, 7),(5, 8),(5, 9),
    -- Davivienda: Colombia y Centroamérica
    (6, 4),(6, 1),(6, 5),(6, 14),(6, 15),(6, 16),
    -- Banco de Bogotá: Colombia, Panamá, EEUU
    (7, 4),(7, 5),(7, 2),
    -- BBVA México: México, España y EEUU
    (8, 3),(8, 6),(8, 2),
    -- Santander España: Europa y Latam
    (9, 6),(9, 3),(9, 9),(9, 10),(9, 11),(9, 2),
    -- Deutsche Bank: Europa y EEUU
    (10, 7),(10, 8),(10, 6),(10, 2),
    -- BNP Paribas: Europa y Latam
    (11, 8),(11, 6),(11, 7),(11, 9),(11, 10),
    -- Itaú: Brasil, Argentina, Chile, Colombia, EEUU
    (12, 9),(12, 10),(12, 11),(12, 4),(12, 2);


-- ─────────────────────────────────────────────────────────────
-- 6. PERSONAS  (60 personas con datos verosímiles)
-- ─────────────────────────────────────────────────────────────
INSERT INTO persona (id_nacionalidad, nombre, apellido, identificacion, fecha_nac, email, telefono) VALUES
-- Costarricenses (id_nac=1)
(1,  'Andrés',    'Mora Jiménez',       'CR-10012345', '1985-03-12', 'andres.mora@email.cr',       '+50688001001'),
(1,  'Sofía',     'Rodríguez Vargas',   'CR-10023456', '1992-07-24', 'sofia.rodriguez@email.cr',   '+50688001002'),
(1,  'Carlos',    'Quesada López',      'CR-10034567', '1978-11-05', 'carlos.quesada@email.cr',    '+50688001003'),
(1,  'Valeria',   'Solís Brenes',       'CR-10045678', '1995-01-30', 'valeria.solis@email.cr',     '+50688001004'),
(1,  'Miguel',    'Herrera Castro',     'CR-10056789', '1970-09-18', 'miguel.herrera@email.cr',    '+50688001005'),
-- Colombianos (id_nac=4)
(4,  'Camila',    'Torres Ríos',        'CO-20011111', '1988-04-22', 'camila.torres@email.co',     '+57301001001'),
(4,  'Sebastián', 'García Muñoz',       'CO-20022222', '1993-08-15', 'sebastian.garcia@email.co',  '+57301001002'),
(4,  'Isabella',  'López Restrepo',     'CO-20033333', '1980-12-01', 'isabella.lopez@email.co',    '+57301001003'),
(4,  'Mateo',     'Ramírez Ospina',     'CO-20044444', '1975-06-10', 'mateo.ramirez@email.co',     '+57301001004'),
(4,  'Valentina', 'Vargas Salazar',     'CO-20055555', '1998-02-28', 'valentina.vargas@email.co',  '+57301001005'),
-- Mexicanos (id_nac=3)
(3,  'Diego',     'Hernández Cruz',     'MX-30011111', '1983-10-07', 'diego.hernandez@email.mx',   '+52551001001'),
(3,  'Lucía',     'Martínez Flores',    'MX-30022222', '1990-05-19', 'lucia.martinez@email.mx',    '+52551001002'),
(3,  'Emilio',    'Sánchez Vega',       'MX-30033333', '1972-03-25', 'emilio.sanchez@email.mx',    '+52551001003'),
(3,  'Fernanda',  'Gutiérrez Ruiz',     'MX-30044444', '1996-11-11', 'fernanda.gutierrez@email.mx','+52551001004'),
(3,  'Javier',    'Morales Peña',       'MX-30055555', '1968-08-30', 'javier.morales@email.mx',    '+52551001005'),
-- Panameños (id_nac=5)
(5,  'Daniela',   'Arias Mendoza',      'PA-40011111', '1987-01-14', 'daniela.arias@email.pa',     '+50764001001'),
(5,  'Roberto',   'Castro Núñez',       'PA-40022222', '1979-07-03', 'roberto.castro@email.pa',    '+50764001002'),
(5,  'Gabriela',  'Delgado Aguilar',    'PA-40033333', '1994-09-22', 'gabriela.delgado@email.pa',  '+50764001003'),
-- Españoles (id_nac=6)
(6,  'Pablo',     'Fernández Iglesias', 'ES-50011111', '1986-04-16', 'pablo.fernandez@email.es',   '+34611001001'),
(6,  'Carmen',    'Navarro Serrano',    'ES-50022222', '1991-12-08', 'carmen.navarro@email.es',    '+34611001002'),
(6,  'Antonio',   'Ruiz Blanco',        'ES-50033333', '1965-02-20', 'antonio.ruiz@email.es',      '+34611001003'),
-- Alemanes (id_nac=7)
(7,  'Klaus',     'Müller Schmidt',     'DE-60011111', '1982-06-11', 'klaus.mueller@email.de',     '+49151001001'),
(7,  'Heike',     'Bauer Wagner',       'DE-60022222', '1977-10-29', 'heike.bauer@email.de',       '+49151001002'),
-- Franceses (id_nac=8)
(8,  'Julien',    'Dubois Martin',      'FR-70011111', '1989-03-05', 'julien.dubois@email.fr',     '+33601001001'),
(8,  'Marie',     'Leroy Bernard',      'FR-70022222', '1993-08-17', 'marie.leroy@email.fr',       '+33601001002'),
-- Brasileños (id_nac=9)
(9,  'Bruno',     'Silva Oliveira',     'BR-80011111', '1984-11-22', 'bruno.silva@email.br',       '+55119001001'),
(9,  'Ana',       'Costa Souza',        'BR-80022222', '1990-05-30', 'ana.costa@email.br',         '+55119001002'),
(9,  'Rodrigo',   'Pereira Santos',     'BR-80033333', '1976-01-07', 'rodrigo.pereira@email.br',   '+55119001003'),
-- Argentinos (id_nac=10)
(10, 'Nicolás',   'González Pérez',     'AR-90011111', '1988-07-19', 'nicolas.gonzalez@email.ar',  '+54911001001'),
(10, 'Florencia', 'Díaz Romero',        'AR-90022222', '1995-04-03', 'florencia.diaz@email.ar',    '+54911001002'),
-- Chilenos (id_nac=11)
(11, 'Ignacio',   'Muñoz Tapia',        'CL-00111111', '1981-09-14', 'ignacio.munoz@email.cl',     '+56991001001'),
(11, 'Catalina',  'Reyes Espinoza',     'CL-00222222', '1997-02-25', 'catalina.reyes@email.cl',    '+56991001002'),
-- Peruanos (id_nac=12)
(12, 'Álvaro',    'Chávez Huanca',      'PE-11100001', '1974-06-06', 'alvaro.chavez@email.pe',     '+51991001001'),
(12, 'Paola',     'Quispe Mamani',      'PE-11100002', '1992-10-18', 'paola.quispe@email.pe',      '+51991001002'),
-- Ecuatorianos (id_nac=13)
(13, 'Esteban',   'Moreno Cabrera',     'EC-12200001', '1980-03-31', 'esteban.moreno@email.ec',    '+59391001001'),
(13, 'Natalia',   'Vega Intriago',      'EC-12200002', '1999-08-09', 'natalia.vega@email.ec',      '+59391001002'),
-- Guatemaltecos (id_nac=14)
(14, 'Marco',     'Coto Tzul',          'GT-13300001', '1973-12-15', 'marco.coto@email.gt',        '+50291001001'),
(14, 'Rosa',      'Ajú Sic',            'GT-13300002', '1985-05-27', 'rosa.aju@email.gt',          '+50291001002'),
-- Hondureños (id_nac=15)
(15, 'Luis',      'Amador Rivas',       'HN-14400001', '1977-09-02', 'luis.amador@email.hn',       '+50498001001'),
(15, 'Elena',     'Mejía Andino',       'HN-14400002', '1994-01-21', 'elena.mejia@email.hn',       '+50498001002'),
-- Salvadoreños (id_nac=16)
(16, 'Kevin',     'Portillo Mena',      'SV-15500001', '1991-07-08', 'kevin.portillo@email.sv',    '+50379001001'),
(16, 'Diana',     'Romero Calles',      'SV-15500002', '1983-11-14', 'diana.romero@email.sv',      '+50379001002'),
-- Estadounidenses (id_nac=2) — perfiles mixtos
(2,  'James',     'Williams Harper',    'US-21100001', '1979-04-09', 'james.williams@email.us',    '+12125001001'),
(2,  'Linda',     'Johnson Clark',      'US-21100002', '1987-08-23', 'linda.johnson@email.us',     '+12125001002'),
(2,  'Robert',    'Davis Mitchell',     'US-21100003', '1965-01-17', 'robert.davis@email.us',      '+12125001003'),
-- Clientes de alto riesgo (nacionales variados, serán marcados en cliente)
(1,  'Ernesto',   'Prado Méndez',       'CR-99900001', '1970-02-14', 'ernesto.prado@email.cr',     '+50688009001'),
(4,  'Ricardo',   'Blanco Uribe',       'CO-99900002', '1975-06-20', 'ricardo.blanco@email.co',    '+57301009002'),
(3,  'Fernando',  'Leal Ochoa',         'MX-99900003', '1968-11-30', 'fernando.leal@email.mx',     '+52551009003'),
(5,  'Héctor',    'Guzmán Pineda',      'PA-99900004', '1980-03-05', 'hector.guzman@email.pa',     '+50764009004'),
(6,  'Óscar',     'Vidal Fuentes',      'ES-99900005', '1972-09-15', 'oscar.vidal@email.es',       '+34611009005'),
(2,  'Marcus',    'Reynolds Stone',     'US-99900006', '1969-07-22', 'marcus.reynolds@email.us',   '+12125009006'),
(9,  'Thiago',    'Nascimento Lima',    'BR-99900007', '1977-12-03', 'thiago.nascimento@email.br', '+55119009007'),
(10, 'Marcos',    'Ibáñez Vera',        'AR-99900008', '1983-04-28', 'marcos.ibanez@email.ar',     '+54911009008'),
(7,  'Stefan',    'Richter Krause',     'DE-99900009', '1971-08-11', 'stefan.richter@email.de',    '+49151009009'),
(11, 'Felipe',    'Acuña Palma',        'CL-99900010', '1984-01-19', 'felipe.acuna@email.cl',      '+56991009010'),
(12, 'Gustavo',   'Flores Vargas',      'PE-99900011', '1973-05-08', 'gustavo.flores@email.pe',     '+51991009011');


-- ─────────────────────────────────────────────────────────────
-- 7. CLIENTES  (60 clientes; personas 47-56 = ALTO riesgo)
-- ─────────────────────────────────────────────────────────────
INSERT INTO cliente (id_persona, id_nivel_riesgo, fecha_alta, activo) VALUES
-- BAJO riesgo (id_nivel_riesgo=1)
(1,  1, '2015-03-10', TRUE),
(2,  1, '2016-07-22', TRUE),
(3,  1, '2010-11-05', TRUE),
(4,  1, '2019-01-30', TRUE),
(5,  1, '2008-09-18', TRUE),
(6,  1, '2017-04-12', TRUE),
(7,  1, '2020-08-05', TRUE),
(8,  1, '2012-12-01', TRUE),
(9,  1, '2007-06-10', TRUE),
(10, 1, '2021-02-28', TRUE),
(11, 1, '2014-10-07', TRUE),
(12, 1, '2018-05-19', TRUE),
(13, 1, '2005-03-25', TRUE),
(14, 1, '2022-11-11', TRUE),
(15, 1, '2003-08-30', TRUE),
(16, 1, '2016-01-14', TRUE),
(17, 1, '2009-07-03', TRUE),
(18, 1, '2021-09-22', TRUE),
(19, 1, '2013-04-16', TRUE),
(20, 1, '2019-12-08', TRUE),
-- MEDIO riesgo (id_nivel_riesgo=2)
(21, 2, '2001-02-20', TRUE),
(22, 2, '2017-06-11', TRUE),
(23, 2, '2011-10-29', TRUE),
(24, 2, '2020-03-05', TRUE),
(25, 2, '2015-08-17', TRUE),
(26, 2, '2013-11-22', TRUE),
(27, 2, '2018-05-30', TRUE),
(28, 2, '2006-01-07', TRUE),
(29, 2, '2022-07-19', TRUE),
(30, 2, '2016-04-03', TRUE),
(31, 2, '2010-09-14', TRUE),
(32, 2, '2023-02-25', TRUE),
(33, 2, '2004-06-06', TRUE),
(34, 2, '2019-10-18', TRUE),
(35, 2, '2008-03-31', TRUE),
(36, 2, '2024-08-09', TRUE),
(37, 2, '2012-12-15', TRUE),
(38, 2, '2017-05-27', TRUE),
(39, 2, '2007-09-02', TRUE),
(40, 2, '2021-01-21', TRUE),
(41, 2, '2014-07-08', TRUE),
(42, 2, '2009-11-14', TRUE),
(43, 2, '2018-04-09', TRUE),
(44, 2, '2022-08-23', TRUE),
(45, 2, '2011-01-17', TRUE),
(46, 2, '2015-03-14', TRUE),
-- ALTO riesgo (id_nivel_riesgo=3)  ← personas 47–56
(47, 3, '2016-06-20', TRUE),
(48, 3, '2010-11-30', TRUE),
(49, 3, '2019-03-05', TRUE),
(50, 3, '2013-09-15', TRUE),
(51, 3, '2005-07-22', TRUE),
(52, 3, '2020-12-03', TRUE),
(53, 3, '2017-04-28', TRUE),
(54, 3, '2008-08-11', TRUE),
(55, 3, '2021-01-19', TRUE),
(56, 3, '2000-02-14', TRUE);


-- ─────────────────────────────────────────────────────────────
-- 8. CUENTAS  (≈ 80 cuentas distribuidas entre bancos y clientes)
-- Formato numero_cuenta:  BBBB-CCCC-NNNN  (banco-cliente-seq)
-- ─────────────────────────────────────────────────────────────
INSERT INTO cuenta (id_cliente, id_banco, id_tipo_cuenta, id_moneda, numero_cuenta, saldo, fecha_apertura, activa) VALUES
-- Clientes BAJO riesgo — cuentas ordinarias
(1,  1, 1, 2, 'BNCR-0001-0001', 1850000.00, '2015-03-10', TRUE),
(2,  1, 2, 2, 'BNCR-0002-0001', 450000.00,  '2016-07-22', TRUE),
(3,  2, 1, 1, 'BAC-0003-0001',   8200.00,   '2010-11-05', TRUE),
(4,  2, 2, 1, 'BAC-0004-0001',   3100.50,   '2019-01-30', TRUE),
(5,  3, 3, 2, 'PROM-0005-0001', 5000000.00, '2008-09-18', TRUE),
(6,  6, 1, 5, 'DAVI-0006-0001', 12000000.00,'2017-04-12', TRUE),
(7,  6, 2, 5, 'DAVI-0007-0001',  3200000.00,'2020-08-05', TRUE),
(8,  7, 1, 5, 'BOG-0008-0001',   9500000.00,'2012-12-01', TRUE),
(9,  7, 2, 5, 'BOG-0009-0001',   1800000.00,'2007-06-10', TRUE),
(10, 6, 3, 5, 'DAVI-0010-0001', 45000000.00,'2021-02-28', TRUE),
(11, 8, 1, 3, 'BBVA-0011-0001',  28500.00,  '2014-10-07', TRUE),
(12, 8, 2, 3, 'BBVA-0012-0001',   6200.75,  '2018-05-19', TRUE),
(13, 8, 1, 3, 'BBVA-0013-0001', 180000.00,  '2005-03-25', TRUE),
(14, 8, 2, 3, 'BBVA-0014-0001',   2100.00,  '2022-11-11', TRUE),
(15, 8, 3, 3, 'BBVA-0015-0001', 750000.00,  '2003-08-30', TRUE),
(16, 3, 1, 2, 'PROM-0016-0001',  650000.00, '2016-01-14', TRUE),
(17, 2, 2, 1, 'BAC-0017-0001',    1900.00,  '2009-07-03', TRUE),
(18, 3, 1, 2, 'PROM-0018-0001',  280000.00, '2021-09-22', TRUE),
(19, 9, 1, 4, 'SANT-0019-0001',  54000.00,  '2013-04-16', TRUE),
(20, 9, 2, 4, 'SANT-0020-0001',  12000.00,  '2019-12-08', TRUE),
-- Clientes MEDIO riesgo
(21, 9, 1, 4, 'SANT-0021-0001', 320000.00,  '2001-02-20', TRUE),
(22, 10, 1, 4, 'DEUT-0022-0001',  98000.00,  '2017-06-11', TRUE),
(23, 10, 2, 4, 'DEUT-0023-0001',  14000.00,  '2011-10-29', TRUE),
(24, 11, 1, 4, 'BNP-0024-0001',  210000.00,  '2020-03-05', TRUE),
(25, 11, 2, 8, 'BNP-0025-0001',   85000.00,  '2015-08-17', TRUE),
(26, 12, 1, 8, 'ITAU-0026-0001', 132000.00,  '2013-11-22', TRUE),
(27, 12, 2, 8, 'ITAU-0027-0001',  29000.00,  '2018-05-30', TRUE),
(28, 12, 1, 8, 'ITAU-0028-0001', 780000.00,  '2006-01-07', TRUE),
(29, 12, 3, 9, 'ITAU-0029-0001', 450000.00,  '2022-07-19', TRUE),
(30, 12, 1, 9, 'ITAU-0030-0001',  66000.00,  '2016-04-03', TRUE),
(31, 4, 1, 10, 'SCOT-0031-0001',  48000.00,  '2010-09-14', TRUE),
(32, 4, 2, 10, 'SCOT-0032-0001',   9000.00,  '2023-02-25', TRUE),
(33, 4, 1, 10, 'SCOT-0033-0001', 520000.00,  '2004-06-06', TRUE),
(34, 4, 2, 11, 'SCOT-0034-0001',  17500.00,  '2019-10-18', TRUE),
(35, 4, 1, 1, 'SCOT-0035-0001',   33000.00,  '2008-03-31', TRUE),
(36, 1, 1, 2, 'BNCR-0036-0001',  890000.00,  '2024-08-09', TRUE),
(37, 2, 2, 2, 'BAC-0037-0001',   110000.00,  '2012-12-15', TRUE),
(38, 2, 1, 2, 'BAC-0038-0001',   240000.00,  '2017-05-27', TRUE),
(39, 3, 2, 2, 'PROM-0039-0001',   55000.00,  '2007-09-02', TRUE),
(40, 3, 1, 2, 'PROM-0040-0001',  410000.00,  '2021-01-21', TRUE),
(41, 4, 2, 1, 'SCOT-0041-0001',    7200.00,  '2014-07-08', TRUE),
(42, 5, 1, 1, 'HSBC-0042-0001',   42000.00,  '2009-11-14', TRUE),
(43, 5, 2, 1, 'HSBC-0043-0001',   18000.00,  '2018-04-09', TRUE),
(44, 5, 1, 1, 'HSBC-0044-0001',  210000.00,  '2022-08-23', TRUE),
(45, 5, 2, 1, 'HSBC-0045-0001',   63000.00,  '2011-01-17', TRUE),
(46, 5, 1, 1, 'HSBC-0046-0001',  175000.00,  '2015-03-14', TRUE),
-- Clientes ALTO riesgo — múltiples cuentas en varios bancos
(47, 4, 1, 2, 'SCOT-0047-0001',  920000.00,  '2016-06-20', TRUE),
(47, 5, 2, 1, 'HSBC-0047-0002',   58000.00,  '2018-11-15', TRUE),
(48, 6, 1, 5, 'DAVI-0048-0001', 8800000.00,  '2010-11-30', TRUE),
(48, 7, 2, 5, 'BOG-0048-0002',  2100000.00,  '2014-03-22', TRUE),
(49, 8, 1, 3, 'BBVA-0049-0001',  620000.00,  '2019-03-05', TRUE),
(49, 9, 2, 4, 'SANT-0049-0002',  310000.00,  '2020-07-18', TRUE),
(50, 5, 1, 1, 'HSBC-0050-0001',  190000.00,  '2013-09-15', TRUE),
(51, 9, 1, 4, 'SANT-0051-0001', 1200000.00,  '2005-07-22', TRUE),
(51, 10, 2, 4, 'DEUT-0051-0002',  480000.00, '2012-02-10', TRUE),
(52, 12, 1, 8, 'ITAU-0052-0001', 3400000.00, '2020-12-03', TRUE),
(52, 11, 2, 4, 'BNP-0052-0002',   720000.00, '2021-05-17', TRUE),
(53, 12, 1, 9, 'ITAU-0053-0001', 9900000.00, '2017-04-28', TRUE),
(54, 10, 1, 4, 'DEUT-0054-0001',  560000.00, '2008-08-11', TRUE),
(55, 4, 1, 10, 'SCOT-0055-0001', 2200000.00, '2021-01-19', TRUE),
(56, 1, 1, 2, 'BNCR-0056-0001', 3500000.00,  '2000-02-14', TRUE),
(56, 2, 2, 1, 'BAC-0056-0002',    95000.00,  '2005-08-30', TRUE);


-- ─────────────────────────────────────────────────────────────
-- HELPER: IDs de catálogos usados frecuentemente
-- estado_transaccion: 1=APROBADA, 2=RECHAZADA, 3=PENDIENTE, 4=REVERTIDA
-- tipo_transaccion:   1=DEPOSITO, 2=RETIRO, 3=TRANSFERENCIA, 4=PAGO, 5=COMPRA
-- pais IDs:           1=CR, 2=US, 3=MX, 4=CO, 5=PA, 6=ES, 7=DE, 8=FR, 9=BR, 10=AR, 11=CL
-- moneda IDs:         1=USD,2=CRC,3=MXN,4=EUR,5=COP,6=PAB,7=GTQ,8=BRL,9=ARS,10=CLP,11=PEN
-- ─────────────────────────────────────────────────────────────


-- ─────────────────────────────────────────────────────────────
-- 9. TRANSACCIONES NORMALES  (comportamiento esperado)
-- ─────────────────────────────────────────────────────────────

INSERT INTO transaccion
    (id_cuenta, id_banco, id_tipo_transaccion, id_estado_transaccion, id_moneda, id_pais, fecha, hora, monto, descripcion, ip_origen, canal)
VALUES
-- Cliente 1 (BAJO): depósitos y pagos rutinarios en CR
(1,  1, 1, 1, 2, 1, '2024-01-05', '09:15:00',  250000.00, 'Depósito de salario enero',         '192.168.1.10', 'SUCURSAL'),
(1,  1, 4, 1, 2, 1, '2024-01-10', '11:30:00',   45000.00, 'Pago servicio eléctrico',            '192.168.1.10', 'APP'),
(1,  1, 4, 1, 2, 1, '2024-01-15', '10:00:00',   18000.00, 'Pago agua y alcantarillado',         '192.168.1.10', 'APP'),
(1,  1, 5, 1, 2, 1, '2024-01-22', '14:45:00',   32000.00, 'Compra supermercado',                '192.168.1.10', 'WEB'),
(1,  1, 1, 1, 2, 1, '2024-02-05', '09:10:00',  250000.00, 'Depósito de salario febrero',        '192.168.1.10', 'SUCURSAL'),
(1,  1, 2, 1, 2, 1, '2024-02-14', '16:00:00',  100000.00, 'Retiro efectivo',                    '10.0.0.5',     'ATM'),
-- Cliente 2 (BAJO): transacciones pequeñas, perfil estudiante
(2,  1, 1, 1, 2, 1, '2024-01-03', '08:00:00',  150000.00, 'Transferencia recibida de familia',  '10.10.1.22',   'APP'),
(2,  1, 4, 1, 2, 1, '2024-01-08', '12:00:00',   12000.00, 'Pago internet',                      '10.10.1.22',   'APP'),
(2,  1, 5, 1, 2, 1, '2024-01-20', '13:30:00',   28000.00, 'Compra librería',                    '10.10.1.22',   'WEB'),
(2,  1, 2, 1, 2, 1, '2024-02-01', '10:30:00',   50000.00, 'Retiro efectivo quincena',           '10.0.0.7',     'ATM'),
-- Cliente 3 (BAJO): transacciones en USD
(3,  2, 1, 1, 1, 1, '2024-01-04', '09:00:00',    1200.00, 'Depósito salario',                   '172.16.0.33',  'SUCURSAL'),
(3,  2, 5, 1, 1, 1, '2024-01-12', '15:00:00',     185.00, 'Compra en línea',                    '172.16.0.33',  'WEB'),
(3,  2, 4, 1, 1, 1, '2024-01-20', '11:00:00',      95.00, 'Pago suscripción streaming',         '172.16.0.33',  'APP'),
(3,  2, 2, 1, 1, 1, '2024-02-02', '10:00:00',     400.00, 'Retiro efectivo',                    '10.0.0.12',    'ATM'),
-- Cliente 6 (BAJO): Colombia, COP
(6,  6, 1, 1, 5, 4, '2024-01-05', '08:30:00', 4500000.00, 'Nómina enero',                       '10.20.1.44',   'SUCURSAL'),
(6,  6, 4, 1, 5, 4, '2024-01-10', '10:00:00',  320000.00, 'Pago arriendo',                      '10.20.1.44',   'APP'),
(6,  6, 5, 1, 5, 4, '2024-01-18', '16:30:00',  180000.00, 'Compra supermercado',                '10.20.1.44',   'WEB'),
(6,  6, 1, 1, 5, 4, '2024-02-05', '08:30:00', 4500000.00, 'Nómina febrero',                     '10.20.1.44',   'SUCURSAL'),
-- Cliente 11 (BAJO): México, MXN
(11, 8, 1, 1, 3, 3, '2024-01-03', '09:00:00',   22000.00, 'Depósito quincenal',                 '192.168.5.11', 'SUCURSAL'),
(11, 8, 4, 1, 3, 3, '2024-01-10', '11:30:00',    3200.00, 'Pago teléfono',                      '192.168.5.11', 'APP'),
(11, 8, 5, 1, 3, 3, '2024-01-17', '14:00:00',    5800.00, 'Compra farmacia',                    '192.168.5.11', 'WEB'),
(11, 8, 2, 1, 3, 3, '2024-01-28', '12:00:00',    8000.00, 'Retiro quincena',                    '10.0.0.22',    'ATM'),
-- Cliente 19 (BAJO): España, EUR
(19, 9, 1, 1, 4, 6, '2024-01-04', '09:30:00',    3200.00, 'Nómina enero',                       '10.30.2.55',   'SUCURSAL'),
(19, 9, 4, 1, 4, 6, '2024-01-08', '10:00:00',     850.00, 'Pago alquiler',                      '10.30.2.55',   'APP'),
(19, 9, 5, 1, 4, 6, '2024-01-15', '13:00:00',     220.00, 'Compra alimentación',                '10.30.2.55',   'WEB'),
(19, 9, 4, 1, 4, 6, '2024-01-22', '11:00:00',     120.00, 'Pago servicios hogar',               '10.30.2.55',   'APP'),
-- Cliente 22 (MEDIO): Alemania, EUR
(22, 10, 1, 1, 4, 7, '2024-01-05', '08:00:00',    4100.00, 'Salario mensual',                   '10.40.3.66',   'SUCURSAL'),
(22, 10, 4, 1, 4, 7, '2024-01-09', '09:30:00',    1200.00, 'Renta apartamento',                 '10.40.3.66',   'APP'),
(22, 10, 5, 1, 4, 7, '2024-01-16', '17:00:00',     340.00, 'Supermercado',                      '10.40.3.66',   'WEB'),
(22, 10, 2, 1, 4, 7, '2024-02-01', '10:00:00',     600.00, 'Retiro efectivo',                   '10.0.0.44',    'ATM'),
-- Cliente 26 (MEDIO): Brasil, BRL
(26, 12, 1, 1, 8, 9, '2024-01-04', '08:00:00',    8500.00, 'Pagamento salário',                 '172.20.1.77',  'SUCURSAL'),
(26, 12, 4, 1, 8, 9, '2024-01-09', '10:00:00',    1800.00, 'Pagamento aluguel',                 '172.20.1.77',  'APP'),
(26, 12, 5, 1, 8, 9, '2024-01-20', '15:00:00',     650.00, 'Compra supermercado',               '172.20.1.77',  'WEB'),
-- Cliente 31 (MEDIO): Chile, CLP
(31, 4, 1, 1, 10, 11, '2024-01-05', '09:00:00', 1250000.00, 'Remuneración mensual',             '10.50.4.88',   'SUCURSAL'),
(31, 4, 4, 1, 10, 11, '2024-01-10', '10:30:00',  350000.00, 'Dividendo arriendo',               '10.50.4.88',   'APP'),
(31, 4, 5, 1, 10, 11, '2024-01-18', '14:00:00',   95000.00, 'Compra retail',                    '10.50.4.88',   'WEB'),
-- Cliente 42 (MEDIO): EEUU, USD
(42, 5, 1, 1, 1, 2, '2024-01-04', '08:00:00',    5200.00, 'Paycheck direct deposit',            '192.168.10.5', 'APP'),
(42, 5, 4, 1, 1, 2, '2024-01-08', '10:00:00',    1800.00, 'Rent payment',                       '192.168.10.5', 'APP'),
(42, 5, 5, 1, 1, 2, '2024-01-15', '12:00:00',     320.00, 'Grocery store',                      '192.168.10.5', 'WEB'),
(42, 5, 2, 1, 1, 2, '2024-01-25', '11:00:00',     500.00, 'Cash withdrawal',                    '10.0.0.55',    'ATM');


-- ─────────────────────────────────────────────────────────────
-- 10. TRANSACCIONES SOSPECHOSAS
-- ─────────────────────────────────────────────────────────────

-- ══════════════════════════════════════════════
-- TIPO 1 — MONTOS INUSUALMENTE ALTOS
-- Cliente 47 (ALTO): su promedio es ~500k CRC, sube a 45M sin justificación
-- ══════════════════════════════════════════════
INSERT INTO transaccion
    (id_cuenta, id_banco, id_tipo_transaccion, id_estado_transaccion, id_moneda, id_pais, fecha, hora, monto, descripcion, ip_origen, canal)
VALUES
(47, 4, 1, 1, 2, 1, '2024-03-01', '14:22:00',   480000.00, 'Depósito ordinario marzo',          '10.1.1.47', 'APP'),
(47, 4, 1, 1, 2, 1, '2024-03-05', '10:00:00',   510000.00, 'Depósito rutinario',                '10.1.1.47', 'SUCURSAL'),
-- Monto inusual: 45x el promedio histórico
(47, 4, 1, 1, 2, 1, '2024-03-12', '11:33:00', 22500000.00, 'Depósito recibido de tercero',      '10.1.1.47', 'WEB'),
(47, 4, 2, 1, 2, 1, '2024-03-12', '11:50:00', 21000000.00, 'Retiro inmediato tras depósito',    '10.1.1.47', 'ATM'),

-- Cliente 56 (ALTO): transferencia masiva en USD
(56, 2, 3, 1, 1, 1, '2024-03-15', '09:00:00',   85000.00, 'Transferencia internacional salida', '10.1.1.56', 'WEB');


-- ══════════════════════════════════════════════
-- TIPO 2 — MUCHAS TRANSACCIONES EN PERIODO CORTO
-- Cliente 48 (ALTO): 12 transacciones en 40 minutos el mismo día
-- ══════════════════════════════════════════════
INSERT INTO transaccion
    (id_cuenta, id_banco, id_tipo_transaccion, id_estado_transaccion, id_moneda, id_pais, fecha, hora, monto, descripcion, ip_origen, canal)
VALUES
(49, 6, 5, 1, 5, 4, '2024-03-20', '02:01:00',  180000.00, 'Compra en línea #1',   '45.60.70.81', 'WEB'),
(49, 6, 5, 1, 5, 4, '2024-03-20', '02:04:00',  175000.00, 'Compra en línea #2',   '45.60.70.81', 'WEB'),
(49, 6, 5, 1, 5, 4, '2024-03-20', '02:07:00',  182000.00, 'Compra en línea #3',   '45.60.70.82', 'WEB'),
(49, 6, 5, 1, 5, 4, '2024-03-20', '02:10:00',  178000.00, 'Compra en línea #4',   '45.60.70.82', 'WEB'),
(49, 6, 5, 1, 5, 4, '2024-03-20', '02:13:00',  190000.00, 'Compra en línea #5',   '45.60.70.83', 'WEB'),
(49, 6, 5, 1, 5, 4, '2024-03-20', '02:16:00',  171000.00, 'Compra en línea #6',   '45.60.70.83', 'WEB'),
(49, 6, 5, 1, 5, 4, '2024-03-20', '02:19:00',  185000.00, 'Compra en línea #7',   '45.60.70.84', 'WEB'),
(49, 6, 5, 1, 5, 4, '2024-03-20', '02:22:00',  177000.00, 'Compra en línea #8',   '45.60.70.84', 'WEB'),
(49, 6, 5, 1, 5, 4, '2024-03-20', '02:25:00',  183000.00, 'Compra en línea #9',   '45.60.70.85', 'WEB'),
(49, 6, 5, 1, 5, 4, '2024-03-20', '02:28:00',  169000.00, 'Compra en línea #10',  '45.60.70.85', 'WEB'),
(49, 6, 5, 1, 5, 4, '2024-03-20', '02:31:00',  192000.00, 'Compra en línea #11',  '45.60.70.86', 'WEB'),
(49, 6, 5, 1, 5, 4, '2024-03-20', '02:34:00',  174000.00, 'Compra en línea #12',  '45.60.70.86', 'WEB'),

-- Cliente 36 (MEDIO): también ráfaga sospechosa, 8 transacciones en 25 min
(36, 1, 4, 1, 2, 1, '2024-04-10', '03:05:00',   15000.00, 'Pago recurrente #1',   '10.1.2.36', 'APP'),
(36, 1, 4, 1, 2, 1, '2024-04-10', '03:08:00',   15000.00, 'Pago recurrente #2',   '10.1.2.36', 'APP'),
(36, 1, 4, 1, 2, 1, '2024-04-10', '03:11:00',   15000.00, 'Pago recurrente #3',   '10.1.2.37', 'APP'),
(36, 1, 4, 1, 2, 1, '2024-04-10', '03:14:00',   15000.00, 'Pago recurrente #4',   '10.1.2.37', 'APP'),
(36, 1, 4, 1, 2, 1, '2024-04-10', '03:17:00',   15000.00, 'Pago recurrente #5',   '10.1.2.38', 'APP'),
(36, 1, 4, 1, 2, 1, '2024-04-10', '03:20:00',   15000.00, 'Pago recurrente #6',   '10.1.2.38', 'APP'),
(36, 1, 4, 1, 2, 1, '2024-04-10', '03:23:00',   15000.00, 'Pago recurrente #7',   '10.1.2.39', 'APP'),
(36, 1, 4, 1, 2, 1, '2024-04-10', '03:26:00',   15000.00, 'Pago recurrente #8',   '10.1.2.39', 'APP');


-- ══════════════════════════════════════════════
-- TIPO 3 — TRANSACCIONES EN PAÍSES DISTINTOS EL MISMO DÍA
-- Cliente 51 (ALTO): opera en España a las 09h, luego en Francia a las 14h,
--                    luego en Alemania a las 17h — mismo día
-- ══════════════════════════════════════════════
INSERT INTO transaccion
    (id_cuenta, id_banco, id_tipo_transaccion, id_estado_transaccion, id_moneda, id_pais, fecha, hora, monto, descripcion, ip_origen, canal)
VALUES
(51, 9, 5, 1, 4, 6,  '2024-04-15', '09:10:00', 420.00, 'Compra en Madrid',         '85.110.20.5',  'WEB'),
(52, 11, 5, 1, 4, 8, '2024-04-15', '14:35:00', 380.00, 'Achat Paris boutique',     '77.190.33.12', 'WEB'),
(54, 10, 5, 1, 4, 7, '2024-04-15', '17:55:00', 560.00, 'Kauf Frankfurt online',    '91.200.40.18', 'WEB'),

-- Cliente 50 (ALTO): USA de mañana, Costa Rica de tarde, mismo día
(50, 5, 2, 1, 1, 2,  '2024-04-20', '08:00:00', 3200.00, 'ATM withdrawal New York',  '108.2.66.100', 'ATM'),
(47, 4, 5, 1, 2, 1,  '2024-04-20', '15:45:00', 85000.00, 'Compra San José CR',      '190.10.5.47',  'WEB');


-- ══════════════════════════════════════════════
-- TIPO 4 — TRANSACCIONES DE MADRUGADA (00:00–05:00)
-- ══════════════════════════════════════════════
INSERT INTO transaccion
    (id_cuenta, id_banco, id_tipo_transaccion, id_estado_transaccion, id_moneda, id_pais, fecha, hora, monto, descripcion, ip_origen, canal)
VALUES
-- Cliente 53 (ALTO): retiros y transferencias entre 01h y 04h
(53, 12, 2, 1, 9,  9, '2024-05-02', '01:17:00', 850000.00, 'Retiro madrugada sin justificación', '200.100.50.53', 'ATM'),
(53, 12, 3, 1, 9,  9, '2024-05-02', '02:44:00', 750000.00, 'Transferencia nocturna cuenta externa','200.100.50.53','WEB'),
(53, 12, 2, 1, 9,  9, '2024-05-02', '04:03:00', 620000.00, 'Retiro nocturno #2',                  '200.100.50.54','ATM'),
-- Cliente 55 (ALTO): compras en línea entre medianoche y 3am
(55, 4, 5, 1, 10, 11, '2024-05-10', '00:12:00', 320000.00, 'Compra madrugada tienda en línea #1', '203.5.60.55',  'WEB'),
(55, 4, 5, 1, 10, 11, '2024-05-10', '00:45:00', 295000.00, 'Compra madrugada tienda en línea #2', '203.5.60.55',  'WEB'),
(55, 4, 5, 1, 10, 11, '2024-05-10', '02:30:00', 310000.00, 'Compra madrugada tienda en línea #3', '203.5.60.56',  'WEB'),
-- Cliente 48 (ALTO): transferencia a las 3am
(48, 6, 3, 1, 5,  4, '2024-05-15', '03:22:00', 4200000.00,'Transferencia exterior madrugada',     '201.44.10.48', 'APP');


-- ══════════════════════════════════════════════
-- TIPO 5 — TRANSACCIONES FALLIDAS SEGUIDAS DE APROBADAS
-- Cliente 54 (ALTO): 4 rechazadas → 1 aprobada (intento de acceso forzado)
-- ══════════════════════════════════════════════
INSERT INTO transaccion
    (id_cuenta, id_banco, id_tipo_transaccion, id_estado_transaccion, id_moneda, id_pais, fecha, hora, monto, descripcion, ip_origen, canal)
VALUES
(54, 10, 2, 2, 4, 7, '2024-06-01', '22:01:00', 15000.00, 'Retiro fallido intento 1',  '91.200.99.10', 'ATM'),
(54, 10, 2, 2, 4, 7, '2024-06-01', '22:03:00', 15000.00, 'Retiro fallido intento 2',  '91.200.99.10', 'ATM'),
(54, 10, 2, 2, 4, 7, '2024-06-01', '22:05:00', 15000.00, 'Retiro fallido intento 3',  '91.200.99.11', 'ATM'),
(54, 10, 2, 2, 4, 7, '2024-06-01', '22:07:00', 15000.00, 'Retiro fallido intento 4',  '91.200.99.11', 'ATM'),
(54, 10, 2, 1, 4, 7, '2024-06-01', '22:09:00', 15000.00, 'Retiro aprobado finalmente', '91.200.99.12', 'ATM'),

-- Cliente 30 (MEDIO): compra rechazada x3, luego aprobada (tarjeta clonada potencial)
(30, 12, 5, 2, 9, 10, '2024-06-10', '13:10:00', 95000.00, 'Compra rechazada #1 comercio desconocido', '189.200.5.30', 'WEB'),
(30, 12, 5, 2, 9, 10, '2024-06-10', '13:12:00', 95000.00, 'Compra rechazada #2',                      '189.200.5.30', 'WEB'),
(30, 12, 5, 2, 9, 10, '2024-06-10', '13:15:00', 95000.00, 'Compra rechazada #3',                      '189.200.5.31', 'WEB'),
(30, 12, 5, 1, 9, 10, '2024-06-10', '13:18:00', 95000.00, 'Compra aprobada comercio desconocido',     '189.200.5.31', 'WEB');


-- ══════════════════════════════════════════════
-- TIPO 6 — ACTIVIDAD FUERA DEL PERFIL DE RIESGO
-- Clientes BAJO riesgo con comportamiento atípico repentino
-- ══════════════════════════════════════════════
INSERT INTO transaccion
    (id_cuenta, id_banco, id_tipo_transaccion, id_estado_transaccion, id_moneda, id_pais, fecha, hora, monto, descripcion, ip_origen, canal)
VALUES
-- Cliente 5 (BAJO, plazo fijo, historial pasivo): de repente retira todo y transfiere al exterior
(5,  3, 2, 1, 2, 1, '2024-07-01', '10:00:00', 4800000.00, 'Retiro total cuenta plazo fijo', '10.5.5.5',  'SUCURSAL'),
(5,  3, 3, 1, 1, 2, '2024-07-01', '10:30:00',   22000.00, 'Transferencia internacional USA','10.5.5.5',  'WEB'),
-- Cliente 9 (BAJO): recibe depósito masivo sin antecedente
(9,  7, 1, 1, 5, 4, '2024-07-05', '08:00:00', 28000000.00,'Depósito origen desconocido',    '200.9.9.9', 'SUCURSAL'),
-- Cliente 13 (BAJO): compras en el extranjero repentinas
(13, 8, 5, 1, 3, 3, '2024-07-10', '20:00:00',   78000.00, 'Compra exterior no habitual',    '190.13.13.1','WEB'),
(13, 8, 5, 1, 3, 3, '2024-07-10', '20:05:00',   82000.00, 'Compra exterior #2',             '190.13.13.2','WEB'),
(13, 8, 5, 1, 3, 3, '2024-07-10', '20:10:00',   79000.00, 'Compra exterior #3',             '190.13.13.3','WEB'),
-- Cliente 15 (BAJO): movimiento de alto volumen sin historial
(15, 8, 3, 1, 4, 6, '2024-07-15', '09:00:00',  620000.00, 'Transferencia destino Europa sin justificación','172.30.1.15','WEB');


-- ─────────────────────────────────────────────────────────────
-- 11. CASOS DE REVISIÓN (uno por cada transacción sospechosa)
-- regla_fraude: 1=MONTO_INUSUAL, 2=ALTA_FRECUENCIA, 3=MULTI_PAIS,
--               4=MADRUGADA, 5=FALLO_SEGUIDO, 6=FUERA_PERFIL
-- Las IDs de transacción dependen del orden de inserción.
-- Se usan subconsultas para evitar hardcodear IDs frágiles.
-- ─────────────────────────────────────────────────────────────

-- MONTO_INUSUAL: depósito masivo cliente 47 (monto 22.5M)
INSERT INTO caso_revision (id_transaccion, id_regla_fraude, fecha_apertura, estado, resolucion, analista)
SELECT id, 1, '2024-03-12 12:05:00', 'ABIERTO', 'Pendiente de análisis.', 'SISTEMA'
FROM transaccion WHERE descripcion = 'Depósito recibido de tercero' AND id_cuenta = 47;

-- MONTO_INUSUAL: retiro inmediato masivo cliente 47
INSERT INTO caso_revision (id_transaccion, id_regla_fraude, fecha_apertura, estado, resolucion, analista)
SELECT id, 1, '2024-03-12 12:10:00', 'ABIERTO', 'Pendiente de análisis.', 'SISTEMA'
FROM transaccion WHERE descripcion = 'Retiro inmediato tras depósito' AND id_cuenta = 47;

-- MONTO_INUSUAL: transferencia masiva cliente 56
INSERT INTO caso_revision (id_transaccion, id_regla_fraude, fecha_apertura, estado, resolucion, analista)
SELECT id, 1, '2024-03-15 09:30:00', 'ESCALADO', 'Requiere autorización del oficial de cumplimiento.', 'Ana Piedra'
FROM transaccion WHERE descripcion = 'Transferencia internacional salida' AND id_cuenta = 56;

-- ALTA_FRECUENCIA: ráfaga de 12 compras cliente 49 (tomamos la primera de la serie)
INSERT INTO caso_revision (id_transaccion, id_regla_fraude, fecha_apertura, estado, resolucion, analista)
SELECT id, 2, '2024-03-20 02:40:00', 'ABIERTO', 'Pendiente de análisis.', 'SISTEMA'
FROM transaccion WHERE descripcion = 'Compra en línea #1' AND id_cuenta = 49;

-- ALTA_FRECUENCIA: ráfaga cliente 36 (primera de la serie)
INSERT INTO caso_revision (id_transaccion, id_regla_fraude, fecha_apertura, estado, resolucion, analista)
SELECT id, 2, '2024-04-10 03:30:00', 'CERRADO', 'Cliente verificó operaciones por teléfono. Caso cerrado.', 'Luis Mora'
FROM transaccion WHERE descripcion = 'Pago recurrente #1' AND id_cuenta = 36;

-- MULTI_PAIS_DIA: Madrid→París→Frankfurt cliente 51 (tomamos la de España)
INSERT INTO caso_revision (id_transaccion, id_regla_fraude, fecha_apertura, estado, resolucion, analista)
SELECT id, 3, '2024-04-15 18:30:00', 'ESCALADO', 'Tres países en un día. Posible cuenta comprometida.', 'María Soto'
FROM transaccion WHERE descripcion = 'Compra en Madrid' AND id_cuenta = 51;

-- MULTI_PAIS_DIA: USA→CR cliente 50
INSERT INTO caso_revision (id_transaccion, id_regla_fraude, fecha_apertura, estado, resolucion, analista)
SELECT id, 3, '2024-04-20 16:00:00', 'ABIERTO', 'Pendiente de análisis.', 'SISTEMA'
FROM transaccion WHERE descripcion = 'ATM withdrawal New York' AND id_cuenta = 50;

-- HORARIO_MADRUGADA: retiro 01:17 cliente 53
INSERT INTO caso_revision (id_transaccion, id_regla_fraude, fecha_apertura, estado, resolucion, analista)
SELECT id, 4, '2024-05-02 04:30:00', 'ABIERTO', 'Pendiente de análisis.', 'SISTEMA'
FROM transaccion WHERE descripcion = 'Retiro madrugada sin justificación' AND id_cuenta = 53;

-- HORARIO_MADRUGADA: compras madrugada cliente 55
INSERT INTO caso_revision (id_transaccion, id_regla_fraude, fecha_apertura, estado, resolucion, analista)
SELECT id, 4, '2024-05-10 03:00:00', 'ABIERTO', 'Pendiente de análisis.', 'SISTEMA'
FROM transaccion WHERE descripcion = 'Compra madrugada tienda en línea #1' AND id_cuenta = 55;

-- HORARIO_MADRUGADA: transferencia 03:22 cliente 48
INSERT INTO caso_revision (id_transaccion, id_regla_fraude, fecha_apertura, estado, resolucion, analista)
SELECT id, 4, '2024-05-15 04:00:00', 'ESCALADO', 'Transferencia exterior de alto monto en horario nocturno.', 'Pedro Rojas'
FROM transaccion WHERE descripcion = 'Transferencia exterior madrugada' AND id_cuenta = 48;

-- FALLO_SEGUIDO: retiro aprobado tras 4 fallos, cliente 54
INSERT INTO caso_revision (id_transaccion, id_regla_fraude, fecha_apertura, estado, resolucion, analista)
SELECT id, 5, '2024-06-01 22:15:00', 'CERRADO', 'Cliente informó pérdida de PIN. Caso cerrado con cambio de clave.', 'Andrea Vega'
FROM transaccion WHERE descripcion = 'Retiro aprobado finalmente' AND id_cuenta = 54;

-- FALLO_SEGUIDO: compra aprobada tras 3 fallos, cliente 30
INSERT INTO caso_revision (id_transaccion, id_regla_fraude, fecha_apertura, estado, resolucion, analista)
SELECT id, 5, '2024-06-10 13:25:00', 'ESCALADO', 'Posible clonación de tarjeta. Tarjeta bloqueada preventivamente.', 'Carlos Nuñez'
FROM transaccion WHERE descripcion = 'Compra aprobada comercio desconocido' AND id_cuenta = 30;

-- ACTIVIDAD_FUERA_PERFIL: retiro total cliente 5 (BAJO riesgo)
INSERT INTO caso_revision (id_transaccion, id_regla_fraude, fecha_apertura, estado, resolucion, analista)
SELECT id, 6, '2024-07-01 11:00:00', 'ABIERTO', 'Pendiente de análisis.', 'SISTEMA'
FROM transaccion WHERE descripcion = 'Retiro total cuenta plazo fijo' AND id_cuenta = 5;

-- ACTIVIDAD_FUERA_PERFIL: depósito masivo cliente 9 (BAJO riesgo)
INSERT INTO caso_revision (id_transaccion, id_regla_fraude, fecha_apertura, estado, resolucion, analista)
SELECT id, 6, '2024-07-05 09:00:00', 'ESCALADO', 'Depósito inusual en cliente de bajo riesgo sin antecedentes.', 'Carmen López'
FROM transaccion WHERE descripcion = 'Depósito origen desconocido' AND id_cuenta = 9;

-- ACTIVIDAD_FUERA_PERFIL: transferencia a Europa cliente 15 (BAJO riesgo)
INSERT INTO caso_revision (id_transaccion, id_regla_fraude, fecha_apertura, estado, resolucion, analista)
SELECT id, 6, '2024-07-15 10:00:00', 'ABIERTO', 'Pendiente de análisis.', 'SISTEMA'
FROM transaccion WHERE descripcion = 'Transferencia destino Europa sin justificación' AND id_cuenta = 15;


-- =============================================================
-- FIN DEL SCRIPT DE DATOS SEMILLA
-- =============================================================