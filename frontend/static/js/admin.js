const API_BASE_URL = window.API_CONFIG.baseUrl;

// Requerir solo admin
Auth.requireAdmin();

let adminProducts = [];
let adminCategories = [];
let adminUsers = [];

function formatMoney(value) {
  return "$" + Number(value || 0).toLocaleString("es-CO", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function showFeedback(message, type) {
  const feedback = document.getElementById("formFeedback");
  feedback.className = `feedback ${type}`;
  feedback.textContent = message;
}

function clearFeedback() {
  const feedback = document.getElementById("formFeedback");
  feedback.className = "feedback";
  feedback.textContent = "";
}

async function loadDashboard() {
  const response = await Auth.fetchWithAuth(`${API_BASE_URL}/api/admin/dashboard`);
  if (!response.ok) {
    return;
  }

  const result = await response.json();
  document.getElementById("todaySalesCount").textContent = result.today_sales_count;
  document.getElementById("todaySalesTotal").textContent = formatMoney(result.today_sales_total);
  document.getElementById("todayItemsSold").textContent = result.today_items_sold;
  document.getElementById("lowStockCount").textContent = result.low_stock_count;

  const topProducts = document.getElementById("topProducts");
  topProducts.innerHTML = "";

  if (!result.top_products.length) {
    topProducts.innerHTML = '<div class="text-muted small">Aun no hay ventas hoy.</div>';
    return;
  }

  result.top_products.forEach(product => {
    topProducts.innerHTML += `
      <div class="top-item">
        <div class="top-name">${product.nombre}</div>
        <div class="top-qty">${product.cantidad} uds</div>
      </div>
    `;
  });
}

async function loadCategories() {
  const response = await Auth.fetchWithAuth(`${API_BASE_URL}/api/categories`);
  if (!response.ok) {
    showFeedback("No fue posible cargar las categorias", "error");
    return;
  }

  adminCategories = await response.json();
  const select = document.getElementById("productCategory");
  select.innerHTML = "";

  adminCategories.forEach(category => {
    select.innerHTML += `<option value="${category.id}">${category.nombre}</option>`;
  });
}

async function loadProducts() {
  const response = await Auth.fetchWithAuth(`${API_BASE_URL}/api/products`);
  if (!response.ok) {
    showFeedback("No fue posible cargar los productos", "error");
    return;
  }

  adminProducts = await response.json();
  renderAdminProducts(adminProducts);
}

function renderAdminProducts(products) {
  const tbody = document.getElementById("adminProductsTable");
  tbody.innerHTML = "";

  if (!products.length) {
    tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-4">Sin productos registrados</td></tr>';
    return;
  }

  products.forEach(product => {
    const category = product.categoria || "Sin categoria";
    const stockClass = product.stock <= product.stock_minimo ? "text-warning" : "";
    tbody.innerHTML += `
      <tr>
        <td>
          <div class="fw-bold">${product.nombre}</div>
          <div class="small text-muted">${product.codigo_barras || "Sin codigo"}</div>
        </td>
        <td>${category}</td>
        <td>${formatMoney(product.precio)}</td>
        <td class="${stockClass}">${product.stock}</td>
        <td>${product.codigo_barras || "-"}</td>
        <td>
          <div class="product-actions">
            <button type="button" class="mini-btn mini-edit" onclick="editProduct(${product.id})">
              <i class="bi bi-pencil"></i>
            </button>
            <button type="button" class="mini-btn mini-delete" onclick="deleteProduct(${product.id})">
              <i class="bi bi-trash"></i>
            </button>
          </div>
        </td>
      </tr>
    `;
  });
}

function filterAdminProducts() {
  const term = document.getElementById("adminProductSearch").value.trim().toLowerCase();
  if (!term) {
    renderAdminProducts(adminProducts);
    return;
  }

  const filtered = adminProducts.filter(product => {
    const name = (product.nombre || "").toLowerCase();
    const category = (product.categoria || "").toLowerCase();
    const barcode = (product.codigo_barras || "").toLowerCase();
    return name.includes(term) || category.includes(term) || barcode.includes(term);
  });

  renderAdminProducts(filtered);
}

function resetProductForm() {
  document.getElementById("productForm").reset();
  document.getElementById("productId").value = "";
  document.getElementById("submitButton").textContent = "Guardar producto";
  clearFeedback();
}

function editProduct(productId) {
  const product = adminProducts.find(item => item.id === productId);
  if (!product) {
    return;
  }

  document.getElementById("productId").value = product.id;
  document.getElementById("productName").value = product.nombre || "";
  document.getElementById("productCategory").value = product.categoria_id || "";
  document.getElementById("productBarcode").value = product.codigo_barras || "";
  document.getElementById("productPrice").value = product.precio ?? "";
  document.getElementById("productStock").value = product.stock ?? "";
  document.getElementById("submitButton").textContent = "Actualizar producto";
  clearFeedback();
}

async function submitProductForm(event) {
  event.preventDefault();

  const productId = document.getElementById("productId").value;
  const nombre = document.getElementById("productName").value.trim();
  const categoriaId = document.getElementById("productCategory").value;
  const codigoBarras = document.getElementById("productBarcode").value.trim();
  const precio = Number(document.getElementById("productPrice").value);
  const stock = Number(document.getElementById("productStock").value);

  if (!nombre) {
    showFeedback("El nombre del producto es obligatorio", "error");
    return;
  }
  if (!categoriaId) {
    showFeedback("Selecciona una categoria", "error");
    return;
  }
  if (Number.isNaN(precio) || precio < 0) {
    showFeedback("Precio invalido", "error");
    return;
  }
  if (!Number.isInteger(stock) || stock < 0) {
    showFeedback("Stock invalido", "error");
    return;
  }

  const payload = {
    nombre,
    categoria_id: Number(categoriaId),
    codigo_barras: codigoBarras,
    precio,
    stock,
    stock_minimo: 5
  };

  const submitButton = document.getElementById("submitButton");
  submitButton.disabled = true;

  try {
    const response = await Auth.fetchWithAuth(
      productId ? `${API_BASE_URL}/api/admin/products/${productId}` : `${API_BASE_URL}/api/admin/products`,
      {
        method: productId ? "PUT" : "POST",
        body: JSON.stringify(payload)
      }
    );

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.error || "No fue posible guardar el producto");
    }

    showFeedback(productId ? "Producto actualizado" : "Producto creado", "success");
    resetProductForm();
    await loadProducts();
  } catch (error) {
    showFeedback(error.message || "No fue posible guardar el producto", "error");
  } finally {
    submitButton.disabled = false;
  }
}

