import json
from decimal import Decimal


def log_audit(
    mysql,
    user_id,
    modulo,
    accion,
    entidad=None,
    entidad_id=None,
    detalles=None,
    cursor=None,
):
    owns_cursor = cursor is None
    local_cursor = cursor or mysql.connection.cursor()

    local_cursor.execute(
        """
        INSERT INTO audit_logs (usuario_id, modulo, accion, entidad, entidad_id, detalles)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (
            user_id,
            modulo,
            accion,
            entidad,
            entidad_id,
            json.dumps(detalles or {}, ensure_ascii=False),
        ),
    )

    if owns_cursor:
        mysql.connection.commit()
        local_cursor.close()


def get_restock_suggestions(mysql, days=30, coverage_days=14, limit=100):
    cursor = mysql.connection.cursor()
    cursor.execute(
        """
        SELECT p.id,
               p.nombre,
               p.stock,
               p.stock_minimo,
               p.costo_compra,
               p.precio_venta,
               COALESCE(SUM(CASE WHEN v.fecha >= DATE_SUB(NOW(), INTERVAL %s DAY) THEN dv.cantidad ELSE 0 END), 0) AS sold_units
        FROM productos p
        LEFT JOIN detalle_venta dv ON dv.producto_id = p.id
        LEFT JOIN ventas v ON v.id = dv.venta_id
        GROUP BY p.id, p.nombre, p.stock, p.stock_minimo, p.costo_compra, p.precio_venta
        ORDER BY sold_units DESC, p.nombre ASC
        LIMIT %s
        """,
        (days, limit),
    )
    rows = cursor.fetchall()
    cursor.close()

    suggestions = []
    coverage_days = max(1, int(coverage_days))
    days = max(1, int(days))

    for row in rows:
        sold_units = int(row[6] or 0)
        avg_daily = sold_units / days
        recommended_stock = int(round(avg_daily * coverage_days))
        min_target = max(recommended_stock, int(row[3] or 0))
        current_stock = int(row[2] or 0)
        reorder_qty = max(0, min_target - current_stock)

        if reorder_qty <= 0:
            continue

        suggestions.append(
            {
                "product_id": row[0],
                "nombre": row[1],
                "current_stock": current_stock,
                "stock_minimo": int(row[3] or 0),
                "sold_units_period": sold_units,
                "avg_daily_sales": round(avg_daily, 2),
                "recommended_stock": min_target,
                "reorder_qty": reorder_qty,
                "estimated_cost": float(Decimal(str(row[4] or 0)) * reorder_qty),
                "estimated_revenue": float(Decimal(str(row[5] or 0)) * reorder_qty),
            }
        )

    return {"days": days, "coverage_days": coverage_days, "suggestions": suggestions}


def list_expiring_batches(mysql, days=30, include_expired=True, limit=200):
    cursor = mysql.connection.cursor()

    if include_expired:
        cursor.execute(
            """
            SELECT b.id,
                   b.producto_id,
                   p.nombre,
                   b.numero_lote,
                   b.fecha_vencimiento,
                   b.cantidad_actual,
                   b.costo_unitario,
                   DATEDIFF(b.fecha_vencimiento, CURDATE()) AS days_to_expire
            FROM producto_lotes b
            INNER JOIN productos p ON p.id = b.producto_id
            WHERE b.cantidad_actual > 0
              AND b.fecha_vencimiento IS NOT NULL
              AND b.fecha_vencimiento <= DATE_ADD(CURDATE(), INTERVAL %s DAY)
            ORDER BY b.fecha_vencimiento ASC
            LIMIT %s
            """,
            (days, limit),
        )
    else:
        cursor.execute(
            """
            SELECT b.id,
                   b.producto_id,
                   p.nombre,
                   b.numero_lote,
                   b.fecha_vencimiento,
                   b.cantidad_actual,
                   b.costo_unitario,
                   DATEDIFF(b.fecha_vencimiento, CURDATE()) AS days_to_expire
            FROM producto_lotes b
            INNER JOIN productos p ON p.id = b.producto_id
            WHERE b.cantidad_actual > 0
              AND b.fecha_vencimiento BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL %s DAY)
            ORDER BY b.fecha_vencimiento ASC
            LIMIT %s
            """,
            (days, limit),
        )

    rows = cursor.fetchall()
    cursor.close()

    return [
        {
            "batch_id": row[0],
            "product_id": row[1],
            "product_name": row[2],
            "batch_number": row[3],
            "expires_at": row[4].strftime("%Y-%m-%d") if row[4] else None,
            "quantity": int(row[5]),
            "unit_cost": float(row[6]),
            "days_to_expire": int(row[7] if row[7] is not None else 9999),
            "status": "expired" if row[7] is not None and row[7] < 0 else "upcoming",
        }
        for row in rows
    ]


def create_purchase_order(mysql, user_id, supplier_id, items, notes=None):
    if not items:
        raise ValueError("Debes enviar al menos un item para la orden de compra")

    connection = mysql.connection
    cursor = connection.cursor()

    try:
        cursor.execute("START TRANSACTION")

        cursor.execute("SELECT id, nombre FROM proveedores WHERE id = %s AND activo = 1", (supplier_id,))
        supplier = cursor.fetchone()
        if supplier is None:
            raise ValueError("Proveedor no encontrado o inactivo")

        total = Decimal("0")
        normalized_items = []

        for item in items:
            try:
                product_id = int(item.get("product_id"))
                quantity = int(item.get("quantity"))
                unit_cost = Decimal(str(item.get("unit_cost")))
            except (TypeError, ValueError):
                raise ValueError("Item invalido en la orden de compra")

            if quantity <= 0 or unit_cost < 0:
                raise ValueError("Cantidad y costo unitario deben ser validos")

            cursor.execute("SELECT id, nombre FROM productos WHERE id = %s", (product_id,))
            product = cursor.fetchone()
            if product is None:
                raise ValueError(f"Producto no encontrado: {product_id}")

            subtotal = unit_cost * quantity
            total += subtotal

            normalized_items.append(
                {
                    "product_id": product_id,
                    "product_name": product[1],
                    "quantity": quantity,
                    "unit_cost": unit_cost,
                    "subtotal": subtotal,
                }
            )

        cursor.execute(
            """
            INSERT INTO ordenes_compra (proveedor_id, usuario_id, estado, total_estimado, notas)
            VALUES (%s, %s, 'emitida', %s, %s)
            """,
            (supplier_id, user_id, float(total), notes),
        )
        order_id = cursor.lastrowid

        for item in normalized_items:
            cursor.execute(
                """
                INSERT INTO orden_compra_detalle
                (orden_compra_id, producto_id, cantidad_pedida, costo_unitario, subtotal)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (order_id, item["product_id"], item["quantity"], float(item["unit_cost"]), float(item["subtotal"])),
            )

        log_audit(
            mysql,
            user_id=user_id,
            modulo="compras",
            accion="crear_orden_compra",
            entidad="orden_compra",
            entidad_id=order_id,
            detalles={"supplier_id": supplier_id, "items": len(normalized_items), "total": float(total)},
            cursor=cursor,
        )

        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()

    return {
        "order_id": order_id,
        "supplier_id": supplier_id,
        "supplier_name": supplier[1],
        "status": "emitida",
        "total_estimated": float(total),
        "items": [
            {
                "product_id": item["product_id"],
                "product_name": item["product_name"],
                "quantity": item["quantity"],
                "unit_cost": float(item["unit_cost"]),
                "subtotal": float(item["subtotal"]),
            }
            for item in normalized_items
        ],
    }


