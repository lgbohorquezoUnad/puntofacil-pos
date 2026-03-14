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

CREATE TABLE IF NOT EXISTS ventas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NULL,
    caja_id INT NOT NULL,
    metodo_pago VARCHAR(50) NOT NULL,
    total DECIMAL(10,2) NOT NULL,
    fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_ventas_fecha (fecha),
    INDEX idx_ventas_usuario (usuario_id),
    INDEX idx_ventas_caja (caja_id),
    FOREIGN KEY (caja_id) REFERENCES cajas(id)
);

CREATE TABLE IF NOT EXISTS detalle_venta (
    id INT AUTO_INCREMENT PRIMARY KEY,
    venta_id INT NOT NULL,
    producto_id INT NOT NULL,
    cantidad INT NOT NULL,
    precio_unitario DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (venta_id) REFERENCES ventas(id),
    FOREIGN KEY (producto_id) REFERENCES productos(id)
);

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

