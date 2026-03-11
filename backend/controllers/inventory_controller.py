from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from models.inventory_model import (
    adjust_inventory_stock,
    get_inventory_overview,
    list_inventory_movements,
)


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


def require_admin_user():
    current_user = get_current_user_context()
    if current_user.get("rol") != "admin":
        return None, (jsonify({"error": "No autorizado"}), 403)
    return current_user, None


@jwt_required()
def get_inventory_overview_controller(mysql):
    current_user, admin_error = require_admin_user()
    if admin_error:
        return admin_error

    search = (request.args.get("search") or "").strip() or None
    category_id = request.args.get("category_id")
    stock_status = (request.args.get("stock_status") or "all").strip().lower()
    sort_by = (request.args.get("sort_by") or "nombre").strip().lower()
    sort_order = (request.args.get("sort_order") or "asc").strip().lower()

    try:
        limit = int(request.args.get("limit", 500))
    except ValueError:
        return jsonify({"error": "El limite enviado no es valido"}), 400

    if limit <= 0 or limit > 1000:
        return jsonify({"error": "El limite debe estar entre 1 y 1000"}), 400

    if category_id in (None, ""):
        category_id = None
    else:
        try:
            category_id = int(category_id)
        except ValueError:
            return jsonify({"error": "La categoria enviada no es valida"}), 400

    if stock_status not in {"all", "ok", "low", "out"}:
        return jsonify({"error": "El filtro de estado de stock no es valido"}), 400

    result = get_inventory_overview(
        mysql,
        search=search,
        category_id=category_id,
        stock_status=stock_status,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
    )

    return jsonify(result), 200


@jwt_required()
def adjust_inventory_stock_controller(mysql, product_id):
    current_user, admin_error = require_admin_user()
    if admin_error:
        return admin_error

    data = request.json or {}
    movement_type = (data.get("movement_type") or "").strip().lower()
    reason = (data.get("reason") or "").strip() or None

    try:
        quantity = int(data.get("quantity"))
    except (TypeError, ValueError):
        return jsonify({"error": "La cantidad enviada no es valida"}), 400

    try:
        result = adjust_inventory_stock(
            mysql,
            product_id=product_id,
            movement_type=movement_type,
            quantity=quantity,
            reason=reason,
            user_id=current_user.get("id"),
        )
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except Exception:
        return jsonify({"error": "No fue posible ajustar el inventario"}), 500

    return jsonify({"message": "Inventario actualizado", "adjustment": result}), 200


@jwt_required()
def get_inventory_movements_controller(mysql):
    current_user, admin_error = require_admin_user()
    if admin_error:
        return admin_error

    product_id = request.args.get("product_id")

    try:
        limit = int(request.args.get("limit", 100))
    except ValueError:
        return jsonify({"error": "El limite enviado no es valido"}), 400

    if limit <= 0 or limit > 500:
        return jsonify({"error": "El limite debe estar entre 1 y 500"}), 400

    if product_id in (None, ""):
        product_id = None
    else:
        try:
            product_id = int(product_id)
        except ValueError:
            return jsonify({"error": "El producto enviado no es valido"}), 400

    movements = list_inventory_movements(mysql, product_id=product_id, limit=limit)
    return jsonify({"movements": movements}), 200