def receive_purchase_order(mysql, user_id, order_id, receipts, batch_expirations=None):
    if not receipts:
        raise ValueError("Debes enviar productos recibidos")

    connection = mysql.connection
    cursor = connection.cursor()

    try:
        cursor.execute("START TRANSACTION")

        cursor.execute(
            "SELECT id, estado FROM ordenes_compra WHERE id = %s FOR UPDATE",
            (order_id,),
        )
        order = cursor.fetchone()
        if order is None:
            raise ValueError("Orden de compra no encontrada")

        if order[1] in ("cancelada", "recibida"):
            raise ValueError("La orden no admite más recepciones")

        received_items = 0

        for receipt in receipts:
            try:
                product_id = int(receipt.get("product_id"))
                qty_received = int(receipt.get("quantity"))
            except (TypeError, ValueError):
                raise ValueError("Item recibido invalido")

            if qty_received <= 0:
                raise ValueError("La cantidad recibida debe ser mayor a cero")

            cursor.execute(
                """
                SELECT id, cantidad_pedida, cantidad_recibida, costo_unitario
                FROM orden_compra_detalle
                WHERE orden_compra_id = %s AND producto_id = %s
                FOR UPDATE
                """,
                (order_id, product_id),
            )
            detail = cursor.fetchone()
            if detail is None:
                raise ValueError(f"Producto {product_id} no pertenece a la orden")

            remaining = int(detail[1]) - int(detail[2])
            if qty_received > remaining:
                raise ValueError(f"Cantidad recibida supera pendiente para producto {product_id}")

            new_received = int(detail[2]) + qty_received
            cursor.execute(
                "UPDATE orden_compra_detalle SET cantidad_recibida = %s WHERE id = %s",
                (new_received, detail[0]),
            )

            cursor.execute(
                "SELECT stock, costo_compra FROM productos WHERE id = %s FOR UPDATE",
                (product_id,),
            )
            product = cursor.fetchone()
            if product is None:
                raise ValueError(f"Producto no encontrado: {product_id}")

            current_stock = int(product[0])
            current_cost = Decimal(str(product[1] or 0))
            received_cost = Decimal(str(detail[3] or 0))
            total_stock = current_stock + qty_received

            if total_stock > 0:
                weighted_cost = ((current_cost * current_stock) + (received_cost * qty_received)) / total_stock
            else:
                weighted_cost = received_cost

            cursor.execute(
                "UPDATE productos SET stock = stock + %s, costo_compra = %s WHERE id = %s",
                (qty_received, float(weighted_cost), product_id),
            )

            expiration = None
            if batch_expirations and str(product_id) in batch_expirations:
                expiration = batch_expirations.get(str(product_id))
            elif batch_expirations and product_id in batch_expirations:
                expiration = batch_expirations.get(product_id)

            batch_number = f"OC-{order_id}-P-{product_id}-{new_received}"
            cursor.execute(
                """
                INSERT INTO producto_lotes (producto_id, numero_lote, fecha_vencimiento, cantidad_actual, costo_unitario)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    cantidad_actual = cantidad_actual + VALUES(cantidad_actual),
                    costo_unitario = VALUES(costo_unitario),
                    fecha_vencimiento = COALESCE(VALUES(fecha_vencimiento), fecha_vencimiento)
                """,
                (product_id, batch_number, expiration, qty_received, float(received_cost)),
            )

            cursor.execute(
                """
                INSERT INTO inventory_movements
                (producto_id, usuario_id, tipo_movimiento, cantidad, stock_antes, stock_despues, motivo)
                VALUES (%s, %s, 'add', %s, %s, %s, %s)
                """,
                (
                    product_id,
                    user_id,
                    qty_received,
                    current_stock,
                    current_stock + qty_received,
                    f"Recepción orden compra #{order_id}",
                ),
            )

            received_items += 1

        cursor.execute(
            """
            SELECT COUNT(*), SUM(CASE WHEN cantidad_recibida >= cantidad_pedida THEN 1 ELSE 0 END)
            FROM orden_compra_detalle
            WHERE orden_compra_id = %s
            """,
            (order_id,),
        )
        status_row = cursor.fetchone()
        total_lines = int(status_row[0] or 0)
        completed_lines = int(status_row[1] or 0)

        new_status = "recibida" if total_lines > 0 and completed_lines == total_lines else "parcial"

        cursor.execute(
            """
            UPDATE ordenes_compra
            SET estado = %s,
                fecha_recepcion = CASE WHEN %s = 'recibida' THEN CURRENT_TIMESTAMP ELSE fecha_recepcion END
            WHERE id = %s
            """,
            (new_status, new_status, order_id),
        )

        log_audit(
            mysql,
            user_id=user_id,
            modulo="compras",
            accion="recepcionar_orden_compra",
            entidad="orden_compra",
            entidad_id=order_id,
            detalles={"items_received": received_items, "new_status": new_status},
            cursor=cursor,
        )

        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()

    return {"order_id": order_id, "status": new_status, "items_received": received_items}


