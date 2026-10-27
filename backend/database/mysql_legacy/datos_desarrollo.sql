-- Datos SOLO para desarrollo (BACKEND.md §5). Solo INSERTs: no modifica la estructura.
-- Generado por scripts/generar_datos_desarrollo.py el 2026-09-27. No editar a mano.
-- Se puede ejecutar varias veces: no duplica registros.
-- Usuario de prueba: demo@kompas.mx / demo1234

INSERT IGNORE INTO categorias (nombre, descripcion) VALUES
  ('Comer', 'Restaurantes, fondas y lugares para comer'),
  ('Café', 'Cafeterías'),
  ('Cultura', 'Museos, galerías y centros culturales'),
  ('Entretenimiento', 'Cines, plazas y lugares de diversión'),
  ('Aire libre', 'Parques y jardines');

INSERT IGNORE INTO transportes (nombre) VALUES
  ('Caminando'),
  ('Transporte público'),
  ('Taxi/App'),
  ('Combinado');

-- Administrador: dueño de los lugares de prueba (su contraseña es aleatoria y nadie la conoce)
INSERT IGNORE INTO usuarios (nombre, primer_apellido, correo, password) VALUES
  ('Administrador', 'Kompás', 'admin@kompas.mx', '$2b$12$Fr7ZKl1/FyGTJJApRtKj.OGS7xCjatX8xsdujQ2sYaArjewPloXLi'),
  ('Demo', 'Kompás', 'demo@kompas.mx', '$2b$12$3gDLCf7RxOZYJiSzv8RFju5d/H4Kd5LknynUaa3TP5mlHTQRUB3sG');

-- Lugares GENÉRICOS de ejemplo (no son negocios reales); Sebas carga los reales
INSERT INTO lugares_de_interes (nombre, latitud, longitud, id_usuario, id_cat)
SELECT 'Cafetería de ejemplo · Centro de Toluca', 19.292, -99.656, u.id_usuario, c.id_categoria
FROM usuarios u JOIN categorias c ON c.nombre = 'Café'
WHERE u.correo = 'admin@kompas.mx'
  AND NOT EXISTS (SELECT 1 FROM lugares_de_interes l WHERE l.nombre = 'Cafetería de ejemplo · Centro de Toluca');

INSERT INTO lugares_de_interes (nombre, latitud, longitud, id_usuario, id_cat)
SELECT 'Restaurante familiar de ejemplo · Toluca', 19.287, -99.64, u.id_usuario, c.id_categoria
FROM usuarios u JOIN categorias c ON c.nombre = 'Comer'
WHERE u.correo = 'admin@kompas.mx'
  AND NOT EXISTS (SELECT 1 FROM lugares_de_interes l WHERE l.nombre = 'Restaurante familiar de ejemplo · Toluca');

INSERT INTO lugares_de_interes (nombre, latitud, longitud, id_usuario, id_cat)
SELECT 'Parque de ejemplo · Toluca', 19.296, -99.662, u.id_usuario, c.id_categoria
FROM usuarios u JOIN categorias c ON c.nombre = 'Aire libre'
WHERE u.correo = 'admin@kompas.mx'
  AND NOT EXISTS (SELECT 1 FROM lugares_de_interes l WHERE l.nombre = 'Parque de ejemplo · Toluca');

INSERT INTO lugares_de_interes (nombre, latitud, longitud, id_usuario, id_cat)
SELECT 'Museo de ejemplo · Toluca', 19.2935, -99.658, u.id_usuario, c.id_categoria
FROM usuarios u JOIN categorias c ON c.nombre = 'Cultura'
WHERE u.correo = 'admin@kompas.mx'
  AND NOT EXISTS (SELECT 1 FROM lugares_de_interes l WHERE l.nombre = 'Museo de ejemplo · Toluca');

INSERT INTO lugares_de_interes (nombre, latitud, longitud, id_usuario, id_cat)
SELECT 'Cine de ejemplo · Toluca oriente', 19.28, -99.61, u.id_usuario, c.id_categoria
FROM usuarios u JOIN categorias c ON c.nombre = 'Entretenimiento'
WHERE u.correo = 'admin@kompas.mx'
  AND NOT EXISTS (SELECT 1 FROM lugares_de_interes l WHERE l.nombre = 'Cine de ejemplo · Toluca oriente');

INSERT INTO lugares_de_interes (nombre, latitud, longitud, id_usuario, id_cat)
SELECT 'Cafetería de ejemplo · Centro de Lerma', 19.285, -99.5115, u.id_usuario, c.id_categoria
FROM usuarios u JOIN categorias c ON c.nombre = 'Café'
WHERE u.correo = 'admin@kompas.mx'
  AND NOT EXISTS (SELECT 1 FROM lugares_de_interes l WHERE l.nombre = 'Cafetería de ejemplo · Centro de Lerma');

INSERT INTO lugares_de_interes (nombre, latitud, longitud, id_usuario, id_cat)
SELECT 'Fonda de ejemplo · San Mateo Atenco', 19.2675, -99.5335, u.id_usuario, c.id_categoria
FROM usuarios u JOIN categorias c ON c.nombre = 'Comer'
WHERE u.correo = 'admin@kompas.mx'
  AND NOT EXISTS (SELECT 1 FROM lugares_de_interes l WHERE l.nombre = 'Fonda de ejemplo · San Mateo Atenco');

INSERT INTO lugares_de_interes (nombre, latitud, longitud, id_usuario, id_cat)
SELECT 'Plaza de ejemplo · Lerma', 19.28, -99.54, u.id_usuario, c.id_categoria
FROM usuarios u JOIN categorias c ON c.nombre = 'Entretenimiento'
WHERE u.correo = 'admin@kompas.mx'
  AND NOT EXISTS (SELECT 1 FROM lugares_de_interes l WHERE l.nombre = 'Plaza de ejemplo · Lerma');

INSERT INTO lugares_de_interes (nombre, latitud, longitud, id_usuario, id_cat)
SELECT 'Jardín de ejemplo · Lerma', 19.2875, -99.514, u.id_usuario, c.id_categoria
FROM usuarios u JOIN categorias c ON c.nombre = 'Aire libre'
WHERE u.correo = 'admin@kompas.mx'
  AND NOT EXISTS (SELECT 1 FROM lugares_de_interes l WHERE l.nombre = 'Jardín de ejemplo · Lerma');

INSERT INTO lugares_de_interes (nombre, latitud, longitud, id_usuario, id_cat)
SELECT 'Galería de ejemplo · Lerma', 19.288, -99.515, u.id_usuario, c.id_categoria
FROM usuarios u JOIN categorias c ON c.nombre = 'Cultura'
WHERE u.correo = 'admin@kompas.mx'
  AND NOT EXISTS (SELECT 1 FROM lugares_de_interes l WHERE l.nombre = 'Galería de ejemplo · Lerma');
