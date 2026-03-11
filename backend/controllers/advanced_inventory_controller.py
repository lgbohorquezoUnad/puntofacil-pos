# -*- coding: utf-8 -*-
from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from models.advanced_inventory_model import (
    create_inventory_count_session,
    create_purchase_order,
    create_transfer,
    get_audit_logs,
    get_inventory_count,
    get_inventory_financial_dashboard,
    get_purchase_order,
    get_restock_suggestions,
    list_expiring_batches,
    list_locations,
    list_suppliers,
    reconcile_inventory_count,
    receive_purchase_order,
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
def restock_suggestions_controller(mysql):
    current_user, admin_error = require_admin_user()
    if admin_error:
        return admin_error

    try:
        days = int(request.args.get("days", 30))
        coverage_days = int(request.args.get("coverage_days", 14))
        limit = int(request.args.get("limit", 100))
    except ValueError:
        return jsonify({"error": "Parámetros inválidos"}), 400

    if days <= 0 or coverage_days <= 0 or limit <= 0:
        return jsonify({"error": "days, coverage_days y limit deben ser mayores a cero"}), 400

    result = get_restock_suggestions(mysql, days=days, coverage_days=coverage_days, limit=limit)
    return jsonify(result), 200


@jwt_required()
def expiring_batches_controller(mysql):
    current_user, admin_error = require_admin_user()
    if admin_error:
        return admin_error

    try:
        days = int(request.args.get("days", 30))
        limit = int(request.args.get("limit", 200))
    except ValueError:
        return jsonify({"error": "Parámetros inválidos"}), 400

    include_expired = str(request.args.get("include_expired", "true")).lower() != "false"

    batches = list_expiring_batches(mysql, days=days, include_expired=include_expired, limit=limit)
    return jsonify({"batches": batches}), 200


@jwt_required()
def create_purchase_order_controller(mysql):
    current_user, admin_error = require_admin_user()
    if admin_error:
        return admin_error

    data = request.json or {}
    supplier_id = data.get("supplier_id")
    items = data.get("items") or []
    notes = data.get("notes")

    try:
        supplier_id = int(supplier_id)
    except (TypeError, ValueError):
        return jsonify({"error": "supplier_id inválido"}), 400

    try:
        order = create_purchase_order(
            mysql,
            user_id=current_user.get("id"),
            supplier_id=supplier_id,
            items=items,
            notes=notes,
        )
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except Exception:
        return jsonify({"error": "No fue posible crear la orden de compra"}), 500

    return jsonify({"message": "Orden de compra creada", "order": order}), 201


@jwt_required()
def receive_purchase_order_controller(mysql, order_id):
    current_user, admin_error = require_admin_user()
    if admin_error:
        return admin_error

    data = request.json or {}
    receipts = data.get("receipts") or []
    batch_expirations = data.get("batch_expirations") or {}

    try:
        result = receive_purchase_order(
            mysql,
            user_id=current_user.get("id"),
            order_id=order_id,
            receipts=receipts,
            batch_expirations=batch_expirations,
        )
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except Exception:
        return jsonify({"error": "No fue posible recepcionar la orden"}), 500

    return jsonify({"message": "Recepción aplicada", "receipt": result}), 200


@jwt_required()
def create_inventory_count_controller(mysql):
    current_user, admin_error = require_admin_user()
    if admin_error:
        return admin_error

    data = request.json or {}
    notes = data.get("notes")

    try:
        result = create_inventory_count_session(mysql, user_id=current_user.get("id"), notes=notes)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except Exception:
        return jsonify({"error": "No fue posible abrir el conteo"}), 500

    return jsonify({"message": "Conteo abierto", "count": result}), 201


@jwt_required()
def reconcile_inventory_count_controller(mysql, count_id):
    current_user, admin_error = require_admin_user()
    if admin_error:
        return admin_error

    data = request.json or {}
    counted_items = data.get("items") or []
    reason = (data.get("reason") or "").strip() or "Ajuste por conteo físico"

    try:
        result = reconcile_inventory_count(
            mysql,
            user_id=current_user.get("id"),
            count_id=count_id,
            counted_items=counted_items,
            reason=reason,
        )
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except Exception:
        return jsonify({"error": "No fue posible cerrar el conteo"}), 500

    return jsonify({"message": "Conteo reconciliado", "count": result}), 200


@jwt_required()
def create_transfer_controller(mysql):
    current_user, admin_error = require_admin_user()
    if admin_error:
        return admin_error

    data = request.json or {}

    try:
        origin_location_id = int(data.get("origin_location_id"))
        destination_location_id = int(data.get("destination_location_id"))
    except (TypeError, ValueError):
        return jsonify({"error": "Ubicaciones inválidas"}), 400

    items = data.get("items") or []
    notes = data.get("notes")

    try:
        result = create_transfer(
            mysql,
            user_id=current_user.get("id"),
            origin_location_id=origin_location_id,
            destination_location_id=destination_location_id,
            items=items,
            notes=notes,
        )
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except Exception:
        return jsonify({"error": "No fue posible registrar la transferencia"}), 500

    return jsonify({"message": "Transferencia registrada", "transfer": result}), 201


@jwt_required()
def audit_logs_controller(mysql):
    current_user, admin_error = require_admin_user()
    if admin_error:
        return admin_error

    module = (request.args.get("module") or "").strip() or None

    try:
        limit = int(request.args.get("limit", 100))
    except ValueError:
        return jsonify({"error": "Límite inválido"}), 400

    if limit <= 0 or limit > 500:
        return jsonify({"error": "El límite debe estar entre 1 y 500"}), 400

    logs = get_audit_logs(mysql, module=module, limit=limit)
    return jsonify({"logs": logs}), 200


@jwt_required()
def financial_dashboard_controller(mysql):
    current_user, admin_error = require_admin_user()
    if admin_error:
        return admin_error

    dashboard = get_inventory_financial_dashboard(mysql)
    return jsonify(dashboard), 200



@jwt_required()
def suppliers_controller(mysql):
    current_user, admin_error = require_admin_user()
    if admin_error:
        return admin_error

    suppliers = list_suppliers(mysql)
    return jsonify({"suppliers": suppliers}), 200


@jwt_required()
def locations_controller(mysql):
    current_user, admin_error = require_admin_user()
    if admin_error:
        return admin_error

    locations = list_locations(mysql)
    return jsonify({"locations": locations}), 200


@jwt_required()
def purchase_order_detail_controller(mysql, order_id):
    current_user, admin_error = require_admin_user()
    if admin_error:
        return admin_error

    order = get_purchase_order(mysql, order_id)
    if order is None:
        return jsonify({"error": "Orden de compra no encontrada"}), 404

    return jsonify(order), 200


@jwt_required()
def inventory_count_detail_controller(mysql, count_id):
    current_user, admin_error = require_admin_user()
    if admin_error:
        return admin_error

    count = get_inventory_count(mysql, count_id)
    if count is None:
        return jsonify({"error": "Conteo no encontrado"}), 404

    return jsonify(count), 200