def create_inventory_count_session(mysql, user_id, notes=None):
    connection = mysql.connection
    cursor = connection.cursor()

    try:
        cursor.execute("START TRANSACTION")

        cursor.execute(
            "INSERT INTO conteos_inventario (usuario_id, estado, notas) VALUES (%s, 'abierto', %s)",
            (user_id, notes),
        )
        count_id = cursor.lastrowid

        cursor.execute("SELECT id, stock FROM productos")
        products = cursor.fetchall()

        for product in products:
            cursor.execute(
                """
                INSERT INTO conteos_detalle (conteo_id, producto_id, stock_sistema)
                VALUES (%s, %s, %s)
                """,
                (count_id, product[0], int(product[1] or 0)),
            )

        log_audit(
            mysql,
            user_id=user_id,
            modulo="inventario",
            accion="abrir_conteo",
            entidad="conteo_inventario",
            entidad_id=count_id,
            detalles={"products": len(products)},
            cursor=cursor,
        )

        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()

    return {"count_id": count_id, "products": len(products), "status": "abierto"}


def reconcile_inventory_count(mysql, user_id, count_id, counted_items, reason="Ajuste por conteo físico"):
    if not counted_items:
        raise ValueError("Debes enviar items contados")

    connection = mysql.connection
    cursor = connection.cursor()

    try:
        cursor.execute("START TRANSACTION")

        cursor.execute(
            "SELECT id, estado FROM conteos_inventario WHERE id = %s FOR UPDATE",
            (count_id,),
        )
        count_row = cursor.fetchone()
        if count_row is None:
            raise ValueError("Conteo no encontrado")
        if count_row[1] != "abierto":
            raise ValueError("El conteo ya fue cerrado")

        adjustments = 0

        for item in counted_items:
            try:
                product_id = int(item.get("product_id"))
                stock_counted = int(item.get("stock_counted"))
            except (TypeError, ValueError):
                raise ValueError("Item de conteo invalido")

            if stock_counted < 0:
                raise ValueError("El stock contado no puede ser negativo")

            cursor.execute(
                """
                SELECT id, stock_sistema
                FROM conteos_detalle
                WHERE conteo_id = %s AND producto_id = %s
                FOR UPDATE
                """,
                (count_id, product_id),
            )
            detail = cursor.fetchone()
            if detail is None:
                raise ValueError(f"Producto {product_id} no pertenece al conteo")

            system_stock = int(detail[1])
            diff = stock_counted - system_stock

            cursor.execute(
                """
                UPDATE conteos_detalle
                SET stock_contado = %s,
                    diferencia = %s
                WHERE id = %s
                """,
                (stock_counted, diff, detail[0]),
            )

            if diff != 0:
                cursor.execute("SELECT stock FROM productos WHERE id = %s FOR UPDATE", (product_id,))
                product = cursor.fetchone()
                if product is None:
                    raise ValueError(f"Producto no encontrado: {product_id}")

                real_before = int(product[0])
                real_after = stock_counted

                cursor.execute("UPDATE productos SET stock = %s WHERE id = %s", (real_after, product_id))

                movement_type = "set"
                cursor.execute(
                    """
                    INSERT INTO inventory_movements
                    (producto_id, usuario_id, tipo_movimiento, cantidad, stock_antes, stock_despues, motivo)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (product_id, user_id, movement_type, diff, real_before, real_after, reason),
                )

                adjustments += 1

        cursor.execute(
            """
            UPDATE conteos_inventario
            SET estado = 'cerrado',
                fecha_cierre = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (count_id,),
        )

        log_audit(
            mysql,
            user_id=user_id,
            modulo="inventario",
            accion="cerrar_conteo",
            entidad="conteo_inventario",
            entidad_id=count_id,
            detalles={"adjustments": adjustments},
            cursor=cursor,
        )

        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()

    return {"count_id": count_id, "status": "cerrado", "adjustments": adjustments}


