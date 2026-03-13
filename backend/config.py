import os


def _detect_local_mysql_port(default='3306'):
    env_port = os.getenv('MYSQL_PORT')
    if env_port:
        return int(env_port)

    candidate_ini = r'C:\xampp\mysql\bin\my.ini'
    if not os.path.exists(candidate_ini):
        return int(default)

    in_mysqld = False
    try:
        with open(candidate_ini, 'r', encoding='utf-8', errors='ignore') as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if line.lower() == '[mysqld]':
                    in_mysqld = True
                    continue
                if in_mysqld and line.startswith('['):
                    break
                if in_mysqld and line.lower().startswith('port='):
                    value = line.split('=', 1)[1].strip()
                    if value.isdigit():
                        return int(value)
    except OSError:
        pass

    return int(default)


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'puntofacil_secret')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'puntofacil_jwt_super_secret')

    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DB = os.getenv('MYSQL_DB', 'puntofacil_pos')
    MYSQL_PORT = _detect_local_mysql_port()
