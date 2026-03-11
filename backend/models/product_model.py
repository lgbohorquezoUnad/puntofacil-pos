def get_products(mysql):
    cursor = mysql.connection.cursor()
    query = """
    SELECT productos.id,
           productos.nombre,
           productos.precio_venta,
           productos.stock,
           productos.stock_minimo,
           categorias.nombre,
           productos.categoria_id,
           productos.codigo_barras
    FROM productos
    LEFT JOIN categorias
    ON productos.categoria_id = categorias.id
    ORDER BY productos.nombre ASC
    """
    cursor.execute(query)
    products = cursor.fetchall()
    cursor.close()
    return products


def get_product_by_id(mysql, product_id):
    cursor = mysql.connection.cursor()
    cursor.execute(
        """
        SELECT productos.id,
               productos.nombre,
               productos.precio_venta,
               productos.stock,
               productos.stock_minimo,
               categorias.nombre,
               productos.categoria_id,
               productos.codigo_barras
        FROM productos
        LEFT JOIN categorias ON productos.categoria_id = categorias.id
        WHERE productos.id = %s
        """,
        (product_id,),
    )
    product = cursor.fetchone()
    cursor.close()
    return product


def get_categories(mysql):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, nombre FROM categorias ORDER BY nombre ASC")
    rows = cursor.fetchall()
    cursor.close()
    return [{"id": row[0], "nombre": row[1]} for row in rows]


def category_exists(mysql, category_id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id FROM categorias WHERE id = %s", (category_id,))
    category = cursor.fetchone()
    cursor.close()
    return category is not None


def create_product(mysql, nombre, codigo_barras, precio, stock, categoria_id, stock_minimo=5):
    if not category_exists(mysql, categoria_id):
        raise ValueError("La categoria seleccionada no existe")

    cursor = mysql.connection.cursor()
    cursor.execute(
        """
        INSERT INTO productos (nombre, codigo_barras, precio_venta, stock, stock_minimo, categoria_id)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (nombre, codigo_barras or None, precio, stock, stock_minimo, categoria_id),
    )
    product_id = cursor.lastrowid
    mysql.connection.commit()
    cursor.close()
    return product_id


def update_product(
    mysql,
    product_id,
    nombre,
    codigo_barras,
    precio,
    stock,
    categoria_id,
    stock_minimo=5,
):
    if not category_exists(mysql, categoria_id):
        raise ValueError("La categoria seleccionada no existe")

    cursor = mysql.connection.cursor()
    cursor.execute(
        """
        UPDATE productos
        SET nombre = %s,
            codigo_barras = %s,
            precio_venta = %s,
            stock = %s,
            stock_minimo = %s,
            categoria_id = %s
        WHERE id = %s
        """,
        (nombre, codigo_barras or None, precio, stock, stock_minimo, categoria_id, product_id),
    )
    updated = cursor.rowcount > 0
    mysql.connection.commit()
    cursor.close()
    return updated


def delete_product(mysql, product_id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM productos WHERE id = %s", (product_id,))
    deleted = cursor.rowcount > 0
    mysql.connection.commit()
    cursor.close()
    return deleted
