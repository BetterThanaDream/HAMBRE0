-- ============================================================
-- HAMBRE CERO - ODS 2 (Hambre Cero)
-- Momento 2 - Desarrollo Sostenible
-- Dump con datos de ejemplo para que el docente pueda
-- probar el sistema sin configurar nada
-- ============================================================


-- Organizaciones solidarias registradas
INSERT INTO organizaciones (id_org, nombre_org, ubicacion, documento_legal, verificada) VALUES
(1, 'Fundacion Manos Amiga', 'Medellin, Antioquia', 'DOC-0012345678', TRUE),
(2, 'Red de Comedores Solidarios', 'Cali, Valle del Cauca', 'DOC-0087654321', TRUE);

-- Campañas activas
INSERT INTO campanas (id_campana, id_org, titulo, descripcion, meta_financiera, monto_recaudado, fecha_limite) VALUES
(1, 1, 'Comedor Infantil Escolar', 'Garantizamos 3 comidas diarias para 150 niños en situacion de pobreza extrema durante todo el ano escolar.', 15000000.00, 0.00, '2026-12-15'),
(2, 2, 'Insumos Agricolas Rurales', 'Empoderamos a 40 familias campesinas con semillas y herramientas para asegurar su autosuficiencia alimentaria.', 10000000.00, 0.00, '2027-03-30');

-- Usuarios de ejemplo (password: admin123 / donante123)
INSERT INTO usuarios (id_usuario, nombre_completo, email, password_hash, rol) VALUES
(1, 'Admin HAMBRE0', 'admin@hambre0.com', 'scrypt:32768:8:1$x9YKt4urMWo6qdNU$f65e1541cb13c767c57684a66f4675ebc0a71f0c1a18ea8837056285aa630231fc137f2e939b4eea7aea0e13a324421316355a833dd34c8fe78dbd694855a617', 'admin'),
(2, 'Donante Ejemplo', 'donante@ejemplo.com', 'scrypt:32768:8:1$NMhF4l8Y5gyiaadY$4fb74524fd10ef5f77b9753ae52c304e06474a6e5c36c0d0ed0b5a02b325b3320809023664518ae46c4111d3354677fab57799c6c99b083b20de89b811cf665c', 'donante');

-- Donaciones de ejemplo aprobadas
INSERT INTO donaciones (id_donacion, id_usuario, id_campana, monto, estado_pago, fecha_donacion) VALUES
(1, 2, 1, 500000.00, 'aprobado', '2026-10-01 10:30:00'),
(2, 2, 1, 250000.00, 'aprobado', '2026-10-05 16:45:00'),
(3, 2, 2, 150000.00, 'aprobado', '2026-10-08 09:15:00');
