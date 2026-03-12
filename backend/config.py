import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "puntofacil_secret")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "puntofacil_jwt_super_secret")

    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DB = os.getenv("MYSQL_DB", "puntofacil_pos")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))