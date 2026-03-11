def get_user_by_email(mysql, email):
    cursor = mysql.connection.cursor()
    query = """
    SELECT id, nombre, email, password, rol
    FROM usuarios
    WHERE email = %s
    LIMIT 1
    """
    cursor.execute(query, (email,))
    user = cursor.fetchone()
    cursor.close()
    return user


def get_all_users(mysql):
    cursor = mysql.connection.cursor()
    query = """
    SELECT id,
           nombre,
           email,
           rol,
           COALESCE(fecha_creacion, creado_en) AS fecha_alta
    FROM usuarios
    """
    cursor.execute(query)
    users = cursor.fetchall()
    cursor.close()

    result = []
    for user in users:
        result.append({
            "id": user[0],
            "nombre": user[1],
            "email": user[2],
            "rol": user[3],
            "fecha_creacion": user[4]
        })
    return result


def create_user(mysql, nombre, email, hashed_password, rol):
    cursor = mysql.connection.cursor()
    query = "INSERT INTO usuarios (nombre, email, password, rol) VALUES (%s, %s, %s, %s)"
    cursor.execute(query, (nombre, email, hashed_password, rol))
    mysql.connection.commit()
    user_id = cursor.lastrowid
    cursor.close()
    return user_id


def update_user(mysql, user_id, nombre, email, rol):
    cursor = mysql.connection.cursor()
    query = "UPDATE usuarios SET nombre=%s, email=%s, rol=%s WHERE id=%s"
    cursor.execute(query, (nombre, email, rol, user_id))
    mysql.connection.commit()
    cursor.close()
    return True


def delete_user(mysql, user_id):
    cursor = mysql.connection.cursor()
    query = "DELETE FROM usuarios WHERE id=%s"
    cursor.execute(query, (user_id,))
    mysql.connection.commit()
    cursor.close()
    return True
