import os

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_mysqldb import MySQL
from flask_jwt_extended import JWTManager
from config import Config

from routes.auth_routes import init_auth_routes
from routes.cash_register_routes import init_cash_register_routes
from routes.product_routes import init_product_routes
from routes.sale_routes import init_sale_routes
from routes.user_routes import init_user_routes

# Absolute paths to the frontend assets.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_TEMPLATES = os.path.join(BASE_DIR, "frontend", "templates")
FRONTEND_STATIC = os.path.join(BASE_DIR, "frontend", "static")

app = Flask(__name__, static_folder=FRONTEND_STATIC, static_url_path="/static")
app.config.from_object(Config)

frontend_url = os.getenv("FRONTEND_URL", "").strip()
cors_origins = [
    "http://localhost:5000",
    "http://127.0.0.1:5000",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
if frontend_url:
    cors_origins.append(frontend_url)

# The frontend may run on Netlify while the API runs on Render.
CORS(
    app,
    resources={r"/api/*": {"origins": cors_origins + [r"https://.*\.netlify\.app", r"https://.*\.onrender\.com"]}},
)
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
@app.route("/login")
def serve_login():
    return send_from_directory(FRONTEND_TEMPLATES, "login.html")

@app.route("/pos")
def serve_pos():
    return send_from_directory(FRONTEND_TEMPLATES, "pos.html")

@app.route("/admin")
def serve_admin():
    return send_from_directory(FRONTEND_TEMPLATES, "admin.html")

@app.route("/inventory")
def serve_inventory():
    return send_from_directory(FRONTEND_TEMPLATES, "inventory.html")

@app.route("/operativa")
def serve_operativa():
    return send_from_directory(FRONTEND_TEMPLATES, "operativa.html")


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "true").lower() == "true"
    )
