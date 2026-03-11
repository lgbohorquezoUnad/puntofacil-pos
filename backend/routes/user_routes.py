from flask import Blueprint
from controllers.user_controller import get_users, add_user, modify_user, remove_user

user_bp = Blueprint("users", __name__)

def init_user_routes(mysql):

    @user_bp.route("/api/usuarios", methods=["GET"])
    def fetch_users():
        return get_users(mysql)

    @user_bp.route("/api/usuarios", methods=["POST"])
    def create_new_user():
        return add_user(mysql)

    @user_bp.route("/api/usuarios/<int:user_id>", methods=["PUT"])
    def update_existing_user(user_id):
        return modify_user(mysql, user_id)

    @user_bp.route("/api/usuarios/<int:user_id>", methods=["DELETE"])
    def delete_existing_user(user_id):
        return remove_user(mysql, user_id)

    return user_bp
