window.APP_CONFIG = window.APP_CONFIG || {
    apiBaseUrl: ""
};

(function () {
    const LOCAL_API_PORT = "5000";
    const DEPLOYED_API_CANDIDATES = [
        "https://puntofacil-api.onrender.com"
    ];

    function normalizeBaseUrl(value) {
        if (!value) {
            return "";
        }

        return String(value).trim().replace(/\/+$/, "");
    }

    function isPrivateIpv4(hostname) {
        return /^10\./.test(hostname)
            || /^192\.168\./.test(hostname)
            || /^172\.(1[6-9]|2\d|3[0-1])\./.test(hostname);
    }

    function isLocalHostname(hostname) {
        // "" happens when the HTML is opened as a local file.
        return hostname === ""
            || hostname === "localhost"
            || hostname === "127.0.0.1"
            || hostname === "::1"
            || isPrivateIpv4(hostname)
            || hostname.endsWith(".local");
    }

    function buildLocalApiBaseUrl() {
        const currentHostname = window.location.hostname;
        const localHostname = currentHostname && currentHostname !== "::1"
            ? currentHostname
            : "127.0.0.1";

        return `${window.location.protocol}//${localHostname}:${LOCAL_API_PORT}`;
    }

    function inferRemoteBaseUrl(hostname) {
        if (!hostname) {
            return "";
        }

        if (hostname.endsWith(".onrender.com")) {
            return window.location.origin;
        }

        if (hostname.endsWith(".netlify.app")) {
            return DEPLOYED_API_CANDIDATES[0] || "";
        }

        return window.location.origin;
    }

    const params = new URLSearchParams(window.location.search);
    const queryBaseUrl = normalizeBaseUrl(params.get("api_base_url"));

    if (queryBaseUrl) {
        localStorage.setItem("api_base_url", queryBaseUrl);
    }

    const storedBaseUrl = normalizeBaseUrl(localStorage.getItem("api_base_url"));
    const configuredBaseUrl = normalizeBaseUrl(window.APP_CONFIG.apiBaseUrl);
    const inferredBaseUrl = normalizeBaseUrl(inferRemoteBaseUrl(window.location.hostname));
    const baseUrl = isLocalHostname(window.location.hostname)
        ? buildLocalApiBaseUrl()
        : (storedBaseUrl || configuredBaseUrl || inferredBaseUrl || "");

    if (!isLocalHostname(window.location.hostname) && !storedBaseUrl && !configuredBaseUrl && !inferredBaseUrl) {
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
