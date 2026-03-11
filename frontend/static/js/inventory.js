const API_BASE_URL = "http://127.0.0.1:5000"

// Requerir solo admin
Auth.requireAdmin();

const state = {
  products: [],
  categories: [],
  movements: [],
  restockSuggestions: [],
  expiringBatches: [],
  financialDashboard: null,
  selectedProduct: null,
  filters: {
    search: "",
    category_id: "",
    stock_status: "all",
    sort_by: "nombre",
    sort_order: "asc"
  }
}

function money(value) {
  return "$" + Number(value || 0).toLocaleString("es-CO", { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function badgeForStatus(status) {
  if (status === "out") return '<span class="badge text-bg-danger">Agotado</span>'
  if (status === "low") return '<span class="badge text-bg-warning">Bajo</span>'
  return '<span class="badge text-bg-success">OK</span>'
}

function movementLabel(type, qty) {
  const sign = qty > 0 ? "+" : ""
  if (type === "set") return `Ajuste (${sign}${qty})`
  if (type === "add") return `Entrada (${sign}${qty})`
  return `Salida (${qty})`
}

async function fetchJson(url, options = undefined) {
  const response = await Auth.fetchWithAuth(url, options)
  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    throw new Error(data.error || "Error de API")
  }

  return data
}

function renderCategories() {
  const select = document.getElementById("filterCategory")
  select.innerHTML = '<option value="">Todas las categorias</option>'

  state.categories.forEach(c => {
    select.innerHTML += `<option value="${c.id}">${c.nombre}</option>`
  })
}

function renderSummary(summary) {
  document.getElementById("kpiProducts").textContent = summary.products_count || 0
  document.getElementById("kpiUnits").textContent = (summary.total_units || 0).toLocaleString("es-CO")
  document.getElementById("kpiValue").textContent = money(summary.total_inventory_value || 0)
  document.getElementById("kpiLow").textContent = summary.low_stock_count || 0
  document.getElementById("kpiOut").textContent = summary.out_of_stock_count || 0
}

function renderTable() {
  const tbody = document.getElementById("inventoryRows")
  tbody.innerHTML = ""

  if (!state.products.length) {
    tbody.innerHTML = '<tr><td colspan="10" class="text-center text-muted py-4">No hay productos para el filtro actual</td></tr>'
    return
  }

  state.products.forEach((p) => {
    tbody.innerHTML += `
      <tr>
        <td>#${p.id}</td>
        <td>
          <div class="fw-bold">${p.nombre}</div>
          <div class="small text-muted">${p.codigo_barras || "Sin codigo"}</div>
        </td>
        <td>${p.categoria || "Sin categoria"}</td>
        <td>${p.stock}</td>
        <td>${p.stock_minimo}</td>
        <td>${badgeForStatus(p.stock_status)}</td>
        <td>${money(p.precio)}</td>
        <td>${money(p.inventory_value)}</td>
        <td>${p.units_sold_30d}</td>
        <td>
          <button class="btn btn-sm btn-primary" onclick="openAdjustModal(${p.id})">Ajustar</button>
        </td>
      </tr>
    `
  })
}

function renderMovements() {
  const tbody = document.getElementById("movementsRows")
  tbody.innerHTML = ""

  if (!state.movements.length) {
    tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-3">Sin movimientos recientes</td></tr>'
    return
  }

  state.movements.forEach(m => {
    tbody.innerHTML += `
      <tr>
        <td>${m.created_at || "-"}</td>
        <td>${m.product_name}</td>
        <td>${movementLabel(m.movement_type, m.quantity)}</td>
        <td>${m.stock_before} -> ${m.stock_after}</td>
        <td>${m.reason || "-"}</td>
        <td class="text-muted">#${m.product_id}</td>
      </tr>
    `
  })
}

function renderRestockSuggestions() {
  const tbody = document.getElementById("restockRows")
  if (!tbody) return

  tbody.innerHTML = ""

  if (!state.restockSuggestions.length) {
    tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted py-2">Sin sugerencias por ahora</td></tr>'
    return
  }

  state.restockSuggestions.slice(0, 12).forEach(item => {
    tbody.innerHTML += `
      <tr>
        <td>${item.nombre}</td>
        <td>${item.current_stock}</td>
        <td>${item.recommended_stock}</td>
        <td><strong>${item.reorder_qty}</strong></td>
      </tr>
    `
  })
}

function renderExpiringBatches() {
  const tbody = document.getElementById("expiringRows")
  if (!tbody) return

  tbody.innerHTML = ""

  if (!state.expiringBatches.length) {
    tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted py-2">Sin lotes próximos a vencer</td></tr>'
    return
  }

  state.expiringBatches.slice(0, 12).forEach(batch => {
    const days = batch.days_to_expire
    const badge = days < 0 ? '<span class="badge text-bg-danger">Vencido</span>' : `<span class="badge text-bg-warning">${days}</span>`

    tbody.innerHTML += `
      <tr>
        <td>${batch.product_name}</td>
        <td>${batch.batch_number}</td>
        <td>${batch.expires_at || "-"}</td>
        <td>${badge}</td>
      </tr>
    `
  })
}

function renderFinancialDashboard() {
  const d = state.financialDashboard || {}

  const fdCost = document.getElementById("fdCost")
  if (!fdCost) return

  document.getElementById("fdCost").textContent = money(d.inventory_cost_value)
  document.getElementById("fdRetail").textContent = money(d.inventory_retail_value)
  document.getElementById("fdPotential").textContent = money(d.inventory_potential_margin)
  document.getElementById("fdSales30").textContent = money(d.sales_30d)
  document.getElementById("fdMargin30").textContent = money(d.gross_margin_30d)
  document.getElementById("fdDeadStock").textContent = d.dead_stock_count_90d || 0
}

function buildInventoryQuery() {
  const params = new URLSearchParams()

  if (state.filters.search) params.set("search", state.filters.search)
  if (state.filters.category_id) params.set("category_id", state.filters.category_id)
  if (state.filters.stock_status) params.set("stock_status", state.filters.stock_status)
  params.set("sort_by", state.filters.sort_by)
  params.set("sort_order", state.filters.sort_order)
  params.set("limit", "500")

  return params.toString()
}

async function loadCategories() {
  const data = await fetchJson(`${API_BASE_URL}/api/categories`)
  state.categories = data
  renderCategories()
}

async function loadInventory() {
  const query = buildInventoryQuery()
  const data = await fetchJson(`${API_BASE_URL}/api/admin/inventory?${query}`)
  state.products = data.products || []
  renderSummary(data.summary || {})
  renderTable()
}

async function loadMovements() {
  const data = await fetchJson(`${API_BASE_URL}/api/admin/inventory/movements?limit=100`)
  state.movements = data.movements || []
  renderMovements()
}

async function loadRestockSuggestions() {
  const data = await fetchJson(`${API_BASE_URL}/api/admin/inventory/restock-suggestions?days=30&coverage_days=14&limit=100`)
  state.restockSuggestions = data.suggestions || []
  renderRestockSuggestions()
}

async function loadExpiringBatches() {
  const data = await fetchJson(`${API_BASE_URL}/api/admin/inventory/batches/expiring?days=45&include_expired=true&limit=200`)
  state.expiringBatches = data.batches || []
  renderExpiringBatches()
}

async function loadFinancialDashboard() {
  const data = await fetchJson(`${API_BASE_URL}/api/admin/inventory/financial-dashboard`)
  state.financialDashboard = data
  renderFinancialDashboard()
}

async function refreshHighImpactWidgets() {
  await Promise.all([
    loadRestockSuggestions(),
    loadExpiringBatches(),
    loadFinancialDashboard()
  ])
}

function wireFilters() {
  document.getElementById("filterSearch").addEventListener("input", async (event) => {
    state.filters.search = event.target.value.trim()
    await loadInventory()
  })

  document.getElementById("filterCategory").addEventListener("change", async (event) => {
    state.filters.category_id = event.target.value
    await loadInventory()
  })

  document.getElementById("filterStockStatus").addEventListener("change", async (event) => {
    state.filters.stock_status = event.target.value
    await loadInventory()
  })

  const refreshRestockBtn = document.getElementById("refreshRestockBtn")
  if (refreshRestockBtn) {
    refreshRestockBtn.addEventListener("click", async () => {
      await refreshHighImpactWidgets()
      UI.toast("Indicadores de alto impacto actualizados", "success")
    })
  }

  document.querySelectorAll("[data-sort]").forEach(button => {
    button.addEventListener("click", async () => {
      const nextSort = button.dataset.sort

      if (state.filters.sort_by === nextSort) {
        state.filters.sort_order = state.filters.sort_order === "asc" ? "desc" : "asc"
      } else {
        state.filters.sort_by = nextSort
        state.filters.sort_order = "asc"
      }

      document.getElementById("sortLabel").textContent = `${state.filters.sort_by} (${state.filters.sort_order})`
      await loadInventory()
    })
  })
}

function openAdjustModal(productId) {
  const product = state.products.find(p => p.id === productId)
  if (!product) {
    return
  }

  state.selectedProduct = product

  document.getElementById("adjustProductName").textContent = `${product.nombre} (#${product.id})`
  document.getElementById("adjustCurrentStock").textContent = String(product.stock)
  document.getElementById("adjustMovementType").value = "add"
  document.getElementById("adjustQuantity").value = ""
  document.getElementById("adjustReason").value = ""

  const modal = new bootstrap.Modal(document.getElementById("adjustStockModal"))
  modal.show()
}

async function submitAdjustment(event) {
  event.preventDefault()

  if (!state.selectedProduct) {
    return
  }

  const movementType = document.getElementById("adjustMovementType").value
  const quantityRaw = document.getElementById("adjustQuantity").value
  const reason = document.getElementById("adjustReason").value.trim()

  const quantity = Number(quantityRaw)
  if (!Number.isInteger(quantity)) {
    UI.toast("La cantidad debe ser un numero entero", "warning")
    return
  }

  try {
    await fetchJson(`${API_BASE_URL}/api/admin/inventory/${state.selectedProduct.id}/stock`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        movement_type: movementType,
        quantity,
        reason
      })
    })

    const modalElement = document.getElementById("adjustStockModal")
    const modal = bootstrap.Modal.getInstance(modalElement)
    if (modal) {
      modal.hide()
    }

    await Promise.all([loadInventory(), loadMovements(), refreshHighImpactWidgets()])
    UI.toast("Ajuste aplicado correctamente", "success")
  } catch (error) {
    UI.alert("Error", error.message || "No fue posible ajustar el inventario")
  }
}

