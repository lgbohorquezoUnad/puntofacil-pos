const API_BASE_URL = window.API_CONFIG.baseUrl;

Auth.requireAdmin();

const state = {
  products: [],
  suppliers: [],
  locations: [],
  poItems: [],
  transferItems: [],
  currentOrder: null,
  currentCount: null,
  countItems: [],
  auditLogs: []
};

function money(value) {
  return "$" + Number(value || 0).toLocaleString("es-CO", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

async function fetchJson(url, options = undefined) {
  const response = await Auth.fetchWithAuth(url, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || "Error de API");
  }
  return data;
}

function setSelectOptions(select, items, labelFn, placeholder) {
  if (!select) return;
  select.innerHTML = "";
  if (placeholder) {
    const option = document.createElement("option");
    option.value = "";
    option.textContent = placeholder;
    select.appendChild(option);
  }
  items.forEach(item => {
    const option = document.createElement("option");
    option.value = item.id;
    option.textContent = labelFn(item);
    select.appendChild(option);
  });
}

function refreshProductSelects() {
  const labelFn = (p) => `${p.nombre} (#${p.id})`;
  setSelectOptions(document.getElementById("poProduct"), state.products, labelFn, "Selecciona producto");
  setSelectOptions(document.getElementById("transferProduct"), state.products, labelFn, "Selecciona producto");
}

function refreshSuppliersSelect() {
  setSelectOptions(
    document.getElementById("poSupplier"),
    state.suppliers,
    (s) => s.nombre,
    "Selecciona proveedor"
  );
}

function refreshLocationsSelects() {
  const labelFn = (l) => `${l.nombre} (${l.tipo})`;
  setSelectOptions(document.getElementById("transferOrigin"), state.locations, labelFn, "Origen");
  setSelectOptions(document.getElementById("transferDestination"), state.locations, labelFn, "Destino");
}

function renderPurchaseItems() {
  const tbody = document.getElementById("poItemsTable");
  tbody.innerHTML = "";

  if (!state.poItems.length) {
    tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-3">Agrega items a la orden</td></tr>';
  } else {
    state.poItems.forEach((item, index) => {
      tbody.innerHTML += `
        <tr>
          <td>${item.product_name}</td>
          <td>${item.quantity}</td>
          <td>${money(item.unit_cost)}</td>
          <td>${money(item.subtotal)}</td>
          <td><button class="btn btn-sm btn-outline-danger" data-index="${index}">Quitar</button></td>
        </tr>
      `;
    });
  }

  const total = state.poItems.reduce((sum, item) => sum + item.subtotal, 0);
  document.getElementById("poTotal").textContent = money(total);

  tbody.querySelectorAll("button[data-index]").forEach(btn => {
    btn.addEventListener("click", () => {
      const index = Number(btn.dataset.index);
      state.poItems.splice(index, 1);
      renderPurchaseItems();
    });
  });
}

function addPurchaseItem() {
  const productId = Number(document.getElementById("poProduct").value);
  const quantity = Number(document.getElementById("poQty").value);
  const unitCost = Number(document.getElementById("poCost").value);

  if (!productId) {
    UI.toast("Selecciona un producto", "warning");
    return;
  }
  if (!Number.isInteger(quantity) || quantity <= 0) {
    UI.toast("Cantidad invalida", "warning");
    return;
  }
  if (Number.isNaN(unitCost) || unitCost < 0) {
    UI.toast("Costo unitario invalido", "warning");
    return;
  }

  const product = state.products.find(p => p.id === productId);
  if (!product) {
    UI.toast("Producto no encontrado", "warning");
    return;
  }

  const existing = state.poItems.find(item => item.product_id === productId);
  if (existing) {
    existing.quantity += quantity;
    existing.unit_cost = unitCost;
    existing.subtotal = existing.quantity * existing.unit_cost;
  } else {
    state.poItems.push({
      product_id: productId,
      product_name: product.nombre,
      quantity,
      unit_cost: unitCost,
      subtotal: quantity * unitCost
    });
  }

  document.getElementById("poQty").value = "";
  document.getElementById("poCost").value = "";
  renderPurchaseItems();
}

async function submitPurchaseOrder() {
  const supplierId = Number(document.getElementById("poSupplier").value);
  const notes = document.getElementById("poNotes").value.trim();

  if (!supplierId) {
    UI.toast("Selecciona un proveedor", "warning");
    return;
  }
  if (!state.poItems.length) {
    UI.toast("Agrega items a la orden", "warning");
    return;
  }

  const payload = {
    supplier_id: supplierId,
    notes,
    items: state.poItems.map(item => ({
      product_id: item.product_id,
      quantity: item.quantity,
      unit_cost: item.unit_cost
    }))
  };

  try {
    const data = await fetchJson(`${API_BASE_URL}/api/admin/purchase-orders`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    UI.toast("Orden de compra emitida", "success");
    state.poItems = [];
    renderPurchaseItems();
    document.getElementById("poNotes").value = "";
    if (data.order && data.order.order_id) {
      document.getElementById("poReceiveId").value = data.order.order_id;
      await loadPurchaseOrder(data.order.order_id);
    }
  } catch (error) {
    UI.alert("Error", error.message || "No fue posible crear la orden");
  }
}

function renderPurchaseOrderSummary() {
  const summary = document.getElementById("poReceiveSummary");
  if (!state.currentOrder) {
    summary.textContent = "No hay orden cargada.";
    document.getElementById("statusOrder").textContent = "Orden activa: Sin orden cargada.";
    return;
  }

  summary.textContent = `Orden #${state.currentOrder.order_id} - ${state.currentOrder.supplier_name} - Estado: ${state.currentOrder.status}`;
  document.getElementById("statusOrder").textContent = `Orden activa: #${state.currentOrder.order_id} (${state.currentOrder.status}).`;
}

function renderPurchaseOrderItems() {
  const tbody = document.getElementById("poReceiveItems");
  tbody.innerHTML = "";

  if (!state.currentOrder || !state.currentOrder.items.length) {
    tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted py-3">Sin items para mostrar</td></tr>';
    return;
  }

  state.currentOrder.items.forEach(item => {
    tbody.innerHTML += `
      <tr>
        <td>${item.product_name}</td>
        <td>${item.qty_pending}</td>
        <td>
          <input type="number" min="0" class="form-control form-control-sm" data-product-id="${item.product_id}" data-pending="${item.qty_pending}" placeholder="0">
        </td>
        <td>
          <input type="date" class="form-control form-control-sm" data-expiration="${item.product_id}">
        </td>
      </tr>
    `;
  });
}

async function loadPurchaseOrder(orderId) {
  if (!orderId) return;
  try {
    const data = await fetchJson(`${API_BASE_URL}/api/admin/purchase-orders/${orderId}`);
    state.currentOrder = data;
    renderPurchaseOrderSummary();
    renderPurchaseOrderItems();
  } catch (error) {
    state.currentOrder = null;
    renderPurchaseOrderSummary();
    renderPurchaseOrderItems();
    UI.alert("Error", error.message || "No fue posible cargar la orden");
  }
}

function fillReceiveAll() {
  if (!state.currentOrder) {
    UI.toast("Carga una orden primero", "warning");
    return;
  }

  document.querySelectorAll("#poReceiveItems input[data-product-id]").forEach(input => {
    input.value = input.dataset.pending || "0";
  });
}

async function submitReceive() {
  if (!state.currentOrder) {
    UI.toast("Carga una orden primero", "warning");
    return;
  }

  const receipts = [];
  const batchExpirations = {};
  let validationError = null;

  document.querySelectorAll("#poReceiveItems input[data-product-id]").forEach(input => {
    const qtyRaw = input.value;
    if (!qtyRaw) return;

    const qty = Number(qtyRaw);
    const pending = Number(input.dataset.pending);
    const productId = Number(input.dataset.productId);

    if (!Number.isInteger(qty) || qty < 0 || qty > pending) {
      validationError = `Cantidad invalida para producto #${productId}`;
      return;
    }

    receipts.push({ product_id: productId, quantity: qty });

    const expirationInput = document.querySelector(`input[data-expiration='${productId}']`);
    if (expirationInput && expirationInput.value) {
      batchExpirations[String(productId)] = expirationInput.value;
    }
  });

  if (validationError) {
    UI.alert("Error", validationError);
    return;
  }

  if (!receipts.length) {
    UI.toast("Indica cantidades a recibir", "warning");
    return;
  }

  try {
    await fetchJson(`${API_BASE_URL}/api/admin/purchase-orders/${state.currentOrder.order_id}/receive`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ receipts, batch_expirations: batchExpirations })
    });

    UI.toast("Recepcion aplicada", "success");
    await loadPurchaseOrder(state.currentOrder.order_id);
  } catch (error) {
    UI.alert("Error", error.message || "No fue posible recepcionar");
  }
}

