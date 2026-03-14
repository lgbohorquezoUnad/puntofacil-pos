/* =================================
   VARIABLES GLOBALES
================================= */

// Requerir autenticacion antes de cualquier cosa para POS
Auth.requireAuth();

let cart = []
let paymentMethod = ""
let productsList = []
let categoriesList = []
let currentCashRegister = null
const API_BASE_URL = window.API_CONFIG.baseUrl


/* =================================
   UTILIDADES
================================= */

function formatMoney(value) {
   return Number(value || 0).toFixed(2)
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
   const bgStart = `hsl(${hue}, 70%, 78%)`
   const bgEnd = `hsl(${(hue + 35) % 360}, 75%, 68%)`
   const svg = `
      <svg xmlns="http://www.w3.org/2000/svg" width="320" height="220" viewBox="0 0 320 220">
         <defs>
            <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
               <stop offset="0%" stop-color="${bgStart}"/>
               <stop offset="100%" stop-color="${bgEnd}"/>
            </linearGradient>
         </defs>
         <rect width="320" height="220" rx="22" fill="url(#g)"/>
         <text x="50%" y="54%" dominant-baseline="middle" text-anchor="middle"
           font-family="Segoe UI, Arial, sans-serif" font-size="68" font-weight="700" fill="#ffffff">${initials}</text>
      </svg>
   `.trim()
   return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`
}

function resolveProductImage(product) {
   const directImage = product?.imagen_url || product?.imagen || product?.image_url || product?.foto_url || product?.foto
   return directImage || buildPlaceholderImage(product?.nombre)
}


function updateSelectedPaymentUI() {
   const paymentStatus = document.getElementById("selectedPaymentStatus")
   const tiles = document.querySelectorAll(".payment-tile")

   paymentStatus.textContent = paymentMethod
      ? `Metodo de pago: ${paymentMethod}`
      : "Metodo de pago: No seleccionado"

   tiles.forEach(tile => {
      const isSelected = tile.dataset.method === paymentMethod

      tile.classList.toggle("selected", isSelected)
   })
}


/* =================================
   PRODUCTOS
================================= */

async function loadProducts() {
   const response = await Auth.fetchWithAuth(`${API_BASE_URL}/api/products`)

   if (!response.ok) {
      UI.toast("No fue posible cargar los productos", "error")
      return
   }

   productsList = await response.json()
   applyFilters()
}

async function loadCategories() {
   const response = await Auth.fetchWithAuth(`${API_BASE_URL}/api/categories`)

   if (!response.ok) {
      UI.toast("No fue posible cargar las categorias", "error")
      return
   }

   categoriesList = await response.json()
   renderCategoryFilter()
}

function renderCategoryFilter() {
   const select = document.getElementById("categoryFilter")
   select.innerHTML = '<option value="">Todas las categorias</option>'

   categoriesList.forEach(category => {
      select.innerHTML += `<option value="${category.nombre}">${category.nombre}</option>`
   })
}

function renderProducts(products) {
   const container = document.getElementById("productList")
   container.innerHTML = ""

   if (!products.length) {
      container.innerHTML = '<div class="text-muted small">No hay productos para este filtro</div>'
      return
   }

   products.forEach(p => {
      container.innerHTML += `
<div class="card product-card" onclick="addToCart(${p.id},'${p.nombre}',${p.precio})">
<div class="card-body">
<div class="product-media">
<img class="product-thumb" src="${resolveProductImage(p)}" alt="Imagen de ${p.nombre}">
</div>
<p class="product-name">${p.nombre}</p>
<p class="product-stock">Stock: ${p.stock}</p>
<p class="product-price">$${formatMoney(p.precio)}</p>
<button class="product-add-btn">Agregar</button>
</div>
</div>
`
   })
}

function applyFilters() {
   const text = document.getElementById("searchProduct").value.toLowerCase()
   const selectedCategory = document.getElementById("categoryFilter").value.toLowerCase()

   const filtered = productsList.filter(product => {
      const matchesText = product.nombre.toLowerCase().includes(text)
      const matchesCategory = !selectedCategory || (product.categoria || "").toLowerCase() === selectedCategory
      return matchesText && matchesCategory
   })

   renderProducts(filtered)
}


/* =================================
   CARRITO
================================= */

function addToCart(id, name, price) {
   let product = cart.find(p => p.id === id)

   if (product) {
      product.qty++
   } else {
      cart.push({ id: id, name: name, price: price, qty: 1 })
   }

   renderCart()
}

function increaseQty(id) {
   const product = cart.find(item => item.id === id)
   if (!product) {
      return
   }

   product.qty++
   renderCart()
}

function decreaseQty(id) {
   const product = cart.find(item => item.id === id)
   if (!product) {
      return
   }

   product.qty--

   if (product.qty <= 0) {
      cart = cart.filter(item => item.id !== id)
   }

   renderCart()
}

function removeFromCart(id) {
   cart = cart.filter(item => item.id !== id)
   renderCart()
}

function renderCart() {
   const cartItems = document.getElementById("cartItems")
   cartItems.innerHTML = ""

   let total = 0

   if (!cart.length) {
      cartItems.innerHTML = '<tr><td colspan="3" class="text-center text-muted">Sin productos en el carrito</td></tr>'
   }

   cart.forEach(p => {
      let subtotal = p.price * p.qty

      total += subtotal

      cartItems.innerHTML += `
<tr>
<td>
<div class="cart-name">${p.name}</div>
<div class="cart-actions mt-1">
<button class="qty-btn" onclick="event.stopPropagation(); decreaseQty(${p.id})">-</button>
<span class="qty-value">${p.qty}</span>
<button class="qty-btn" onclick="event.stopPropagation(); increaseQty(${p.id})">+</button>
<button class="remove-btn" onclick="event.stopPropagation(); removeFromCart(${p.id})"><i class="bi bi-x-lg"></i></button>
</div>
</td>
<td>${p.qty}</td>
<td>$${formatMoney(subtotal)}</td>
</tr>
`
   })

   document.getElementById("total").innerText = formatMoney(total)
}


/* =================================
   METODO DE PAGO
================================= */

function setPayment(method) {
   paymentMethod = method
   updateSelectedPaymentUI()
}


/* =================================
   CAJA
================================= */

function renderCashRegisterStatus() {
   const container = document.getElementById("cashRegisterStatus")

   if (!currentCashRegister) {
      container.innerHTML = "<strong>Estado:</strong> Sin caja abierta"
      return
   }

   container.innerHTML = `
<strong>Estado:</strong> ${currentCashRegister.status}<br>
<strong>Caja:</strong> #${currentCashRegister.cash_register_id}<br>
<strong>Apertura:</strong> $${formatMoney(currentCashRegister.opening_amount)}<br>
<strong>Fecha:</strong> ${currentCashRegister.opened_at}
`
}

async function loadCashRegisterStatus() {
   const response = await Auth.fetchWithAuth(`${API_BASE_URL}/api/cash-register/current`)
   const result = await response.json()
   currentCashRegister = result.cash_register
   renderCashRegisterStatus()
}

async function openCashRegister() {
   const openingAmount = document.getElementById("openingAmount").value

   if (openingAmount === "") {
      UI.toast("Debes indicar el monto de apertura", "warning")
      return
   }

   const response = await Auth.fetchWithAuth(`${API_BASE_URL}/api/cash-register/open`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ opening_amount: openingAmount })
   })

   const result = await response.json()

   if (!response.ok) {
      UI.alert("Error", result.error || "No fue posible abrir la caja")
      return
   }

   currentCashRegister = result.cash_register
   document.getElementById("openingAmount").value = ""
   renderCashRegisterStatus()
   UI.toast("Caja abierta correctamente")
}

async function closeCashRegister() {
   const closingAmount = document.getElementById("closingAmount").value

   if (closingAmount === "") {
      UI.toast("Debes indicar el monto de cierre", "warning")
      return
   }

   const response = await Auth.fetchWithAuth(`${API_BASE_URL}/api/cash-register/close`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ closing_amount: closingAmount })
   })

   const result = await response.json()

   if (!response.ok) {
      UI.alert("Error", result.error || "No fue posible cerrar la caja")
      return
   }

   currentCashRegister = null
   document.getElementById("closingAmount").value = ""
   renderCashRegisterStatus()
   UI.alert(
      "Caja cerrada",
      "Ventas: $" + formatMoney(result.summary.sales_total) +
      "\nEsperado: $" + formatMoney(result.summary.expected_amount) +
      "\nCierre: $" + formatMoney(result.summary.closing_amount) +
      "\nDiferencia: $" + formatMoney(result.summary.difference),
      "info"
   )
}


/* =================================
   HISTORIAL
================================= */

function renderSalesHistory(sales) {
   const container = document.getElementById("salesHistory")
   container.innerHTML = ""

   if (!sales.length) {
      container.innerHTML = '<tr><td colspan="4" class="text-center text-muted">Sin ventas registradas</td></tr>'
      return
   }

   sales.forEach(sale => {
      container.innerHTML += `
<tr>
<td>#${sale.sale_id}</td>
<td>${sale.fecha}</td>
<td>${sale.payment_method}</td>
<td>$${formatMoney(sale.total)}</td>
</tr>
`
   })
}

async function loadSalesHistory() {
   const response = await Auth.fetchWithAuth(`${API_BASE_URL}/api/sales?limit=10`)

   if (!response.ok) {
      UI.toast("No fue posible cargar el historial de ventas", "error")
      return
   }

   const result = await response.json()
   renderSalesHistory(result.sales || [])
}


/* =================================
   COBRAR VENTA
================================= */

async function checkout() {
   if (cart.length === 0) {
      UI.toast("No hay productos en el carrito", "warning")
      return
   }

   if (paymentMethod === "") {
      UI.toast("Selecciona un metodo de pago", "warning")
      return
   }

   if (!currentCashRegister) {
      UI.alert("Atención", "Debes abrir caja antes de cobrar", "warning")
      return
   }

   const payload = {
      payment_method: paymentMethod,
      items: cart.map(item => ({
         product_id: item.id,
         qty: item.qty
      }))
   }

   try {
      const response = await Auth.fetchWithAuth(`${API_BASE_URL}/api/sales`, {
         method: "POST",
         headers: { "Content-Type": "application/json" },
         body: JSON.stringify(payload)
      })

      const result = await response.json()

      if (!response.ok) {
         UI.alert("Error", result.error || "No fue posible registrar la venta")
         return
      }

      UI.alert(
         "Venta registrada",
         "Metodo: " + result.sale.payment_method +
         "\nTotal: $" + formatMoney(result.sale.total) +
         "\nFactura: #" + result.sale.sale_id +
         "\nCaja: #" + result.sale.cash_register_id,
         "success"
      )

      cart = []
      paymentMethod = ""
      renderCart()
      updateSelectedPaymentUI()
      await loadProducts()
      await loadSalesHistory()
      await loadCashRegisterStatus()

   } catch (error) {
      UI.toast("Error de conexion con la API", "error")
   }
}


/* =================================
   INICIO
================================= */

async function initPOS() {
   await loadCategories()
   await loadProducts()
   await loadCashRegisterStatus()
   await loadSalesHistory()
   renderCart()
   updateSelectedPaymentUI()
}

initPOS()







