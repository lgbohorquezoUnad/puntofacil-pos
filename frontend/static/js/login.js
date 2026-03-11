// File: frontend/static/js/login.js

const API_URL = "http://localhost:5000";

document.addEventListener("DOMContentLoaded", () => {
    // Si ya esta autenticado, redirigir
    if (Auth.isAuthenticated()) {
        const user = Auth.getUser();
        if (user.rol === 'admin') {
            window.location.href = "/frontend/templates/admin.html";
        } else {
            window.location.href = "/frontend/templates/pos.html";
        }
    }
});

document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const btn = document.getElementById('submitBtn');
    const errorDiv = document.getElementById('errorMessage');

    btn.disabled = true;
    btn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span> Entrando...`;
    errorDiv.style.display = 'none';

    try {
        const response = await fetch(`${API_URL}/api/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Credenciales incorrectas');
        }

        Auth.setSession(data.token, data.user);

        // Redireccion basada en rol
        if (data.user.rol === 'admin') {
            window.location.href = "/frontend/templates/admin.html";
        } else {
            window.location.href = "/frontend/templates/pos.html";
        }

    } catch (error) {
        errorDiv.textContent = error.message;
        errorDiv.style.display = 'block';
    } finally {
        btn.disabled = false;
        btn.innerHTML = `Iniciar Sesión <i class="bi bi-box-arrow-in-right ms-1"></i>`;
    }
});
