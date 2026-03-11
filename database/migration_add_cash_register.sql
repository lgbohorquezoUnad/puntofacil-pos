CREATE TABLE IF NOT EXISTS cajas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NULL,
    monto_apertura DECIMAL(10,2) NOT NULL,
    monto_cierre DECIMAL(10,2) NULL,
    monto_esperado DECIMAL(10,2) NULL,
    diferencia DECIMAL(10,2) NULL,
    estado ENUM('abierta', 'cerrada') NOT NULL DEFAULT 'abierta',
    fecha_apertura DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_cierre DATETIME NULL,
    observaciones VARCHAR(255) NULL,
    observaciones_cierre VARCHAR(255) NULL,
    INDEX idx_cajas_estado (estado),
    INDEX idx_cajas_fecha_apertura (fecha_apertura)
);

ALTER TABLE ventas
ADD COLUMN caja_id INT NULL AFTER usuario_id;

ALTER TABLE ventas
ADD INDEX idx_ventas_caja (caja_id);

ALTER TABLE ventas
ADD CONSTRAINT fk_ventas_caja FOREIGN KEY (caja_id) REFERENCES cajas(id);
