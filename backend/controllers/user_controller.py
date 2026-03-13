from flask import request, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models.user_model import get_all_users, create_user, update_user, delete_user

bcrypt = Bcrypt()


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


def check_is_admin():
    current_user = get_current_user_context()
    if not current_user or current_user.get("rol") != "admin":
        return False
    return True


@jwt_required()
def get_users(mysql):
    if not check_is_admin():
        return jsonify({"error": "No autorizado"}), 403

    try:
        users = get_all_users(mysql)
        return jsonify(users), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@jwt_required()
def add_user(mysql):
    if not check_is_admin():
        return jsonify({"error": "No autorizado"}), 403

    data = request.json or {}
    nombre = (data.get("nombre") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    rol = data.get("rol", "cajero")
    estado = data.get("estado", "activo")

    if not nombre or not email or not password:
        return jsonify({"error": "Faltan datos obligatorios"}), 400

    if rol not in {"admin", "cajero"}:
        return jsonify({"error": "Rol invalido"}), 400

    if estado not in {"activo", "inactivo"}:
        return jsonify({"error": "Estado invalido"}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

    try:
        user_id = create_user(mysql, nombre, email, hashed_password, rol, estado)
        return jsonify({"message": "Usuario creado correctamente", "id": user_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@jwt_required()
def modify_user(mysql, user_id):
    if not check_is_admin():
        return jsonify({"error": "No autorizado"}), 403

    data = request.json or {}
    nombre = (data.get("nombre") or "").strip()
    email = (data.get("email") or "").strip().lower()
    rol = data.get("rol")
    estado = data.get("estado")
    password = (data.get("password") or "").strip()

    if not nombre or not email or not rol or not estado:
        return jsonify({"error": "Faltan datos obligatorios"}), 400

    if rol not in {"admin", "cajero"}:
        return jsonify({"error": "Rol invalido"}), 400

    if estado not in {"activo", "inactivo"}:
        return jsonify({"error": "Estado invalido"}), 400

    hashed_password = None
    if password:
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

    try:
        update_user(mysql, user_id, nombre, email, rol, estado, hashed_password)
        return jsonify({"message": "Usuario actualizado correctamente"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@jwt_required()
def remove_user(mysql, user_id):
    if not check_is_admin():
        return jsonify({"error": "No autorizado"}), 403

    try:
        delete_user(mysql, user_id)
        return jsonify({"message": "Usuario eliminado correctamente"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
