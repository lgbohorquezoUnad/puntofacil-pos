from decimal import Decimal


def get_inventory_overview(
    mysql,
    search=None,
    category_id=None,
    stock_status="all",
    sort_by="nombre",
    sort_order="asc",
    limit=500,
):
    allowed_sort = {
        "nombre": "p.nombre",
        "stock": "p.stock",
        "stock_minimo": "p.stock_minimo",
        "precio": "p.precio_venta",
        "categoria": "c.nombre",
        "ventas_30": "units_sold_30d",
        "valor_inventario": "inventory_value",
    }

    order_column = allowed_sort.get(sort_by, "p.nombre")
    order_direction = "DESC" if str(sort_order).lower() == "desc" else "ASC"

    where_clauses = []
    params = []

    if search:
        where_clauses.append("(p.nombre LIKE %s OR p.codigo_barras LIKE %s)")
        wildcard = f"%{search.strip()}%"
        params.extend([wildcard, wildcard])

    if category_id:
        where_clauses.append("p.categoria_id = %s")
        params.append(category_id)

    if stock_status == "out":
        where_clauses.append("p.stock = 0")
    elif stock_status == "low":
        where_clauses.append("p.stock > 0 AND p.stock <= p.stock_minimo")
    elif stock_status == "ok":
        where_clauses.append("p.stock > p.stock_minimo")

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    cursor = mysql.connection.cursor()
    cursor.execute(
        f"""
        SELECT p.id,
               p.nombre,
               p.codigo_barras,
               p.stock,
               p.stock_minimo,
               p.precio_venta,
               c.nombre,
               COALESCE(SUM(CASE WHEN v.fecha >= DATE_SUB(NOW(), INTERVAL 30 DAY) THEN dv.cantidad ELSE 0 END), 0) AS units_sold_30d,
               MAX(v.fecha) AS last_sale_at,
               (p.stock * p.precio_venta) AS inventory_value
        FROM productos p
        LEFT JOIN categorias c ON c.id = p.categoria_id
        LEFT JOIN detalle_venta dv ON dv.producto_id = p.id
        LEFT JOIN ventas v ON v.id = dv.venta_id
        {where_sql}
        GROUP BY p.id, p.nombre, p.codigo_barras, p.stock, p.stock_minimo, p.precio_venta, c.nombre
        ORDER BY {order_column} {order_direction}, p.nombre ASC
        LIMIT %s
        """,
        tuple(params + [limit]),
    )
    rows = cursor.fetchall()
    cursor.close()

    products = []
    total_units = 0
    total_value = Decimal("0")
    low_stock_count = 0
    out_of_stock_count = 0

    for row in rows:
        stock = int(row[3])
        stock_minimo = int(row[4])
        price = Decimal(str(row[5]))
        inventory_value = Decimal(str(row[9] or 0))

        if stock == 0:
            status = "out"
            out_of_stock_count += 1
        elif stock <= stock_minimo:
            status = "low"
            low_stock_count += 1
        else:
            status = "ok"

        total_units += stock
        total_value += inventory_value

        products.append(
            {
                "id": row[0],
                "nombre": row[1],
                "codigo_barras": row[2],
                "stock": stock,
                "stock_minimo": stock_minimo,
                "precio": float(price),
                "categoria": row[6],
                "units_sold_30d": int(row[7] or 0),
                "last_sale_at": row[8].strftime("%Y-%m-%d %H:%M:%S") if row[8] else None,
                "inventory_value": float(inventory_value),
                "stock_status": status,
            }
        )

    summary = {
        "products_count": len(products),
        "total_units": total_units,
        "total_inventory_value": float(total_value),
        "low_stock_count": low_stock_count,
        "out_of_stock_count": out_of_stock_count,
    }

    return {"summary": summary, "products": products}


def adjust_inventory_stock(mysql, product_id, movement_type, quantity, reason, user_id=None):
    movement_type = (movement_type or "").strip().lower()
    valid_types = {"add", "subtract", "set"}

    if movement_type not in valid_types:
        raise ValueError("Tipo de ajuste invalido. Usa add, subtract o set")

    if movement_type == "set":
        if quantity < 0:
            raise ValueError("El stock final no puede ser negativo")
    elif quantity <= 0:
        raise ValueError("La cantidad del ajuste debe ser mayor a cero")

    connection = mysql.connection
    cursor = connection.cursor()

    try:
        cursor.execute("START TRANSACTION")
        cursor.execute(
            """
            SELECT id, nombre, stock, stock_minimo, precio_venta
            FROM productos
            WHERE id = %s
            FOR UPDATE
            """,
            (product_id,),
        )
        product = cursor.fetchone()

        if product is None:
            raise ValueError("Producto no encontrado")

        stock_before = int(product[2])

        if movement_type == "add":
            stock_after = stock_before + quantity
            signed_quantity = quantity
        elif movement_type == "subtract":
            stock_after = stock_before - quantity
            signed_quantity = -quantity
        else:
            stock_after = quantity
            signed_quantity = quantity - stock_before

        if stock_after < 0:
            raise ValueError("El ajuste deja el stock en negativo")

        cursor.execute(
            "UPDATE productos SET stock = %s WHERE id = %s",
            (stock_after, product_id),
        )

        cursor.execute(
            """
            INSERT INTO inventory_movements
            (producto_id, usuario_id, tipo_movimiento, cantidad, stock_antes, stock_despues, motivo)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                product_id,
                user_id,
                movement_type,
                signed_quantity,
                stock_before,
                stock_after,
                reason,
            ),
        )

        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()

    return {
        "product_id": product[0],
        "nombre": product[1],
        "stock_before": stock_before,
        "stock_after": stock_after,
        "stock_minimo": int(product[3]),
        "precio": float(Decimal(str(product[4]))),
        "movement_type": movement_type,
        "quantity": signed_quantity,
        "reason": reason,
    }


def list_inventory_movements(mysql, product_id=None, limit=100):
    cursor = mysql.connection.cursor()

    if product_id:
        cursor.execute(
            """
            SELECT m.id,
                   m.producto_id,
                   p.nombre,
                   m.tipo_movimiento,
                   m.cantidad,
                   m.stock_antes,
                   m.stock_despues,
                   m.motivo,
                   m.fecha
            FROM inventory_movements m
            INNER JOIN productos p ON p.id = m.producto_id
            WHERE m.producto_id = %s
            ORDER BY m.fecha DESC
            LIMIT %s
            """,
            (product_id, limit),
        )
    else:
        cursor.execute(
            """
            SELECT m.id,
                   m.producto_id,
                   p.nombre,
                   m.tipo_movimiento,
                   m.cantidad,
                   m.stock_antes,
                   m.stock_despues,
                   m.motivo,
                   m.fecha
            FROM inventory_movements m
            INNER JOIN productos p ON p.id = m.producto_id
            ORDER BY m.fecha DESC
            LIMIT %s
            """,
            (limit,),
        )

    rows = cursor.fetchall()
    cursor.close()

    return [
        {
            "movement_id": row[0],
            "product_id": row[1],
            "product_name": row[2],
            "movement_type": row[3],
            "quantity": int(row[4]),
            "stock_before": int(row[5]),
            "stock_after": int(row[6]),
            "reason": row[7],
            "created_at": row[8].strftime("%Y-%m-%d %H:%M:%S") if row[8] else None,
        }
        for row in rows
    ]
