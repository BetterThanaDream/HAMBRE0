-- ============================================================
-- HAMBRE CERO - ODS 2 (Hambre Cero)
-- Momento 2 - Desarrollo Sostenible
-- Esquema de base de datos (Motor: SQLite - Motor permitido
-- por la guia del momento 2)
-- Nota: en SQLite los ENUM se reemplazan por CHECK constraints
-- ============================================================

CREATE TABLE usuarios (
    id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_completo VARCHAR(150) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    rol VARCHAR(20) NOT NULL DEFAULT 'donante' CHECK (rol IN ('donante', 'admin')),
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE organizaciones (
    id_org INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_org VARCHAR(200) NOT NULL,
    ubicacion VARCHAR(255) NOT NULL,
    documento_legal VARCHAR(50) UNIQUE NOT NULL,
    verificada BOOLEAN DEFAULT FALSE
);

CREATE TABLE campanas (
    id_campana INTEGER PRIMARY KEY AUTOINCREMENT,
    id_org INTEGER NOT NULL,
    titulo VARCHAR(200) NOT NULL,
    descripcion TEXT NOT NULL,
    meta_financiera DECIMAL(12,2) NOT NULL,
    monto_recaudado DECIMAL(12,2) DEFAULT 0.00,
    fecha_limite DATE NOT NULL,
    FOREIGN KEY (id_org) REFERENCES organizaciones(id_org) ON DELETE CASCADE
);

CREATE TABLE donaciones (
    id_donacion INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario INTEGER NOT NULL,
    id_campana INTEGER NOT NULL,
    monto DECIMAL(12,2) NOT NULL,
    estado_pago VARCHAR(20) NOT NULL DEFAULT 'pendiente' CHECK (estado_pago IN ('pendiente', 'aprobado', 'rechazado')),
    fecha_donacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
    FOREIGN KEY (id_campana) REFERENCES campanas(id_campana) ON DELETE CASCADE
);
