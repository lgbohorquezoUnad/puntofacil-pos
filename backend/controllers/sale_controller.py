from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from models.sale_model import create_sale, list_sales


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


@jwt_required()
def register_sale(mysql):
    current_user = get_current_user_context()
    data = request.json or {}
    payment_method = (data.get("payment_method") or "").strip()
    items = data.get("items") or []
    user_id = current_user.get("id")

    if not payment_method:
        return jsonify({"error": "Debes seleccionar un metodo de pago"}), 400

    if not items:
        return jsonify({"error": "Debes enviar al menos un producto"}), 400

    normalized_items = {}

    for item in items:
        try:
            product_id = int(item.get("product_id"))
            qty = int(item.get("qty"))
        except (TypeError, ValueError):
            return jsonify({"error": "Los productos enviados no son validos"}), 400

        if product_id not in normalized_items:
            normalized_items[product_id] = 0

        normalized_items[product_id] += qty

    sale_items = [
        {"product_id": product_id, "qty": qty}
        for product_id, qty in normalized_items.items()
    ]

    try:
        sale = create_sale(mysql, payment_method, sale_items, user_id)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except Exception:
        return jsonify({"error": "No fue posible registrar la venta"}), 500

    return jsonify({"message": "Venta registrada correctamente", "sale": sale}), 201


@jwt_required()
def get_sales_history(mysql):
    current_user = get_current_user_context()
    if current_user.get("rol") != "admin":
        return jsonify({"error": "No autorizado"}), 403

    try:
        limit = int(request.args.get("limit", 20))
    except ValueError:
        return jsonify({"error": "El limite enviado no es valido"}), 400

    sales = list_sales(mysql, limit)
    return jsonify({"sales": sales}), 200
