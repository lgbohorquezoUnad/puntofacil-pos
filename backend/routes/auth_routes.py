from flask import Blueprint
from controllers.auth_controller import login

auth_bp = Blueprint("auth", __name__)

def init_auth_routes(mysql):

    @auth_bp.route("/api/login", methods=["POST"])
    def login_route():
        return login(mysql)

    return auth_bp