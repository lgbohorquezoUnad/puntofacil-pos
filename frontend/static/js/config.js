window.APP_CONFIG = window.APP_CONFIG || {
    apiBaseUrl: ""
};

(function () {
    const LOCAL_API_BASE_URL = "http://127.0.0.1:5000";

    function normalizeBaseUrl(value) {
        if (!value) {
            return "";
        }

        return String(value).trim().replace(/\/+$/, "");
    }

    function isLocalHostname(hostname) {
        return hostname === "localhost" || hostname === "127.0.0.1";
    }

    const params = new URLSearchParams(window.location.search);
    const queryBaseUrl = normalizeBaseUrl(params.get("api_base_url"));

    if (queryBaseUrl) {
        localStorage.setItem("api_base_url", queryBaseUrl);
    }

    const storedBaseUrl = normalizeBaseUrl(localStorage.getItem("api_base_url"));
    const configuredBaseUrl = normalizeBaseUrl(window.APP_CONFIG.apiBaseUrl);
    const baseUrl = isLocalHostname(window.location.hostname)
        ? LOCAL_API_BASE_URL
        : (storedBaseUrl || configuredBaseUrl || "");

    if (!isLocalHostname(window.location.hostname) && !storedBaseUrl && !configuredBaseUrl) {
        console.warn("API base URL no configurada. Define window.APP_CONFIG.apiBaseUrl en static/js/config.js o usa ?api_base_url=https://tu-backend.com");
    }

    window.API_CONFIG = {
        baseUrl,
        buildUrl(path) {
            const normalizedPath = path.startsWith("/") ? path : `/${path}`;
            return `${this.baseUrl}${normalizedPath}`;
        },
        setBaseUrl(nextBaseUrl) {
            const normalized = normalizeBaseUrl(nextBaseUrl);
            if (normalized) {
                localStorage.setItem("api_base_url", normalized);
            } else {
                localStorage.removeItem("api_base_url");
            }
            window.location.reload();
        },
        clearBaseUrl() {
            localStorage.removeItem("api_base_url");
            window.location.reload();
        }
    };
})();