function renderCountInfo() {
  const info = document.getElementById("countCurrentInfo");
  if (!state.currentCount) {
    info.textContent = "Sin conteo activo.";
    document.getElementById("statusCount").textContent = "Conteo activo: Sin conteo cargado.";
    return;
  }

  info.textContent = `Conteo #${state.currentCount.count_id} - Estado: ${state.currentCount.status}`;
  document.getElementById("statusCount").textContent = `Conteo activo: #${state.currentCount.count_id} (${state.currentCount.status}).`;
}

function renderCountItems() {
  const tbody = document.getElementById("countItemsTable");
  tbody.innerHTML = "";

  if (!state.countItems.length) {
    tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted py-3">Sin items para contar</td></tr>';
    return;
  }

  const term = document.getElementById("countSearch").value.trim().toLowerCase();
  const filtered = term
    ? state.countItems.filter(item => item.product_name.toLowerCase().includes(term))
    : state.countItems;

  if (!filtered.length) {
    tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted py-3">No hay coincidencias</td></tr>';
    return;
  }

  filtered.forEach(item => {
    const countedValue = item.counted_stock === null ? "" : item.counted_stock;
    const diffValue = item.counted_stock === null ? "-" : (item.counted_stock - item.system_stock);

    tbody.innerHTML += `
      <tr>
        <td>${item.product_name}</td>
        <td>${item.system_stock}</td>
        <td>
          <input type="number" min="0" class="form-control form-control-sm" data-count-product="${item.product_id}" data-system="${item.system_stock}" value="${countedValue}">
        </td>
        <td class="text-muted" data-diff="${item.product_id}">${diffValue}</td>
      </tr>
    `;
  });

  tbody.querySelectorAll("input[data-count-product]").forEach(input => {
    input.addEventListener("input", () => {
      const productId = input.dataset.countProduct;
      const system = Number(input.dataset.system);
      const value = input.value === "" ? null : Number(input.value);
      const diffCell = document.querySelector(`[data-diff='${productId}']`);
      if (!diffCell) return;
      if (value === null || Number.isNaN(value)) {
        diffCell.textContent = "-";
        return;
      }
      diffCell.textContent = String(value - system);
    });
  });
}

