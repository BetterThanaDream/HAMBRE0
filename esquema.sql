
CREATE DATABASE IF NOT EXISTS hambre_cero_db;
USE hambre_cero_db;

CREATE TABLE usuarios (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nombre_completo VARCHAR(150) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    rol ENUM('donante', 'admin') DEFAULT 'donante',
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE organizaciones (
    id_org INT AUTO_INCREMENT PRIMARY KEY,
    nombre_org VARCHAR(200) NOT NULL,
    ubicacion VARCHAR(255) NOT NULL,
    documento_legal VARCHAR(50) UNIQUE NOT NULL,
    verificada BOOLEAN DEFAULT FALSE
);

CREATE TABLE campañas (
    id_campaña INT AUTO_INCREMENT PRIMARY KEY,
    id_org INT NOT NULL,
    titulo VARCHAR(200) NOT NULL,
    descripcion TEXT NOT NULL,
    meta_financiera DECIMAL(12,2) NOT NULL,
    monto_recaudado DECIMAL(12,2) DEFAULT 0.00,
    fecha_limite DATE NOT NULL,
    FOREIGN KEY (id_org) REFERENCES organizaciones(id_org) ON DELETE CASCADE
);

CREATE TABLE donaciones (
    id_donacion INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    id_campana INT NOT NULL,
    monto DECIMAL(12,2) NOT NULL,
    estado_pago ENUM('pendiente', 'aprobado', 'rechazado') DEFAULT 'pendiente',
    fecha_donacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario),
    FOREIGN KEY (id_campana) REFERENCES campanas(id_campana)
);
