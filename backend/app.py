import os

from flask import Flask
from flask_cors import CORS
from flask_mysqldb import MySQL
from flask_jwt_extended import JWTManager
from config import Config

from routes.auth_routes import init_auth_routes
from routes.cash_register_routes import init_cash_register_routes
from routes.product_routes import init_product_routes
from routes.sale_routes import init_sale_routes
from routes.user_routes import init_user_routes

app = Flask(__name__)
app.config.from_object(Config)

frontend_url = os.getenv("FRONTEND_URL", "").strip()
cors_origins = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
if frontend_url:
    cors_origins.append(frontend_url)

CORS(app, resources={r"/api/*": {"origins": cors_origins}})
jwt = JWTManager(app)

mysql = MySQL(app)

auth_routes = init_auth_routes(mysql)
app.register_blueprint(auth_routes)

product_routes = init_product_routes(mysql)
app.register_blueprint(product_routes)

sale_routes = init_sale_routes(mysql)
app.register_blueprint(sale_routes)

cash_register_routes = init_cash_register_routes(mysql)
app.register_blueprint(cash_register_routes)

user_routes = init_user_routes(mysql)
app.register_blueprint(user_routes)


@app.route("/")
def home():
    return {"mensaje": "PuntoFacil POS API"}


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "true").lower() == "true"
    )