async function createCount() {
  const notes = document.getElementById("countNotes").value.trim();
  try {
    const data = await fetchJson(`${API_BASE_URL}/api/admin/inventory-counts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ notes })
    });

    UI.toast("Conteo abierto", "success");
    if (data.count && data.count.count_id) {
      document.getElementById("countLoadId").value = data.count.count_id;
      await loadCount(data.count.count_id);
    }
  } catch (error) {
    UI.alert("Error", error.message || "No fue posible abrir el conteo");
  }
}

async function loadCount(countId) {
  if (!countId) return;
  try {
    const data = await fetchJson(`${API_BASE_URL}/api/admin/inventory-counts/${countId}`);
    state.currentCount = data;
    state.countItems = data.items || [];
    renderCountInfo();
    renderCountItems();
  } catch (error) {
    state.currentCount = null;
    state.countItems = [];
    renderCountInfo();
    renderCountItems();
    UI.alert("Error", error.message || "No fue posible cargar el conteo");
  }
}

async function reconcileCount() {
  if (!state.currentCount) {
    UI.toast("Carga un conteo primero", "warning");
    return;
  }

  const items = [];
  document.querySelectorAll("#countItemsTable input[data-count-product]").forEach(input => {
    if (input.value === "") return;
    const value = Number(input.value);
    if (!Number.isInteger(value) || value < 0) {
      return;
    }
    items.push({
      product_id: Number(input.dataset.countProduct),
      stock_counted: value
    });
  });

  if (!items.length) {
    UI.toast("Ingresa al menos un stock contado", "warning");
    return;
  }

  const reason = document.getElementById("countReason").value.trim();

  try {
    await fetchJson(`${API_BASE_URL}/api/admin/inventory-counts/${state.currentCount.count_id}/reconcile`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ items, reason })
    });

    UI.toast("Conteo conciliado", "success");
    await loadCount(state.currentCount.count_id);
  } catch (error) {
    UI.alert("Error", error.message || "No fue posible cerrar el conteo");
  }
}

function renderTransferItems() {
  const tbody = document.getElementById("transferItemsTable");
  tbody.innerHTML = "";

  if (!state.transferItems.length) {
    tbody.innerHTML = '<tr><td colspan="3" class="text-center text-muted py-3">Agrega items a transferir</td></tr>';
  } else {
    state.transferItems.forEach((item, index) => {
      tbody.innerHTML += `
        <tr>
          <td>${item.product_name}</td>
          <td>${item.quantity}</td>
          <td><button class="btn btn-sm btn-outline-danger" data-index="${index}">Quitar</button></td>
        </tr>
      `;
    });
  }

  tbody.querySelectorAll("button[data-index]").forEach(btn => {
    btn.addEventListener("click", () => {
      const index = Number(btn.dataset.index);
      state.transferItems.splice(index, 1);
      renderTransferItems();
    });
  });
}

function addTransferItem() {
  const productId = Number(document.getElementById("transferProduct").value);
  const quantity = Number(document.getElementById("transferQty").value);

  if (!productId) {
    UI.toast("Selecciona un producto", "warning");
    return;
  }
  if (!Number.isInteger(quantity) || quantity <= 0) {
    UI.toast("Cantidad invalida", "warning");
    return;
  }

  const product = state.products.find(p => p.id === productId);
  if (!product) {
    UI.toast("Producto no encontrado", "warning");
    return;
  }

  const existing = state.transferItems.find(item => item.product_id === productId);
  if (existing) {
    existing.quantity += quantity;
  } else {
    state.transferItems.push({
      product_id: productId,
      product_name: product.nombre,
      quantity
    });
  }

  document.getElementById("transferQty").value = "";
  renderTransferItems();
}

async function submitTransfer() {
  const originId = Number(document.getElementById("transferOrigin").value);
  const destinationId = Number(document.getElementById("transferDestination").value);
  const notes = document.getElementById("transferNotes").value.trim();

  if (!originId || !destinationId) {
    UI.toast("Selecciona origen y destino", "warning");
    return;
  }
  if (originId === destinationId) {
    UI.toast("Origen y destino no pueden ser iguales", "warning");
    return;
  }
  if (!state.transferItems.length) {
    UI.toast("Agrega items a transferir", "warning");
    return;
  }

  try {
    await fetchJson(`${API_BASE_URL}/api/admin/transfers`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        origin_location_id: originId,
        destination_location_id: destinationId,
        notes,
        items: state.transferItems.map(item => ({
          product_id: item.product_id,
          quantity: item.quantity
        }))
      })
    });

    UI.toast("Transferencia registrada", "success");
    state.transferItems = [];
    renderTransferItems();
    document.getElementById("transferNotes").value = "";
    document.getElementById("statusTransfer").textContent = "Transferencias listas para enviar.";
  } catch (error) {
    UI.alert("Error", error.message || "No fue posible registrar la transferencia");
  }
}

function renderAuditLogs() {
  const tbody = document.getElementById("auditTable");
  tbody.innerHTML = "";

  if (!state.auditLogs.length) {
    tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted py-3">Sin registros recientes</td></tr>';
    return;
  }

  state.auditLogs.forEach(log => {
    const detailParts = [];
    if (log.entity) {
      detailParts.push(`${log.entity} #${log.entity_id || "-"}`);
    }
    const details = log.details ? JSON.stringify(log.details) : "";
    if (details) {
      detailParts.push(details.length > 140 ? `${details.slice(0, 140)}...` : details);
    }

    tbody.innerHTML += `
      <tr>
        <td>${log.created_at || "-"}</td>
        <td>${log.module}</td>
        <td>${log.action}</td>
        <td>${detailParts.join(" - ") || "-"}</td>
      </tr>
    `;
  });
}

