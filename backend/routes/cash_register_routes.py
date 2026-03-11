from flask import Blueprint

from controllers.cash_register_controller import (
    close_cash_register_controller,
    get_cash_register_status,
    open_cash_register_controller,
)

cash_register_bp = Blueprint("cash_register", __name__)


def init_cash_register_routes(mysql):
    @cash_register_bp.route("/api/cash-register/current", methods=["GET"])
    def current_cash_register():
        return get_cash_register_status(mysql)

    @cash_register_bp.route("/api/cash-register/open", methods=["POST"])
    def open_cash_register():
        return open_cash_register_controller(mysql)

    @cash_register_bp.route("/api/cash-register/close", methods=["POST"])
    def close_cash_register():
        return close_cash_register_controller(mysql)

    return cash_register_bp
