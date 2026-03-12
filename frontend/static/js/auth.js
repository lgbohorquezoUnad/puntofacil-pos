// File: frontend/static/js/auth.js

const Auth = {
    getToken() {
        return localStorage.getItem('token');
    },

    getUser() {
        const userStr = localStorage.getItem('user');
        if (!userStr) return null;
        try {
            return JSON.parse(userStr);
        } catch(e) {
            return null;
        }
    },

    setSession(token, user) {
        localStorage.setItem('token', token);
        localStorage.setItem('user', JSON.stringify(user));
    },

    clearSession() {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
    },

    isAuthenticated() {
        return !!this.getToken() && !!this.getUser();
    },

    isAdmin() {
        const user = this.getUser();
        return user && user.rol === 'admin';
    },

    requireAuth() {
        if (!this.isAuthenticated()) {
            window.location.href = "/login";
        }
    },

    requireAdmin() {
        this.requireAuth();
        if (!this.isAdmin()) {
            // Un administrador puede ir a pos, pero un cajero no puede ir a admin
            window.location.href = "/pos";
        }
    },

    getAuthHeaders() {
        return {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.getToken()}`
        };
    },

    // A helper method wrapping fetch to automatically attach headers
    async fetchWithAuth(url, options = {}) {
        const headers = {
            ...this.getAuthHeaders(),
            ...options.headers
        };

        const response = await fetch(url, { ...options, headers });
        
        // If unauthorized because token expired or invalid
        if (response.status === 401 || response.status === 422) {
            this.clearSession();
            window.location.href = "/login";
            throw new Error('Session expired');
        }

        return response;
    },

    logout() {
        this.clearSession();
        window.location.href = "/login";
    }
};

window.Auth = Auth;
