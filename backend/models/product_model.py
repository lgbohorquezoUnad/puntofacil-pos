from decimal import Decimal


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
           productos.codigo_barras,
           productos.imagen_url
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
               productos.codigo_barras,
               productos.imagen_url
        FROM productos
        LEFT JOIN categorias ON productos.categoria_id = categorias.id
        WHERE productos.id = %s
        """,
        (product_id,),
    )
    product = cursor.fetchone()
    cursor.close()
    return product



def get_product_by_barcode(mysql, barcode):
    if not barcode:
        return None

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
               productos.codigo_barras,
               productos.imagen_url
        FROM productos
        LEFT JOIN categorias ON productos.categoria_id = categorias.id
        WHERE productos.codigo_barras = %s
        LIMIT 1
        """,
        (barcode,),
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



def get_category_by_name(mysql, category_name):
    if not category_name:
        return None

    cursor = mysql.connection.cursor()
    cursor.execute(
        "SELECT id, nombre FROM categorias WHERE LOWER(nombre) = LOWER(%s) LIMIT 1",
        (category_name.strip(),),
    )
    category = cursor.fetchone()
    cursor.close()

    if category is None:
        return None

    return {"id": category[0], "nombre": category[1]}



def create_category(mysql, category_name):
    name = (category_name or "").strip()
    if not name:
        raise ValueError("El nombre de la categoria es obligatorio")

    cursor = mysql.connection.cursor()
    cursor.execute("INSERT INTO categorias (nombre) VALUES (%s)", (name,))
    category_id = cursor.lastrowid
    mysql.connection.commit()
    cursor.close()
    return {"id": category_id, "nombre": name}



def get_or_create_category(mysql, category_name):
    existing = get_category_by_name(mysql, category_name)
    if existing:
        return existing
    return create_category(mysql, category_name)



def create_product(mysql, nombre, codigo_barras, precio, stock, categoria_id, stock_minimo=5, imagen_url=None):
    if not category_exists(mysql, categoria_id):
        raise ValueError("La categoria seleccionada no existe")

    cursor = mysql.connection.cursor()
    cursor.execute(
        """
        INSERT INTO productos (nombre, codigo_barras, precio_venta, stock, stock_minimo, categoria_id, imagen_url)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (nombre, codigo_barras or None, precio, stock, stock_minimo, categoria_id, imagen_url or None),
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
    imagen_url=None,
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
            categoria_id = %s,
            imagen_url = %s
        WHERE id = %s
        """,
        (nombre, codigo_barras or None, precio, stock, stock_minimo, categoria_id, imagen_url or None, product_id),
    )
    updated = cursor.rowcount > 0
    mysql.connection.commit()
    cursor.close()
    return updated



def update_product_image(mysql, product_id, image_url):
    cursor = mysql.connection.cursor()
    cursor.execute(
        "UPDATE productos SET imagen_url = %s WHERE id = %s",
        (image_url or None, product_id),
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