async function loadAuditLogs() {
  const moduleValue = document.getElementById("auditModule").value;
  const url = moduleValue
    ? `${API_BASE_URL}/api/admin/audit-logs?module=${encodeURIComponent(moduleValue)}&limit=120`
    : `${API_BASE_URL}/api/admin/audit-logs?limit=120`;

  try {
    const data = await fetchJson(url);
    state.auditLogs = data.logs || [];
    renderAuditLogs();
  } catch (error) {
    UI.alert("Error", error.message || "No fue posible cargar auditoria");
  }
}

async function loadInitialData() {
  const [products, suppliers, locations] = await Promise.all([
    fetchJson(`${API_BASE_URL}/api/products`),
    fetchJson(`${API_BASE_URL}/api/admin/suppliers`),
    fetchJson(`${API_BASE_URL}/api/admin/locations`)
  ]);

  state.products = products || [];
  state.suppliers = suppliers.suppliers || [];
  state.locations = locations.locations || [];

  refreshProductSelects();
  refreshSuppliersSelect();
  refreshLocationsSelects();
}

function wireEvents() {
  document.getElementById("poAddItem").addEventListener("click", addPurchaseItem);
  document.getElementById("poSubmit").addEventListener("click", submitPurchaseOrder);
  document.getElementById("poLoadBtn").addEventListener("click", () => {
    const orderId = Number(document.getElementById("poReceiveId").value);
    if (!orderId) {
      UI.toast("Indica un ID de orden", "warning");
      return;
    }
    loadPurchaseOrder(orderId);
  });
  document.getElementById("poReceiveFillAll").addEventListener("click", fillReceiveAll);
  document.getElementById("poReceiveSubmit").addEventListener("click", submitReceive);

  document.getElementById("countCreateBtn").addEventListener("click", createCount);
  document.getElementById("countLoadBtn").addEventListener("click", () => {
    const countId = Number(document.getElementById("countLoadId").value);
    if (!countId) {
      UI.toast("Indica un ID de conteo", "warning");
      return;
    }
    loadCount(countId);
  });
  document.getElementById("countSearch").addEventListener("input", renderCountItems);
  document.getElementById("countReconcileBtn").addEventListener("click", reconcileCount);

  document.getElementById("transferAddItem").addEventListener("click", addTransferItem);
  document.getElementById("transferSubmit").addEventListener("click", submitTransfer);

  document.getElementById("auditRefreshBtn").addEventListener("click", loadAuditLogs);
  document.getElementById("auditModule").addEventListener("change", loadAuditLogs);
}

async function initOperativa() {
  try {
    wireEvents();
    await loadInitialData();
    renderPurchaseItems();
    renderTransferItems();
    renderCountInfo();
    await loadAuditLogs();
  } catch (error) {
    UI.alert("Error", error.message || "No fue posible inicializar la pantalla operativa");
  }
}

initOperativa();