def create_transfer(mysql, user_id, origin_location_id, destination_location_id, items, notes=None):
    if not items:
        raise ValueError("Debes enviar al menos un item para transferir")

    if origin_location_id == destination_location_id:
        raise ValueError("Origen y destino no pueden ser iguales")

    connection = mysql.connection
    cursor = connection.cursor()

    try:
        cursor.execute("START TRANSACTION")

        cursor.execute(
            "SELECT id FROM inventario_ubicaciones WHERE id = %s AND activo = 1",
            (origin_location_id,),
        )
        origin = cursor.fetchone()
        cursor.execute(
            "SELECT id FROM inventario_ubicaciones WHERE id = %s AND activo = 1",
            (destination_location_id,),
        )
        destination = cursor.fetchone()

        if origin is None or destination is None:
            raise ValueError("Ubicación origen/destino inválida")

        cursor.execute(
            """
            INSERT INTO transferencias
            (origen_ubicacion_id, destino_ubicacion_id, usuario_id, estado, notas, fecha_completada)
            VALUES (%s, %s, %s, 'completada', %s, CURRENT_TIMESTAMP)
            """,
            (origin_location_id, destination_location_id, user_id, notes),
        )
        transfer_id = cursor.lastrowid

        for item in items:
            try:
                product_id = int(item.get("product_id"))
                quantity = int(item.get("quantity"))
            except (TypeError, ValueError):
                raise ValueError("Item de transferencia inválido")

            if quantity <= 0:
                raise ValueError("La cantidad transferida debe ser mayor a cero")

            cursor.execute(
                "SELECT stock FROM productos WHERE id = %s FOR UPDATE",
                (product_id,),
            )
            product = cursor.fetchone()
            if product is None:
                raise ValueError(f"Producto no encontrado: {product_id}")

            before_stock = int(product[0])
            after_stock = before_stock - quantity
            if after_stock < 0:
                raise ValueError(f"Stock insuficiente para producto {product_id}")

            cursor.execute(
                "UPDATE productos SET stock = %s WHERE id = %s",
                (after_stock, product_id),
            )

            cursor.execute(
                """
                INSERT INTO transferencias_detalle (transferencia_id, producto_id, cantidad)
                VALUES (%s, %s, %s)
                """,
                (transfer_id, product_id, quantity),
            )

            cursor.execute(
                """
                INSERT INTO inventory_movements
                (producto_id, usuario_id, tipo_movimiento, cantidad, stock_antes, stock_despues, motivo)
                VALUES (%s, %s, 'subtract', %s, %s, %s, %s)
                """,
                (
                    product_id,
                    user_id,
                    -quantity,
                    before_stock,
                    after_stock,
                    f"Transferencia #{transfer_id} a ubicación {destination_location_id}",
                ),
            )

        log_audit(
            mysql,
            user_id=user_id,
            modulo="inventario",
            accion="transferencia",
            entidad="transferencia",
            entidad_id=transfer_id,
            detalles={
                "origin": origin_location_id,
                "destination": destination_location_id,
                "items": len(items),
            },
            cursor=cursor,
        )

        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()

    return {
        "transfer_id": transfer_id,
        "origin_location_id": origin_location_id,
        "destination_location_id": destination_location_id,
        "status": "completada",
        "items": len(items),
    }


