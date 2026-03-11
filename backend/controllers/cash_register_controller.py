from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from models.cash_register_model import (
    close_cash_register,
    get_open_cash_register,
    open_cash_register,
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


@jwt_required()
def get_cash_register_status(mysql):
    cash_register = get_open_cash_register(mysql)
    return jsonify({"cash_register": cash_register}), 200


@jwt_required()
def open_cash_register_controller(mysql):
    current_user = get_current_user_context()
    data = request.json or {}
    user_id = current_user.get("id")
    notes = data.get("notes")

    try:
        opening_amount = float(data.get("opening_amount"))
    except (TypeError, ValueError):
        return jsonify({"error": "Debes enviar un monto de apertura valido"}), 400

    try:
        cash_register = open_cash_register(mysql, opening_amount, user_id, notes)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except Exception:
        return jsonify({"error": "No fue posible abrir la caja"}), 500

    return jsonify({"message": "Caja abierta correctamente", "cash_register": cash_register}), 201


@jwt_required()
def close_cash_register_controller(mysql):
    data = request.json or {}
    notes = data.get("notes")

    try:
        closing_amount = float(data.get("closing_amount"))
    except (TypeError, ValueError):
        return jsonify({"error": "Debes enviar un monto de cierre valido"}), 400

    try:
        summary = close_cash_register(mysql, closing_amount, notes)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except Exception:
        return jsonify({"error": "No fue posible cerrar la caja"}), 500

    return jsonify({"message": "Caja cerrada correctamente", "summary": summary}), 200
