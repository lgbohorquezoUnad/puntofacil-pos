from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from models.product_model import (
    create_product,
    delete_product,
    get_categories,
    get_product_by_id,
    get_products,
    update_product,
)
from models.sale_model import get_daily_summary


def get_current_user_context():
    identity = get_jwt_identity()
    claims = get_jwt() or {}

    if isinstance(identity, dict):
        return {
            "id": identity.get("id"),
            "nombre": identity.get("nombre") or claims.get("nombre"),
            "rol": identity.get("rol") or claims.get("rol"),
        }

    user_id = identity
    try:
        user_id = int(identity)
    except (TypeError, ValueError):
        pass

    return {
        "id": user_id,
        "nombre": claims.get("nombre"),
        "rol": claims.get("rol"),
    }


def serialize_products(products):
    result = []
    for p in products:
        result.append(
            {
                "id": p[0],
                "nombre": p[1],
                "precio": float(p[2]),
                "stock": p[3],
                "stock_minimo": p[4],
                "categoria": p[5],
                "categoria_id": p[6],
                "codigo_barras": p[7],
            }
        )
    return result


@jwt_required()
def list_products(mysql):
    products = get_products(mysql)
    return jsonify(serialize_products(products))


@jwt_required()
def list_categories(mysql):
    return jsonify(get_categories(mysql))


@jwt_required()
def create_product_controller(mysql):
    current_user = get_current_user_context()
    if current_user.get("rol") != "admin":
        return jsonify({"error": "No autorizado"}), 403

    data = request.json or {}

    try:
        category_id = int(data.get("categoria_id"))
        stock = int(data.get("stock"))
        stock_minimo = int(data.get("stock_minimo", 5))
        price = float(data.get("precio"))
    except (TypeError, ValueError):
        return jsonify({"error": "Categoria, stock, stock minimo o precio invalidos"}), 400

    if stock < 0 or stock_minimo < 0 or price < 0:
        return jsonify({"error": "Stock, stock minimo y precio no pueden ser negativos"}), 400

    nombre = (data.get("nombre") or "").strip()
    codigo_barras = (data.get("codigo_barras") or "").strip()

    if not nombre:
        return jsonify({"error": "El nombre del producto es obligatorio"}), 400

    try:
        product_id = create_product(
            mysql,
            nombre,
            codigo_barras,
            price,
            stock,
            category_id,
            stock_minimo,
        )
        product = get_product_by_id(mysql, product_id)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except Exception:
        return jsonify({"error": "No fue posible crear el producto"}), 500

    return jsonify({"message": "Producto creado", "product": serialize_products([product])[0]}), 201


@jwt_required()
def update_product_controller(mysql, product_id):
    current_user = get_current_user_context()
    if current_user.get("rol") != "admin":
        return jsonify({"error": "No autorizado"}), 403

    data = request.json or {}

    try:
        category_id = int(data.get("categoria_id"))
        stock = int(data.get("stock"))
        stock_minimo = int(data.get("stock_minimo", 5))
        price = float(data.get("precio"))
    except (TypeError, ValueError):
        return jsonify({"error": "Categoria, stock, stock minimo o precio invalidos"}), 400

    if stock < 0 or stock_minimo < 0 or price < 0:
        return jsonify({"error": "Stock, stock minimo y precio no pueden ser negativos"}), 400

    nombre = (data.get("nombre") or "").strip()
    codigo_barras = (data.get("codigo_barras") or "").strip()

    if not nombre:
        return jsonify({"error": "El nombre del producto es obligatorio"}), 400

    try:
        updated = update_product(
            mysql,
            product_id,
            nombre,
            codigo_barras,
            price,
            stock,
            category_id,
            stock_minimo,
        )
        if not updated:
            return jsonify({"error": "Producto no encontrado"}), 404
        product = get_product_by_id(mysql, product_id)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except Exception:
        return jsonify({"error": "No fue posible actualizar el producto"}), 500

    return jsonify({"message": "Producto actualizado", "product": serialize_products([product])[0]}), 200


@jwt_required()
def delete_product_controller(mysql, product_id):
    current_user = get_current_user_context()
    if current_user.get("rol") != "admin":
        return jsonify({"error": "No autorizado"}), 403

    try:
        deleted = delete_product(mysql, product_id)
        if not deleted:
            return jsonify({"error": "Producto no encontrado"}), 404
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except Exception:
        return jsonify({"error": "No fue posible eliminar el producto"}), 500

    return jsonify({"message": "Producto eliminado"}), 200


@jwt_required()
def get_admin_dashboard(mysql):
    current_user = get_current_user_context()
    if current_user.get("rol") != "admin":
        return jsonify({"error": "No autorizado"}), 403

    return jsonify(get_daily_summary(mysql)), 200
