-- File: database/migration_users.sql
-- Create the table for usuarios with Roles

CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    rol ENUM('admin', 'cajero') NOT NULL DEFAULT 'cajero',
    fecha_creacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_usuarios_email (email),
    INDEX idx_usuarios_rol (rol)
);

-- Admin inicial:
-- email: admin@puntofacil.com
-- password: admin123
INSERT IGNORE INTO usuarios (nombre, email, password, rol)
VALUES (
    'Administrador',
    'admin@puntofacil.com',
    '$2b$12$1dYxC448JsqUKqm/e/Cv1O2einJUYF9qspotJ6Pq4HhOpDi9Nacru',
    'admin'
);
