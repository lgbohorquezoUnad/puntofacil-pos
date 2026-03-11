from decimal import Decimal


def get_open_cash_register(mysql):
    cursor = mysql.connection.cursor()
    cursor.execute(
        """
        SELECT id, usuario_id, monto_apertura, estado, fecha_apertura, observaciones
        FROM cajas
        WHERE estado = 'abierta'
        ORDER BY fecha_apertura DESC
        LIMIT 1
        """
    )
    row = cursor.fetchone()
    cursor.close()

    if row is None:
        return None

    return {
        "cash_register_id": row[0],
        "user_id": row[1],
        "opening_amount": float(row[2]),
        "status": row[3],
        "opened_at": row[4].strftime("%Y-%m-%d %H:%M:%S") if row[4] else None,
        "notes": row[5],
    }


def open_cash_register(mysql, opening_amount, user_id=None, notes=None):
    if opening_amount < 0:
        raise ValueError("El monto de apertura no puede ser negativo")

    current_cash_register = get_open_cash_register(mysql)
    if current_cash_register is not None:
        raise ValueError("Ya hay una caja abierta")

    cursor = mysql.connection.cursor()
    cursor.execute(
        """
        INSERT INTO cajas (usuario_id, monto_apertura, estado, observaciones)
        VALUES (%s, %s, 'abierta', %s)
        """,
        (user_id, float(opening_amount), notes),
    )
    cash_register_id = cursor.lastrowid
    mysql.connection.commit()
    cursor.close()

    return get_open_cash_register(mysql) | {"cash_register_id": cash_register_id}


def close_cash_register(mysql, closing_amount, notes=None):
    if closing_amount < 0:
        raise ValueError("El monto de cierre no puede ser negativo")

    connection = mysql.connection
    cursor = connection.cursor()

    try:
        cursor.execute("START TRANSACTION")
        cursor.execute(
            """
            SELECT id, monto_apertura
            FROM cajas
            WHERE estado = 'abierta'
            ORDER BY fecha_apertura DESC
            LIMIT 1
            FOR UPDATE
            """
        )
        current_cash_register = cursor.fetchone()

        if current_cash_register is None:
            raise ValueError("No hay una caja abierta para cerrar")

        cash_register_id = current_cash_register[0]
        opening_amount = Decimal(str(current_cash_register[1]))

        cursor.execute(
            """
            SELECT COALESCE(SUM(total), 0)
            FROM ventas
            WHERE caja_id = %s
            """,
            (cash_register_id,),
        )
        sales_total_row = cursor.fetchone()
        sales_total = Decimal(str(sales_total_row[0]))
        expected_amount = opening_amount + sales_total
        difference = Decimal(str(closing_amount)) - expected_amount

        cursor.execute(
            """
            UPDATE cajas
            SET estado = 'cerrada',
                monto_cierre = %s,
                monto_esperado = %s,
                diferencia = %s,
                fecha_cierre = CURRENT_TIMESTAMP,
                observaciones_cierre = %s
            WHERE id = %s
            """,
            (
                float(closing_amount),
                float(expected_amount),
                float(difference),
                notes,
                cash_register_id,
            ),
        )

        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()

    return {
        "cash_register_id": cash_register_id,
        "opening_amount": float(opening_amount),
        "sales_total": float(sales_total),
        "expected_amount": float(expected_amount),
        "closing_amount": float(closing_amount),
        "difference": float(difference),
        "status": "cerrada",
    }
