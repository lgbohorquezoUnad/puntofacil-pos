from decimal import Decimal


def get_current_cash_register(cursor):
    cursor.execute(
        """
        SELECT id, usuario_id, monto_apertura, estado, fecha_apertura, observaciones
        FROM cajas
        WHERE estado = 'abierta'
        ORDER BY fecha_apertura DESC
        LIMIT 1
        FOR UPDATE
        """
    )
    return cursor.fetchone()


def create_sale(mysql, payment_method, items, user_id=None):
    connection = mysql.connection
    cursor = connection.cursor()

    try:
        cursor.execute("START TRANSACTION")

        cash_register = get_current_cash_register(cursor)

        if cash_register is None:
            raise ValueError("Debes abrir caja antes de registrar ventas")

        product_ids = [item["product_id"] for item in items]
        placeholders = ",".join(["%s"] * len(product_ids))
        cursor.execute(
            f"""
            SELECT id, nombre, precio_venta, stock
            FROM productos
            WHERE id IN ({placeholders})
            FOR UPDATE
            """,
            tuple(product_ids),
        )
        products = cursor.fetchall()

        products_by_id = {
            product[0]: {
                "id": product[0],
                "nombre": product[1],
                "precio": Decimal(str(product[2])),
                "stock": int(product[3]),
            }
            for product in products
        }

        validated_items = []
        total = Decimal("0.00")

        for item in items:
            product_id = item["product_id"]
            qty = item["qty"]
            product = products_by_id.get(product_id)

            if product is None:
                raise ValueError(f"El producto con ID {product_id} no existe")

            if qty <= 0:
                raise ValueError(f"La cantidad para {product['nombre']} debe ser mayor a cero")

            if product["stock"] < qty:
                raise ValueError(
                    f"Stock insuficiente para {product['nombre']}. Disponible: {product['stock']}"
                )

            subtotal = product["precio"] * qty
            total += subtotal

            validated_items.append(
                {
                    "product_id": product_id,
                    "nombre": product["nombre"],
                    "qty": qty,
                    "price": product["precio"],
                    "subtotal": subtotal,
                }
            )

        cash_register_id = cash_register[0]

        cursor.execute(
            """
            INSERT INTO ventas (usuario_id, caja_id, metodo_pago, total)
            VALUES (%s, %s, %s, %s)
            """,
            (user_id, cash_register_id, payment_method, float(total)),
        )
        sale_id = cursor.lastrowid

        for item in validated_items:
            cursor.execute(
                """
                INSERT INTO detalle_venta (venta_id, producto_id, cantidad, precio_unitario, subtotal)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    sale_id,
                    item["product_id"],
                    item["qty"],
                    float(item["price"]),
                    float(item["subtotal"]),
                ),
            )

            cursor.execute(
                """
                UPDATE productos
                SET stock = stock - %s
                WHERE id = %s
                """,
                (item["qty"], item["product_id"]),
            )

        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()

    return {
        "sale_id": sale_id,
        "cash_register_id": cash_register_id,
        "payment_method": payment_method,
        "total": float(total),
        "items": [
            {
                "product_id": item["product_id"],
                "nombre": item["nombre"],
                "qty": item["qty"],
                "price": float(item["price"]),
                "subtotal": float(item["subtotal"]),
            }
            for item in validated_items
        ],
    }


def list_sales(mysql, limit=20):
    cursor = mysql.connection.cursor()
    cursor.execute(
        """
        SELECT ventas.id,
               ventas.fecha,
               ventas.metodo_pago,
               ventas.total,
               ventas.caja_id,
               COALESCE(SUM(detalle_venta.cantidad), 0) AS total_items
        FROM ventas
        LEFT JOIN detalle_venta ON detalle_venta.venta_id = ventas.id
        GROUP BY ventas.id, ventas.fecha, ventas.metodo_pago, ventas.total, ventas.caja_id
        ORDER BY ventas.fecha DESC
        LIMIT %s
        """,
        (limit,),
    )
    rows = cursor.fetchall()
    cursor.close()

    return [
        {
            "sale_id": row[0],
            "fecha": row[1].strftime("%Y-%m-%d %H:%M:%S") if row[1] else None,
            "payment_method": row[2],
            "total": float(row[3]),
            "cash_register_id": row[4],
            "items_count": int(row[5]),
        }
        for row in rows
    ]


def get_daily_summary(mysql):
    cursor = mysql.connection.cursor()

    cursor.execute(
        """
        SELECT COUNT(*), COALESCE(SUM(total), 0)
        FROM ventas
        WHERE DATE(fecha) = CURDATE()
        """
    )
    sales_row = cursor.fetchone()

    cursor.execute(
        """
        SELECT COALESCE(SUM(cantidad), 0)
        FROM detalle_venta
        INNER JOIN ventas ON ventas.id = detalle_venta.venta_id
        WHERE DATE(ventas.fecha) = CURDATE()
        """
    )
    items_row = cursor.fetchone()

    cursor.execute(
        """
        SELECT productos.nombre, SUM(detalle_venta.cantidad) AS total_vendido
        FROM detalle_venta
        INNER JOIN ventas ON ventas.id = detalle_venta.venta_id
        INNER JOIN productos ON productos.id = detalle_venta.producto_id
        WHERE DATE(ventas.fecha) = CURDATE()
        GROUP BY productos.id, productos.nombre
        ORDER BY total_vendido DESC, productos.nombre ASC
        LIMIT 5
        """
    )
    top_rows = cursor.fetchall()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM productos
        WHERE stock <= 5
        """
    )
    low_stock_row = cursor.fetchone()

    cursor.close()

    return {
        "today_sales_count": int(sales_row[0] or 0),
        "today_sales_total": float(sales_row[1] or 0),
        "today_items_sold": int(items_row[0] or 0),
        "low_stock_count": int(low_stock_row[0] or 0),
        "top_products": [
            {"nombre": row[0], "cantidad": int(row[1])}
            for row in top_rows
        ],
    }
