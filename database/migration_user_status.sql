ALTER TABLE usuarios
ADD COLUMN estado ENUM('activo', 'inactivo') NOT NULL DEFAULT 'activo' AFTER rol;

UPDATE usuarios
SET estado = 'activo'
WHERE estado IS NULL;
