const SESSION_KEY = "gsp_auth_session";

window.GSP_CONFIG = { auth_enabled: false };

async function cargarConfig() {
    try {
        const res = await fetch("/api/config");
        window.GSP_CONFIG = await res.json();
    } catch (_) {
        window.GSP_CONFIG = { auth_enabled: false };
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

function crearClienteSupabase() {
    const cfg = window.GSP_CONFIG;
    if (!cfg.supabase_url || !cfg.supabase_anon_key || !window.supabase) return null;
    return window.supabase.createClient(cfg.supabase_url, cfg.supabase_anon_key);
}

async function iniciarSesion(email, password) {
    const sb = crearClienteSupabase();
    if (!sb) throw new Error("Supabase no configurado en el servidor.");
    const { data, error } = await sb.auth.signInWithPassword({ email, password });
    if (error) throw error;
    setSession(data.session);
    return data.session;
}
