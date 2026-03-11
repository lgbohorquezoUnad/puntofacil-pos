ALTER TABLE productos
ADD COLUMN IF NOT EXISTS stock_minimo INT NOT NULL DEFAULT 5 AFTER stock;

CREATE TABLE IF NOT EXISTS inventory_movements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    producto_id INT NOT NULL,
    usuario_id INT NULL,
    tipo_movimiento ENUM('add', 'subtract', 'set') NOT NULL,
    cantidad INT NOT NULL,
    stock_antes INT NOT NULL,
    stock_despues INT NOT NULL,
    motivo VARCHAR(255) NULL,
    fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_inventory_movements_producto (producto_id),
    INDEX idx_inventory_movements_fecha (fecha),
    FOREIGN KEY (producto_id) REFERENCES productos(id)
);
