const API_BASE_URL = window.API_CONFIG.baseUrl

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

function buildPlaceholderImage(productName = "Producto") {
  const safeName = String(productName || "Producto").trim()
  const initials = safeName
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map(word => word[0].toUpperCase())
    .join("") || "P"
  const hue = safeName.split("").reduce((acc, char) => acc + char.charCodeAt(0), 0) % 360
  const bgStart = `hsl(${hue}, 72%, 82%)`
  const bgEnd = `hsl(${(hue + 28) % 360}, 78%, 70%)`
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="420" height="420" viewBox="0 0 420 420">
      <defs>
        <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="${bgStart}"/>
          <stop offset="100%" stop-color="${bgEnd}"/>
        </linearGradient>
      </defs>
      <rect width="420" height="420" rx="38" fill="url(#g)"/>
      <text x="50%" y="54%" dominant-baseline="middle" text-anchor="middle"
        font-family="Segoe UI, Arial, sans-serif" font-size="132" font-weight="700" fill="#ffffff">${initials}</text>
    </svg>
  `.trim()
  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`
}

function resolveProductImage(product) {
  const directImage = product?.imagen_url || product?.imagen || product?.image_url || product?.foto_url || product?.foto
  return directImage || buildPlaceholderImage(product?.nombre)
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

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement("a")
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
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
    const isSelected = state.selectedProduct?.id === p.id
    tbody.innerHTML += `
      <tr class="product-row ${isSelected ? "is-selected" : ""}" onclick="selectInventoryProduct(${p.id})">
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
          <button class="btn btn-sm btn-primary" onclick="event.stopPropagation(); openAdjustModal(${p.id})">Ajustar</button>
        </td>
      </tr>
    `
  })
}

function renderSelectedProduct() {
  const image = document.getElementById("selectedProductImage")
  const name = document.getElementById("selectedProductName")
  const code = document.getElementById("selectedProductCode")
  const price = document.getElementById("selectedProductPrice")
  const stock = document.getElementById("selectedProductStock")
  const category = document.getElementById("selectedProductCategory")
  const value = document.getElementById("selectedProductValue")
  const imageUrlInput = document.getElementById("selectedProductImageUrl")
  const imageFileInput = document.getElementById("selectedProductImageFile")

  if (!image || !name || !code || !price || !stock || !category || !value) {
    return
  }

  if (!state.selectedProduct) {
    image.src = buildPlaceholderImage("Producto")
    image.alt = "Vista previa del producto seleccionado"
    name.textContent = "Selecciona un producto"
    code.textContent = "Haz clic en una fila para ver su imagen y resumen."
    price.textContent = "$0"
    stock.textContent = "0"
    category.textContent = "-"
    value.textContent = "$0"
    if (imageUrlInput) imageUrlInput.value = ""
    if (imageFileInput) imageFileInput.value = ""
    return
  }

  const product = state.selectedProduct
  image.src = resolveProductImage(product)
  image.alt = `Imagen de ${product.nombre}`
  name.textContent = product.nombre
  code.textContent = `${product.codigo_barras || "Sin codigo"} - ID #${product.id}`
  price.textContent = money(product.precio)
  stock.textContent = String(product.stock)
  category.textContent = product.categoria || "Sin categoria"
  value.textContent = money(product.inventory_value)
  if (imageUrlInput) imageUrlInput.value = product.imagen_url || ""
  if (imageFileInput) imageFileInput.value = ""
}

function selectInventoryProduct(productId) {
  const product = state.products.find(item => item.id === productId)
  if (!product) {
    return
  }

  state.selectedProduct = product
  renderSelectedProduct()
  renderTable()
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
    tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted py-2">Sin lotes proximos a vencer</td></tr>'
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
  if (state.selectedProduct) {
    state.selectedProduct = state.products.find(item => item.id === state.selectedProduct.id) || state.products[0] || null
  } else {
    state.selectedProduct = state.products[0] || null
  }
  renderSummary(data.summary || {})
  renderSelectedProduct()
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

async function refreshInventoryScreen({ includeCategories = false } = {}) {
  const tasks = [loadInventory(), loadMovements(), refreshHighImpactWidgets()]
  if (includeCategories) {
    tasks.unshift(loadCategories())
  }
  await Promise.all(tasks)
}

async function downloadInventoryTemplate() {
  try {
    const response = await Auth.fetchWithAuth(`${API_BASE_URL}/api/admin/products/import-template`)
    if (!response.ok) {
      const data = await response.json().catch(() => ({}))
      throw new Error(data.error || "No fue posible descargar la plantilla")
    }

    const blob = await response.blob()
    downloadBlob(blob, `plantilla_productos_${new Date().toISOString().slice(0, 10)}.xlsx`)
    UI.toast("Plantilla Excel descargada", "success")
  } catch (error) {
    UI.alert("Error", error.message || "No fue posible descargar la plantilla")
  }
}

async function importProductsFile(file) {
  const formData = new FormData()
  formData.append("file", file)

  try {
    const response = await Auth.fetchWithAuth(`${API_BASE_URL}/api/admin/products/import`, {
      method: "POST",
      body: formData,
    })
    const result = await response.json().catch(() => ({}))
    if (!response.ok) {
      throw new Error(result.error || "No fue posible importar el archivo")
    }

    await refreshInventoryScreen({ includeCategories: true })

    const errors = result.summary?.errors || []
    const message = [
      `Creados: ${result.summary?.created || 0}`,
      `Actualizados: ${result.summary?.updated || 0}`,
      `Errores: ${errors.length}`,
      errors.length ? "Primeros errores: " + errors.slice(0, 5).join(" | ") : "Archivo procesado correctamente"
    ].join("\n")

    UI.alert("Carga masiva completada", message, errors.length ? "warning" : "success")
  } catch (error) {
    UI.alert("Error", error.message || "No fue posible importar el archivo")
  }
}

async function saveSelectedProductImageUrl() {
  if (!state.selectedProduct) {
    UI.toast("Selecciona un producto primero", "warning")
    return
  }

  const imageUrlInput = document.getElementById("selectedProductImageUrl")
  const image_url = imageUrlInput?.value.trim() || ""

  try {
    await fetchJson(`${API_BASE_URL}/api/admin/products/${state.selectedProduct.id}/image`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ image_url })
    })
    await refreshInventoryScreen()
    UI.toast("Imagen actualizada", "success")
  } catch (error) {
    UI.alert("Error", error.message || "No fue posible actualizar la imagen")
  }
}

