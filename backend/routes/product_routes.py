from flask import Blueprint

from controllers.advanced_inventory_controller import (
    audit_logs_controller,
    create_inventory_count_controller,
    create_purchase_order_controller,
    create_transfer_controller,
    expiring_batches_controller,
    financial_dashboard_controller,
    inventory_count_detail_controller,
    locations_controller,
    purchase_order_detail_controller,
    receive_purchase_order_controller,
    reconcile_inventory_count_controller,
    restock_suggestions_controller,
    suppliers_controller,
)
from controllers.inventory_controller import (
    adjust_inventory_stock_controller,
    get_inventory_movements_controller,
    get_inventory_overview_controller,
)
from controllers.product_controller import (
    create_product_controller,
    delete_product_controller,
    get_admin_dashboard,
    list_categories,
    list_products,
    update_product_controller,
)
from controllers.sale_controller import get_sales_history

product_bp = Blueprint("products", __name__)


def init_product_routes(mysql):
    @product_bp.route("/api/products", methods=["GET"])
    def products():
        return list_products(mysql)

    @product_bp.route("/api/categories", methods=["GET"])
    def categories():
        return list_categories(mysql)

    @product_bp.route("/api/sales", methods=["GET"])
    def sales_history():
        return get_sales_history(mysql)

    @product_bp.route("/api/admin/dashboard", methods=["GET"])
    def admin_dashboard():
        return get_admin_dashboard(mysql)

    @product_bp.route("/api/admin/products", methods=["POST"])
    def admin_create_product():
        return create_product_controller(mysql)

    @product_bp.route("/api/admin/products/<int:product_id>", methods=["PUT"])
    def admin_update_product(product_id):
        return update_product_controller(mysql, product_id)

    @product_bp.route("/api/admin/products/<int:product_id>", methods=["DELETE"])
    def admin_delete_product(product_id):
        return delete_product_controller(mysql, product_id)

    @product_bp.route("/api/admin/inventory", methods=["GET"])
    def admin_inventory_overview():
        return get_inventory_overview_controller(mysql)

    @product_bp.route("/api/admin/inventory/movements", methods=["GET"])
    def admin_inventory_movements():
        return get_inventory_movements_controller(mysql)

    @product_bp.route("/api/admin/inventory/<int:product_id>/stock", methods=["PATCH"])
    def admin_adjust_inventory(product_id):
        return adjust_inventory_stock_controller(mysql, product_id)

    @product_bp.route("/api/admin/inventory/restock-suggestions", methods=["GET"])
    def admin_restock_suggestions():
        return restock_suggestions_controller(mysql)

    @product_bp.route("/api/admin/inventory/financial-dashboard", methods=["GET"])
    def admin_financial_dashboard():
        return financial_dashboard_controller(mysql)

    @product_bp.route("/api/admin/inventory/batches/expiring", methods=["GET"])
    def admin_expiring_batches():
        return expiring_batches_controller(mysql)

    @product_bp.route("/api/admin/suppliers", methods=["GET"])
    def admin_suppliers():
        return suppliers_controller(mysql)

    @product_bp.route("/api/admin/locations", methods=["GET"])
    def admin_locations():
        return locations_controller(mysql)

    @product_bp.route("/api/admin/purchase-orders", methods=["POST"])
    def admin_create_purchase_order():
        return create_purchase_order_controller(mysql)

    @product_bp.route("/api/admin/purchase-orders/<int:order_id>", methods=["GET"])
    def admin_purchase_order_detail(order_id):
        return purchase_order_detail_controller(mysql, order_id)

    @product_bp.route("/api/admin/purchase-orders/<int:order_id>/receive", methods=["POST"])
    def admin_receive_purchase_order(order_id):
        return receive_purchase_order_controller(mysql, order_id)

    @product_bp.route("/api/admin/inventory-counts", methods=["POST"])
    def admin_create_count():
        return create_inventory_count_controller(mysql)

    @product_bp.route("/api/admin/inventory-counts/<int:count_id>", methods=["GET"])
    def admin_count_detail(count_id):
        return inventory_count_detail_controller(mysql, count_id)

    @product_bp.route("/api/admin/inventory-counts/<int:count_id>/reconcile", methods=["POST"])
    def admin_reconcile_count(count_id):
        return reconcile_inventory_count_controller(mysql, count_id)

    @product_bp.route("/api/admin/transfers", methods=["POST"])
    def admin_create_transfer():
        return create_transfer_controller(mysql)

    @product_bp.route("/api/admin/audit-logs", methods=["GET"])
    def admin_audit_logs():
        return audit_logs_controller(mysql)

    return product_bp