async function deleteProduct(productId) {
  const confirmation = await UI.confirm("Deseas eliminar este producto?");
  if (!confirmation.isConfirmed) {
    return;
  }

  try {
    const response = await Auth.fetchWithAuth(`${API_BASE_URL}/api/admin/products/${productId}`, {
      method: "DELETE"
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.error || "No fue posible eliminar el producto");
    }

    UI.toast("Producto eliminado", "success");
    await loadProducts();
  } catch (error) {
    UI.alert("Error", error.message || "No fue posible eliminar el producto");
  }
}

function formatUserDate(value) {
  if (!value) return "-";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleDateString("es-CO");
}

function renderUsers(users) {
  const tbody = document.getElementById("adminUsersTable");
  tbody.innerHTML = "";

  if (!users.length) {
    tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-4">No hay usuarios habilitados para este filtro</td></tr>';
    return;
  }

  users.forEach(user => {
    const status = user.estado || "activo";
    tbody.innerHTML += `
      <tr>
        <td>
          <div class="user-name">${user.nombre}</div>
          <div class="user-meta">ID #${user.id}</div>
        </td>
        <td>${user.email}</td>
        <td><span class="badge ${user.rol === "admin" ? "bg-danger" : "bg-primary"}">${user.rol}</span></td>
        <td><span class="badge ${status === "activo" ? "bg-success" : "bg-secondary"}">${status}</span></td>
        <td>${formatUserDate(user.fecha_creacion)}</td>
        <td>
          <div class="product-actions">
            <button type="button" class="mini-btn mini-edit" onclick="editUser(${user.id})">
              <i class="bi bi-pencil"></i>
            </button>
            <button type="button" class="mini-btn mini-delete" onclick="deleteUser(${user.id})">
              <i class="bi bi-trash"></i>
            </button>
          </div>
        </td>
      </tr>
    `;
  });
}

function updateUsersSummary(users) {
  const admins = users.filter(user => user.rol === "admin").length;
  const cashiers = users.filter(user => user.rol === "cajero").length;
  document.getElementById("usersTotal").textContent = users.length;
  document.getElementById("usersAdmins").textContent = admins;
  document.getElementById("usersCashiers").textContent = cashiers;
  document.getElementById("usersCountBadge").textContent = `${users.length} usuarios`;
}

