import bcrypt
import pymysql

try:
    hashed = bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode('utf-8')
    
    connection = pymysql.connect(host='localhost', user='root', password='', database='puntofacil_pos')
    with connection.cursor() as cursor:
        sql = "UPDATE usuarios SET password=%s WHERE email=%s"
        cursor.execute(sql, (hashed, 'admin@puntofacil.com'))
    connection.commit()
    connection.close()
    
    print("Admin hash updated successfully.")
except Exception as e:
    print(f"Error: {e}")
