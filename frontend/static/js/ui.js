const UI = {
    getMode() {
        return localStorage.getItem('app_mode') || 'simple';
    },

    setMode(mode) {
        const nextMode = mode === 'advanced' ? 'advanced' : 'simple';
        localStorage.setItem('app_mode', nextMode);
        this.applyMode(nextMode);
        this.updateModeButton(nextMode);
        this.toast(`Modo ${nextMode === 'advanced' ? 'avanzado' : 'simple'} activado`, 'info');
    },

    toggleMode() {
        const current = this.getMode();
        const next = current === 'advanced' ? 'simple' : 'advanced';
        this.setMode(next);
    },

    applyMode(mode = null) {
        const current = mode || this.getMode();
        document.documentElement.setAttribute('data-app-mode', current);
    },

    updateModeButton(mode = null) {
        const current = mode || this.getMode();
        const btn = document.getElementById('modeToggle');
        if (!btn) return;
        btn.textContent = `Modo: ${current === 'advanced' ? 'Avanzado' : 'Simple'}`;
    },

    toast(title, icon = 'success') {
        Swal.fire({
            toast: true,
            position: 'top-end',
            icon: icon,
            title: title,
            showConfirmButton: false,
            timer: 3000,
            timerProgressBar: true,
            didOpen: (toast) => {
                toast.addEventListener('mouseenter', Swal.stopTimer)
                toast.addEventListener('mouseleave', Swal.resumeTimer)
            }
        });
    },

    alert(title, text = '', icon = 'error') {
        Swal.fire({
            title: title,
            text: text,
            icon: icon,
            confirmButtonColor: '#2563eb'
        });
    },

    confirm(title, text = '') {
        return Swal.fire({
            title: title,
            text: text,
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#2563eb',
            cancelButtonColor: '#d33',
            confirmButtonText: 'Sí, confirmar',
            cancelButtonText: 'Cancelar'
        });
    },

    initTheme() {
        const savedTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', savedTheme);
        this.updateThemeIcon(savedTheme);
    },

    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        this.updateThemeIcon(newTheme);
        this.toast(`Modo ${newTheme === 'dark' ? 'oscuro' : 'claro'} activado`, 'info');
    },

    updateThemeIcon(theme) {
        const btn = document.getElementById('themeToggle');
        if (!btn) return;
        const icon = btn.querySelector('i');
        if (!icon) return;
        if (theme === 'dark') {
            icon.className = 'bi bi-sun-fill';
        } else {
            icon.className = 'bi bi-moon-fill';
        }
    }
};

window.UI = UI;
document.addEventListener('DOMContentLoaded', () => {
    UI.initTheme();
    UI.applyMode();
    UI.updateModeButton();
});
