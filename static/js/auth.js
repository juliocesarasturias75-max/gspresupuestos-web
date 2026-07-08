const SESSION_KEY = "gsp_auth_session";

window.GSP_CONFIG = { auth_enabled: true };

async function cargarConfig() {
    try {
        const res = await fetch("/api/config");
        window.GSP_CONFIG = await res.json();
    } catch (_) {
        window.GSP_CONFIG = { auth_enabled: true };
    }
    return window.GSP_CONFIG;
}

function getSession() {
    try {
        const raw = localStorage.getItem(SESSION_KEY);
        return raw ? JSON.parse(raw) : null;
    } catch (_) {
        return null;
    }
}

function setSession(session) {
    if (session) {
        localStorage.setItem(SESSION_KEY, JSON.stringify(session));
    } else {
        localStorage.removeItem(SESSION_KEY);
    }
}

function apiHeaders(extra = {}) {
    const headers = { ...extra };
    const session = getSession();
    if (session?.access_token) {
        headers.Authorization = `Bearer ${session.access_token}`;
    }
    return headers;
}

async function apiFetch(url, options = {}) {
    const opts = { ...options };
    opts.headers = apiHeaders(options.headers || {});
    return fetch(url, opts);
}

async function requiereAuth(redirigir = true) {
    const cfg = await cargarConfig();
    if (!cfg.auth_enabled) return true;
    const session = getSession();
    if (!session?.access_token && redirigir) {
        window.location.href = "/login";
        return false;
    }
    return !!session?.access_token;
}

function cerrarSesion() {
    setSession(null);
    window.location.href = "/login";
}

async function iniciarSesion(email, password) {
    const res = await fetch("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
    });
    const data = await res.json();
    if (!res.ok) {
        throw new Error(data.detail || "Error al iniciar sesión.");
    }
    const session = {
        access_token: data.access_token,
        user: data.user,
    };
    setSession(session);
    return session;
}

async function cargarUsuarioActual() {
    const res = await apiFetch("/api/me");
    if (!res.ok) return null;
    return res.json();
}

function esAdmin() {
    const session = getSession();
    return !!session?.user?.is_admin;
}
