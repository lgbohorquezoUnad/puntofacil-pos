def get_user_by_email(mysql, email):
    cursor = mysql.connection.cursor()
    query = """
    SELECT id, nombre, email, password, rol, estado
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
           creado_en AS fecha_alta,
           estado
    FROM usuarios
    ORDER BY estado DESC, nombre ASC
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
            "fecha_creacion": user[4],
            "estado": user[5],
        })
    return result


def create_user(mysql, nombre, email, hashed_password, rol, estado="activo"):
    cursor = mysql.connection.cursor()
    query = "INSERT INTO usuarios (nombre, email, password, rol, estado) VALUES (%s, %s, %s, %s, %s)"
    cursor.execute(query, (nombre, email, hashed_password, rol, estado))
    mysql.connection.commit()
    user_id = cursor.lastrowid
    cursor.close()
    return user_id


def update_user(mysql, user_id, nombre, email, rol, estado, hashed_password=None):
    cursor = mysql.connection.cursor()
    if hashed_password:
        query = "UPDATE usuarios SET nombre=%s, email=%s, rol=%s, estado=%s, password=%s WHERE id=%s"
        cursor.execute(query, (nombre, email, rol, estado, hashed_password, user_id))
    else:
        query = "UPDATE usuarios SET nombre=%s, email=%s, rol=%s, estado=%s WHERE id=%s"
        cursor.execute(query, (nombre, email, rol, estado, user_id))
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
