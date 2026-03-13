from flask import request, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token
from models.user_model import get_user_by_email

bcrypt = Bcrypt()


def login(mysql):
    data = request.json or {}

    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Debes enviar correo y contrasena"}), 400

    user = get_user_by_email(mysql, email)

    if user is None:
        return jsonify({"error": "Usuario no encontrado"}), 404

    hashed_password = user[3]
    user_status = user[5] if len(user) > 5 else "activo"

    if user_status != "activo":
        return jsonify({"error": "Usuario inactivo. Contacta al administrador"}), 403

    if bcrypt.check_password_hash(hashed_password, password):
        user_payload = {
            "id": user[0],
            "nombre": user[1],
            "rol": user[4],
            "estado": user_status,
        }

        access_token = create_access_token(
            identity=str(user[0]),
            additional_claims={
                "nombre": user[1],
                "rol": user[4],
            },
        )

        return jsonify({
            "message": "Login correcto",
            "token": access_token,
            "user": user_payload,
        })

    return jsonify({"error": "Contrasena incorrecta"}), 401
