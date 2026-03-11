from flask import Blueprint

from controllers.sale_controller import register_sale

sale_bp = Blueprint("sales", __name__)


def init_sale_routes(mysql):
    @sale_bp.route("/api/sales", methods=["POST"])
    def sales():
        return register_sale(mysql)

    return sale_bp
