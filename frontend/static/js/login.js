// File: frontend/static/js/login.js

const API_URL = window.API_CONFIG.baseUrl;

function getFriendlyLoginError(response, payloadText, payloadJson) {
    if (!API_URL) {
        return 'Falta configurar la URL del backend. Define apiBaseUrl en static/js/config.js o abre la app con ?api_base_url=https://tu-backend.com';
    }

    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
        return 'El backend no respondio JSON. Verifica que apiBaseUrl apunte a tu API y no al sitio de Netlify.';
    }

    if (payloadJson && payloadJson.error) {
        return payloadJson.error;
    }

    if (!response.ok) {
        return 'Credenciales incorrectas o backend no disponible';
    }

    return payloadText || 'No fue posible iniciar sesion';
}

document.addEventListener("DOMContentLoaded", () => {
    if (Auth.isAuthenticated()) {
        const user = Auth.getUser();
        if (user.rol === 'admin') {
            window.location.href = "admin.html";
        } else {
            window.location.href = "pos.html";
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

        const payloadText = await response.text();
        let payloadJson = null;

        try {
            payloadJson = payloadText ? JSON.parse(payloadText) : null;
        } catch (_) {
            payloadJson = null;
        }

        if (!response.ok || !payloadJson) {
            throw new Error(getFriendlyLoginError(response, payloadText, payloadJson));
        }

        Auth.setSession(payloadJson.token, payloadJson.user);

        if (payloadJson.user.rol === 'admin') {
            window.location.href = "admin.html";
        } else {
            window.location.href = "pos.html";
        }

    } catch (error) {
        errorDiv.textContent = error.message;
        errorDiv.style.display = 'block';
    } finally {
        btn.disabled = false;
        btn.innerHTML = `Iniciar Sesion <i class="bi bi-box-arrow-in-right ms-1"></i>`;
    }
});