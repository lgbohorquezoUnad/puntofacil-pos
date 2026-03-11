ALTER TABLE productos
ADD COLUMN IF NOT EXISTS costo_compra DECIMAL(10,2) NOT NULL DEFAULT 0 AFTER precio_venta;

CREATE TABLE IF NOT EXISTS proveedores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL,
    nit VARCHAR(40) NULL,
    telefono VARCHAR(40) NULL,
    email VARCHAR(120) NULL,
    contacto VARCHAR(120) NULL,
    activo TINYINT(1) NOT NULL DEFAULT 1,
    creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_proveedores_nombre (nombre)
);

CREATE TABLE IF NOT EXISTS ordenes_compra (
    id INT AUTO_INCREMENT PRIMARY KEY,
    proveedor_id INT NOT NULL,
    usuario_id INT NULL,
    estado ENUM('borrador','emitida','parcial','recibida','cancelada') NOT NULL DEFAULT 'emitida',
    total_estimado DECIMAL(12,2) NOT NULL DEFAULT 0,
    notas VARCHAR(255) NULL,
    fecha_emision DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_recepcion DATETIME NULL,
    FOREIGN KEY (proveedor_id) REFERENCES proveedores(id),
    INDEX idx_oc_estado (estado),
    INDEX idx_oc_fecha (fecha_emision)
);

CREATE TABLE IF NOT EXISTS orden_compra_detalle (
    id INT AUTO_INCREMENT PRIMARY KEY,
    orden_compra_id INT NOT NULL,
    producto_id INT NOT NULL,
    cantidad_pedida INT NOT NULL,
    cantidad_recibida INT NOT NULL DEFAULT 0,
    costo_unitario DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(12,2) NOT NULL,
    FOREIGN KEY (orden_compra_id) REFERENCES ordenes_compra(id),
    FOREIGN KEY (producto_id) REFERENCES productos(id),
    INDEX idx_ocd_orden (orden_compra_id),
    INDEX idx_ocd_producto (producto_id)
);

CREATE TABLE IF NOT EXISTS producto_lotes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    producto_id INT NOT NULL,
    numero_lote VARCHAR(80) NOT NULL,
    fecha_vencimiento DATE NULL,
    cantidad_actual INT NOT NULL DEFAULT 0,
    costo_unitario DECIMAL(10,2) NOT NULL DEFAULT 0,
    creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (producto_id) REFERENCES productos(id),
    UNIQUE KEY uk_lote_producto (producto_id, numero_lote),
    INDEX idx_lotes_vencimiento (fecha_vencimiento)
);

CREATE TABLE IF NOT EXISTS inventario_ubicaciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    tipo ENUM('sucursal','bodega') NOT NULL DEFAULT 'sucursal',
    activo TINYINT(1) NOT NULL DEFAULT 1,
    creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_ubicacion_nombre (nombre)
);

INSERT IGNORE INTO inventario_ubicaciones (id, nombre, tipo) VALUES
(1, 'Sucursal principal', 'sucursal'),
(2, 'Bodega central', 'bodega');

CREATE TABLE IF NOT EXISTS transferencias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    origen_ubicacion_id INT NOT NULL,
    destino_ubicacion_id INT NOT NULL,
    usuario_id INT NULL,
    estado ENUM('pendiente','en_transito','completada','cancelada') NOT NULL DEFAULT 'completada',
    notas VARCHAR(255) NULL,
    fecha_creacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_completada DATETIME NULL,
    FOREIGN KEY (origen_ubicacion_id) REFERENCES inventario_ubicaciones(id),
    FOREIGN KEY (destino_ubicacion_id) REFERENCES inventario_ubicaciones(id),
    INDEX idx_transferencias_estado (estado),
    INDEX idx_transferencias_fecha (fecha_creacion)
);

CREATE TABLE IF NOT EXISTS transferencias_detalle (
    id INT AUTO_INCREMENT PRIMARY KEY,
    transferencia_id INT NOT NULL,
    producto_id INT NOT NULL,
    cantidad INT NOT NULL,
    FOREIGN KEY (transferencia_id) REFERENCES transferencias(id),
    FOREIGN KEY (producto_id) REFERENCES productos(id)
);

CREATE TABLE IF NOT EXISTS conteos_inventario (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NULL,
    estado ENUM('abierto','cerrado') NOT NULL DEFAULT 'abierto',
    notas VARCHAR(255) NULL,
    fecha_inicio DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_cierre DATETIME NULL,
    INDEX idx_conteos_estado (estado)
);

CREATE TABLE IF NOT EXISTS conteos_detalle (
    id INT AUTO_INCREMENT PRIMARY KEY,
    conteo_id INT NOT NULL,
    producto_id INT NOT NULL,
    stock_sistema INT NOT NULL,
    stock_contado INT NULL,
    diferencia INT NULL,
    FOREIGN KEY (conteo_id) REFERENCES conteos_inventario(id),
    FOREIGN KEY (producto_id) REFERENCES productos(id),
    UNIQUE KEY uk_conteo_producto (conteo_id, producto_id)
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NULL,
    modulo VARCHAR(80) NOT NULL,
    accion VARCHAR(120) NOT NULL,
    entidad VARCHAR(120) NULL,
    entidad_id INT NULL,
    detalles JSON NULL,
    creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_audit_modulo (modulo),
    INDEX idx_audit_fecha (creado_en)
);