async function uploadSelectedProductImage() {
  if (!state.selectedProduct) {
    UI.toast("Selecciona un producto primero", "warning")
    return
  }

  const input = document.getElementById("selectedProductImageFile")
  const file = input?.files?.[0]

  if (!file) {
    UI.toast("Selecciona un archivo de imagen", "warning")
    return
  }

  const formData = new FormData()
  formData.append("image", file)

  try {
    const response = await Auth.fetchWithAuth(`${API_BASE_URL}/api/admin/products/${state.selectedProduct.id}/image`, {
      method: "POST",
      body: formData,
    })
    const result = await response.json().catch(() => ({}))
    if (!response.ok) {
      throw new Error(result.error || "No fue posible subir la imagen")
    }

    await refreshInventoryScreen()
    UI.toast("Imagen cargada correctamente", "success")
  } catch (error) {
    UI.alert("Error", error.message || "No fue posible subir la imagen")
  }
}

function printPhysicalCountSheet() {
  const rows = state.products.map(product => `
    <tr>
      <td>${product.id}</td>
      <td>${product.nombre}</td>
      <td>${product.categoria || "Sin categoria"}</td>
      <td>${product.codigo_barras || "-"}</td>
      <td>${product.stock}</td>
      <td style="height:36px;"></td>
      <td></td>
    </tr>
  `).join("")

  const html = `
    <html lang="es">
      <head>
        <title>Conteo fisico de inventario</title>
        <style>
          body { font-family: Arial, sans-serif; color: #111827; margin: 24px; }
          h1 { margin: 0 0 6px; font-size: 22px; }
          p { margin: 0 0 16px; color: #4b5563; }
          table { width: 100%; border-collapse: collapse; }
          th, td { border: 1px solid #cbd5e1; padding: 8px; font-size: 12px; text-align: left; }
          th { background: #e2e8f0; text-transform: uppercase; letter-spacing: .04em; font-size: 11px; }
          .sign { margin-top: 20px; display: flex; justify-content: space-between; gap: 24px; }
          .sign div { width: 48%; border-top: 1px solid #94a3b8; padding-top: 8px; font-size: 12px; }
        </style>
      </head>
      <body>
        <h1>Conteo fisico de inventario</h1>
        <p>Fecha: ${new Date().toLocaleString("es-CO")} | Referencias: ${state.products.length}</p>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Producto</th>
              <th>Categoria</th>
              <th>Codigo</th>
              <th>Stock sistema</th>
              <th>Conteo fisico</th>
              <th>Observaciones</th>
            </tr>
          </thead>
          <tbody>${rows || '<tr><td colspan="7">No hay productos para imprimir.</td></tr>'}</tbody>
        </table>
        <div class="sign">
          <div>Responsable del conteo</div>
          <div>Verificacion</div>
        </div>
        <script>window.onload = () => window.print();</script>
      </body>
    </html>
  `

  const printWindow = window.open("", "_blank", "width=1100,height=800")
  if (!printWindow) {
    UI.alert("Error", "Tu navegador bloqueo la ventana de impresion")
    return
  }

  printWindow.document.open()
  printWindow.document.write(html)
  printWindow.document.close()
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

  document.getElementById("downloadTemplateBtn")?.addEventListener("click", downloadInventoryTemplate)
  document.getElementById("printCountBtn")?.addEventListener("click", printPhysicalCountSheet)
  document.getElementById("saveImageUrlBtn")?.addEventListener("click", saveSelectedProductImageUrl)
  document.getElementById("uploadImageBtn")?.addEventListener("click", uploadSelectedProductImage)

  const importButton = document.getElementById("importProductsBtn")
  const importInput = document.getElementById("importProductsFile")
  if (importButton && importInput) {
    importButton.addEventListener("click", () => importInput.click())
    importInput.addEventListener("change", async (event) => {
      const file = event.target.files?.[0]
      if (!file) return
      await importProductsFile(file)
      event.target.value = ""
    })
  }
}

function openAdjustModal(productId) {
  const product = state.products.find(p => p.id === productId)
  if (!product) {
    return
  }

  state.selectedProduct = product
  renderSelectedProduct()
  renderTable()

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

    await refreshInventoryScreen()
    UI.toast("Ajuste aplicado correctamente", "success")
  } catch (error) {
    UI.alert("Error", error.message || "No fue posible ajustar el inventario")
  }
}

function exportCurrentView() {
  const headers = [
    "ID", "Nombre", "Categoria", "Codigo", "Stock", "Stock Minimo", "Estado", "Precio", "Valor Inventario", "Ventas 30d", "Imagen URL"
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
    p.units_sold_30d,
    p.imagen_url || ""
  ])

  const csv = [headers, ...rows]
    .map(row => row.map(value => `"${String(value).replaceAll('"', '""')}"`).join(","))
    .join("\n")

  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" })
  downloadBlob(blob, `inventario_${new Date().toISOString().slice(0, 10)}.csv`)
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
window.selectInventoryProduct = selectInventoryProduct
initInventoryScreen()