function filterUsers() {
  const term = (document.getElementById("adminUserSearch")?.value || "").trim().toLowerCase();
  if (!term) {
    renderUsers(adminUsers);
    return;
  }

  const filtered = adminUsers.filter(user => {
    const name = (user.nombre || "").toLowerCase();
    const email = (user.email || "").toLowerCase();
    const rol = (user.rol || "").toLowerCase();
    const estado = (user.estado || "").toLowerCase();
    return name.includes(term) || email.includes(term) || rol.includes(term) || estado.includes(term);
  });

  renderUsers(filtered);
}

async function loadUsers() {
  const response = await Auth.fetchWithAuth(`${API_BASE_URL}/api/usuarios`);
  if (!response.ok) {
    showFeedback("No fue posible cargar los usuarios", "error");
    return;
  }

  adminUsers = await response.json();
  updateUsersSummary(adminUsers);
  renderUsers(adminUsers);
}

function resetUserForm() {
  document.getElementById("userForm").reset();
  document.getElementById("userId").value = "";
  document.getElementById("userStatus").value = "activo";
  document.getElementById("submitUserButton").textContent = "Crear usuario";
  clearFeedback();
}

function editUser(id) {
  const user = adminUsers.find(item => item.id === id);
  if (!user) {
    return;
  }

  document.getElementById("userId").value = user.id;
  document.getElementById("userName").value = user.nombre || "";
  document.getElementById("userEmail").value = user.email || "";
  document.getElementById("userPassword").value = "";
  document.getElementById("userRole").value = user.rol || "cajero";
  document.getElementById("userStatus").value = user.estado || "activo";
  document.getElementById("submitUserButton").textContent = "Actualizar usuario";
  clearFeedback();
}

async function submitUserForm(event) {
  event.preventDefault();

  const userId = document.getElementById("userId").value;
  const payload = {
    nombre: document.getElementById("userName").value.trim(),
    email: document.getElementById("userEmail").value.trim(),
    password: document.getElementById("userPassword").value.trim(),
    rol: document.getElementById("userRole").value,
    estado: document.getElementById("userStatus").value
  };

  if (!payload.nombre || !payload.email) {
    showFeedback("Completa los datos del usuario", "error");
    return;
  }

  if (!userId && !payload.password) {
    showFeedback("La contrasena es obligatoria para crear usuarios", "error");
    return;
  }

  const btn = document.getElementById("submitUserButton");
  btn.disabled = true;

  try {
    const response = await Auth.fetchWithAuth(userId ? `${API_BASE_URL}/api/usuarios/${userId}` : `${API_BASE_URL}/api/usuarios`, {
      method: userId ? "PUT" : "POST",
      body: JSON.stringify(payload)
    });

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.error || "Error guardando usuario");
    }

    UI.toast(userId ? "Usuario actualizado exitosamente" : "Usuario creado exitosamente", "success");
    resetUserForm();
    await loadUsers();
  } catch (err) {
    showFeedback(err.message || "No se pudo guardar el usuario", "error");
  } finally {
    btn.disabled = false;
  }
}

async function deleteUser(id) {
  const confirmation = await UI.confirm("Deseas eliminar a este usuario?");
  if (!confirmation.isConfirmed) {
    return;
  }

  try {
    const response = await Auth.fetchWithAuth(`${API_BASE_URL}/api/usuarios/${id}`, { method: "DELETE" });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.error || "No se pudo eliminar el usuario");
    }

    UI.toast("Usuario eliminado", "success");
    await loadUsers();
  } catch (err) {
    UI.alert("Error", err.message || "No se pudo eliminar el usuario");
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  const productForm = document.getElementById("productForm");
  if (productForm && !productForm.hasAttribute("onsubmit")) {
    productForm.addEventListener("submit", submitProductForm);
  }

  const userForm = document.getElementById("userForm");
  if (userForm) {
    userForm.addEventListener("submit", submitUserForm);
  }

  resetUserForm();

  await Promise.all([
    loadDashboard(),
    loadCategories(),
    loadProducts(),
    loadUsers()
  ]);
});

window.filterAdminProducts = filterAdminProducts;
window.submitProductForm = submitProductForm;
window.resetProductForm = resetProductForm;
window.editProduct = editProduct;
window.deleteProduct = deleteProduct;
window.deleteUser = deleteUser;
window.editUser = editUser;
window.filterUsers = filterUsers;
window.resetUserForm = resetUserForm;