def get_audit_logs(mysql, module=None, limit=100):
    cursor = mysql.connection.cursor()

    if module:
        cursor.execute(
            """
            SELECT id, usuario_id, modulo, accion, entidad, entidad_id, detalles, creado_en
            FROM audit_logs
            WHERE modulo = %s
            ORDER BY creado_en DESC
            LIMIT %s
            """,
            (module, limit),
        )
    else:
        cursor.execute(
            """
            SELECT id, usuario_id, modulo, accion, entidad, entidad_id, detalles, creado_en
            FROM audit_logs
            ORDER BY creado_en DESC
            LIMIT %s
            """,
            (limit,),
        )

    rows = cursor.fetchall()
    cursor.close()

    result = []
    for row in rows:
        details = row[6]
        if isinstance(details, str):
            try:
                details = json.loads(details)
            except Exception:
                details = {"raw": details}

        result.append(
            {
                "audit_id": row[0],
                "user_id": row[1],
                "module": row[2],
                "action": row[3],
                "entity": row[4],
                "entity_id": row[5],
                "details": details or {},
                "created_at": row[7].strftime("%Y-%m-%d %H:%M:%S") if row[7] else None,
            }
        )

    return result


def get_inventory_financial_dashboard(mysql):
    cursor = mysql.connection.cursor()

    cursor.execute(
        """
        SELECT COALESCE(SUM(stock * costo_compra), 0),
               COALESCE(SUM(stock * precio_venta), 0),
               COUNT(*)
        FROM productos
        """
    )
    inv_row = cursor.fetchone()

    cursor.execute(
        """
        SELECT COALESCE(SUM(dv.subtotal), 0),
               COALESCE(SUM(dv.cantidad * p.costo_compra), 0)
        FROM detalle_venta dv
        INNER JOIN ventas v ON v.id = dv.venta_id
        INNER JOIN productos p ON p.id = dv.producto_id
        WHERE v.fecha >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        """
    )
    month_row = cursor.fetchone()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM productos p
        WHERE p.stock > 0
          AND NOT EXISTS (
              SELECT 1
              FROM detalle_venta dv
              INNER JOIN ventas v ON v.id = dv.venta_id
              WHERE dv.producto_id = p.id
                AND v.fecha >= DATE_SUB(NOW(), INTERVAL 90 DAY)
          )
        """
    )
    dead_stock_row = cursor.fetchone()

    cursor.execute(
        """
        SELECT p.id,
               p.nombre,
               COALESCE(SUM(dv.subtotal), 0) AS revenue_30d
        FROM productos p
        LEFT JOIN detalle_venta dv ON dv.producto_id = p.id
        LEFT JOIN ventas v ON v.id = dv.venta_id
                             AND v.fecha >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        GROUP BY p.id, p.nombre
        ORDER BY revenue_30d DESC, p.nombre ASC
        LIMIT 5
        """
    )
    top_rows = cursor.fetchall()

    cursor.close()

    inventory_cost = float(inv_row[0] or 0)
    inventory_retail = float(inv_row[1] or 0)
    sales_30d = float(month_row[0] or 0)
    cogs_30d = float(month_row[1] or 0)
    gross_margin_30d = sales_30d - cogs_30d

    return {
        "inventory_cost_value": inventory_cost,
        "inventory_retail_value": inventory_retail,
        "inventory_potential_margin": inventory_retail - inventory_cost,
        "sales_30d": sales_30d,
        "cogs_30d": cogs_30d,
        "gross_margin_30d": gross_margin_30d,
        "products_count": int(inv_row[2] or 0),
        "dead_stock_count_90d": int(dead_stock_row[0] or 0),
        "top_revenue_products_30d": [
            {
                "product_id": row[0],
                "nombre": row[1],
                "revenue_30d": float(row[2] or 0),
            }
            for row in top_rows
        ],
    }


def list_suppliers(mysql):
    cursor = mysql.connection.cursor()
    cursor.execute(
        """
        SELECT id, nombre, nit, telefono, email, contacto
        FROM proveedores
        WHERE activo = 1
        ORDER BY nombre ASC
        """
    )
    rows = cursor.fetchall()
    cursor.close()

    return [
        {
            "id": row[0],
            "nombre": row[1],
            "nit": row[2],
            "telefono": row[3],
            "email": row[4],
            "contacto": row[5],
        }
        for row in rows
    ]


def list_locations(mysql):
    cursor = mysql.connection.cursor()
    cursor.execute(
        """
        SELECT id, nombre, tipo
        FROM inventario_ubicaciones
        WHERE activo = 1
        ORDER BY nombre ASC
        """
    )
    rows = cursor.fetchall()
    cursor.close()

    return [{"id": row[0], "nombre": row[1], "tipo": row[2]} for row in rows]


def get_purchase_order(mysql, order_id):
    cursor = mysql.connection.cursor()
    cursor.execute(
        """
        SELECT oc.id,
               oc.proveedor_id,
               p.nombre,
               oc.estado,
               oc.total_estimado,
               oc.notas,
               oc.fecha_emision,
               oc.fecha_recepcion
        FROM ordenes_compra oc
        INNER JOIN proveedores p ON p.id = oc.proveedor_id
        WHERE oc.id = %s
        """,
        (order_id,),
    )
    order = cursor.fetchone()

    if order is None:
        cursor.close()
        return None

    cursor.execute(
        """
        SELECT d.producto_id,
               pr.nombre,
               d.cantidad_pedida,
               d.cantidad_recibida,
               d.costo_unitario,
               d.subtotal
        FROM orden_compra_detalle d
        INNER JOIN productos pr ON pr.id = d.producto_id
        WHERE d.orden_compra_id = %s
        ORDER BY pr.nombre ASC
        """,
        (order_id,),
    )
    items = cursor.fetchall()
    cursor.close()

    return {
        "order_id": order[0],
        "supplier_id": order[1],
        "supplier_name": order[2],
        "status": order[3],
        "total_estimated": float(order[4] or 0),
        "notes": order[5],
        "issued_at": order[6].strftime("%Y-%m-%d %H:%M:%S") if order[6] else None,
        "received_at": order[7].strftime("%Y-%m-%d %H:%M:%S") if order[7] else None,
        "items": [
            {
                "product_id": row[0],
                "product_name": row[1],
                "qty_ordered": int(row[2] or 0),
                "qty_received": int(row[3] or 0),
                "qty_pending": max(0, int(row[2] or 0) - int(row[3] or 0)),
                "unit_cost": float(row[4] or 0),
                "subtotal": float(row[5] or 0),
            }
            for row in items
        ],
    }


def get_inventory_count(mysql, count_id):
    cursor = mysql.connection.cursor()
    cursor.execute(
        """
        SELECT id, estado, notas, fecha_inicio, fecha_cierre
        FROM conteos_inventario
        WHERE id = %s
        """,
        (count_id,),
    )
    count_row = cursor.fetchone()

    if count_row is None:
        cursor.close()
        return None

    cursor.execute(
        """
        SELECT d.producto_id,
               p.nombre,
               d.stock_sistema,
               d.stock_contado,
               d.diferencia
        FROM conteos_detalle d
        INNER JOIN productos p ON p.id = d.producto_id
        WHERE d.conteo_id = %s
        ORDER BY p.nombre ASC
        """,
        (count_id,),
    )
    items = cursor.fetchall()
    cursor.close()

    return {
        "count_id": count_row[0],
        "status": count_row[1],
        "notes": count_row[2],
        "started_at": count_row[3].strftime("%Y-%m-%d %H:%M:%S") if count_row[3] else None,
        "closed_at": count_row[4].strftime("%Y-%m-%d %H:%M:%S") if count_row[4] else None,
        "items": [
            {
                "product_id": row[0],
                "product_name": row[1],
                "system_stock": int(row[2] or 0),
                "counted_stock": None if row[3] is None else int(row[3]),
                "difference": None if row[4] is None else int(row[4]),
            }
            for row in items
        ],
    }