function exportCurrentView() {
  const headers = [
    "ID", "Nombre", "Categoria", "Codigo", "Stock", "Stock Minimo", "Estado", "Precio", "Valor Inventario", "Ventas 30d"
  ]

  const rows = state.products.map(p => [
    p.id,
    p.nombre,
    p.categoria || "",
    p.codigo_barras || "",
    p.stock,
    p.stock_minimo,
    p.stock_status,
    p.precio,
    p.inventory_value,
    p.units_sold_30d
  ])

  const csv = [headers, ...rows]
    .map(row => row.map(value => `"${String(value).replaceAll('"', '""')}"`).join(","))
    .join("\n")

  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" })
  const url = URL.createObjectURL(blob)
  const link = document.createElement("a")
  link.href = url
  link.download = `inventario_${new Date().toISOString().slice(0, 10)}.csv`
  link.click()
  URL.revokeObjectURL(url)
}

async function initInventoryScreen() {
  try {
    wireFilters()
    document.getElementById("adjustStockForm").addEventListener("submit", submitAdjustment)
    document.getElementById("exportCsvBtn").addEventListener("click", exportCurrentView)

    await loadCategories()
    await Promise.all([
      loadInventory(),
      loadMovements(),
      refreshHighImpactWidgets()
    ])
  } catch (error) {
    UI.alert("Error", error.message || "No fue posible inicializar la pantalla de inventario")
  }
}

window.openAdjustModal = openAdjustModal
initInventoryScreen()
